import httpx
import pytest

from packages.core.io import digest, read_json
from packages.prices.client import SourceClient


def client_for(tmp_path, handler):
    client = SourceClient(tmp_path)
    client.client.close()
    client.client = httpx.Client(transport=httpx.MockTransport(handler))
    return client


def test_source_cache_revalidation_and_exact_response_digest(tmp_path):
    calls = []

    def handler(request):
        calls.append(request)
        if len(calls) == 1:
            return httpx.Response(200, json={"rate": "0.526"}, headers={"ETag": '"rate-v1"'})
        assert request.headers["If-None-Match"] == '"rate-v1"'
        return httpx.Response(304)

    client = client_for(tmp_path, handler)
    url = "https://example.com/prices"
    assert client.get(url) == client.get(url) == {"rate": "0.526"}
    cached = read_json(tmp_path / (digest(url) + ".json"))
    assert len(cached["response_digest"]) == 64
    assert client.visited == [url, url]
    with pytest.raises(ValueError):
        client.get("http://example.com/prices")


def test_source_retries_resume_and_long_limits_fail(tmp_path, monkeypatch):
    waits = []
    monkeypatch.setattr("packages.prices.client.time.sleep", waits.append)
    responses = [
        httpx.Response(503),
        httpx.Response(429, headers={"Retry-After": "2"}),
        httpx.Response(200, json=[]),
    ]
    client = client_for(tmp_path, lambda _: responses.pop(0))
    assert client.get("https://example.com/retry") == []
    assert waits == [1, 2]
    client = client_for(tmp_path, lambda _: httpx.Response(403, headers={"Retry-After": "61"}))
    with pytest.raises(RuntimeError, match="resume"):
        client.get("https://example.com/limited")
    client = client_for(tmp_path, lambda _: httpx.Response(429, headers={"Retry-After": "1"}))
    with pytest.raises(RuntimeError, match="exhausted"):
        client.get("https://example.com/exhausted")
    client = client_for(tmp_path, lambda _: httpx.Response(404))
    with pytest.raises(httpx.HTTPStatusError):
        client.get("https://example.com/missing")


def test_source_pagination_keeps_all_complete_pages(tmp_path):
    def handler(request):
        page = int(request.url.params["page"])
        assert request.url.params["per_page"] == "100"
        return httpx.Response(
            200,
            json={"jobs": [{"id": 100 * (page - 1) + i} for i in range(100 if page == 1 else 3)]},
        )

    client = client_for(tmp_path, handler)
    rows = client.github_pages("https://example.com/jobs?status=completed", "jobs")
    assert [row["id"] for row in rows] == list(range(103))


def test_model_partition_accounts_for_unowned_rows():
    from packages.allocation.engine import allocate_models

    bills = {"ads": 100, "unallocated": 20, "empty": 0}
    weights = {"ads": {"model": 60, "training": 40}, "unallocated": {"model": 20}, "empty": {}}
    assert allocate_models(bills, weights) == {"model": 80, "training": 40}
    with pytest.raises(ValueError):
        allocate_models(bills, {"ads": {"model": 1}})


def test_storage_commits_across_processes_and_closes_atomically(tmp_path):
    import json
    import os
    import subprocess
    import sys
    from datetime import UTC, datetime

    from sqlalchemy import BigInteger

    from packages.api.storage import RequestLog, Store
    from packages.core.io import ROOT

    salt = "test-only-salt-for-local-verification"
    database = "sqlite:///" + str(tmp_path / "independent.sqlite")
    store = Store(database, salt)
    identifier = store.append(
        "forecast", {"book": "platform", "team": "ads"}, {"point_usd": "5000"}, "2025-01"
    )
    code = "from packages.api.storage import Store;import json,os,sys;print(json.dumps(Store(os.environ['TEST_DB'],os.environ['TEST_SALT']).get(sys.argv[1])))"
    output = subprocess.check_output(
        [sys.executable, "-c", code, identifier],
        env={**os.environ, "TEST_DB": database, "TEST_SALT": salt},
        cwd=ROOT,
        text=True,
    )
    assert json.loads(output)["id"] == identifier
    assert isinstance(RequestLog.__table__.c.actual_micro.type, BigInteger)
    with pytest.raises(ValueError, match="not closed"):
        store.close_period("2025-01", {}, datetime(2025, 1, 15, tzinfo=UTC))
    with pytest.raises(ValueError, match="Missing actual"):
        store.close_period("2025-01", {}, datetime(2025, 2, 1, tzinfo=UTC))
    assert store.get(identifier)["scored_at"] is None
    assert (
        store.close_period(
            "2025-01", {"platform:ads": 5000000000}, datetime(2025, 2, 1, tzinfo=UTC)
        )
        == 1
    )
    assert store.get(identifier)["actual_micro"] == 5000000000
    assert store.close_period("2025-01", {}, datetime(2025, 2, 1, tzinfo=UTC)) == 0
    assert store.get("absent") is None

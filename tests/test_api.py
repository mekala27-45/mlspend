from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, date, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from packages.api.app import create_app, estimate_workload
from packages.api.storage import Store
from packages.core.contracts import EstimateRequest
from packages.core.io import STATEMENT
from packages.prices.book import PriceBook

SALT = "test-only-random-salt-not-a-credential"


@pytest.fixture
def client(tmp_path):
    api = create_app("sqlite:///" + str(tmp_path / "log.sqlite"), SALT)
    with TestClient(api) as connection:
        yield connection, api.state.store


def test_estimate_is_committed_before_response_and_readable_independently(client, tmp_path):
    connection, store = client
    request = {
        "price_id": "azure-t4",
        "requests_per_day": 100000,
        "seconds_per_request": "0.1",
        "capacity_per_replica": 1,
        "minimum_replicas": 1,
        "days": 30,
    }
    response = connection.post("/v1/estimate", json=request)
    assert response.status_code == 200
    result = response.json()
    assert result["shadow_cost_usd"] == "378.720"
    independent = Store(str(store.engine.url), SALT)
    row = independent.get(result["id"])
    assert row is not None and row["kind"] == "estimate"
    assert json.loads(row["result"])["shadow_cost_usd"] == result["shadow_cost_usd"]
    assert response.headers["X-Price-Ids"] == "vercel-cpu,vercel-memory"
    assert float(response.headers["X-Shadow-Cost-USD"]) >= 0
    assert float(response.headers["X-CPU-Seconds"]) >= 0


def test_forecast_committed_and_scored_only_after_close(client):
    connection, store = client
    payload = {
        "book": "portfolio",
        "team": "search",
        "period": "2099-01",
        "point_usd": "10",
        "lower_usd": "8",
        "upper_usd": "13",
        "data_cutoff": date.today().isoformat(),
    }
    response = connection.post("/v1/forecasts", json=payload)
    assert response.status_code == 200
    identifier = response.json()["id"]
    assert connection.get("/v1/forecasts/" + identifier).status_code == 200
    independent = Store(str(store.engine.url), SALT)
    assert independent.get(identifier)["period"] == "2099-01"
    with pytest.raises(ValueError):
        store.close_period(
            "2099-01", {"portfolio:search": 12000000}, datetime(2099, 1, 20, tzinfo=UTC)
        )
    with pytest.raises(ValueError):
        store.close_period("2099-01", {}, datetime(2099, 2, 1, tzinfo=UTC))
    assert independent.get(identifier)["scored_at"] is None
    assert (
        store.close_period(
            "2099-01", {"portfolio:search": 12000000}, datetime(2099, 2, 1, tzinfo=UTC)
        )
        == 1
    )
    assert independent.get(identifier)["actual_micro"] == 12000000
    assert store.close_period("2099-01", {}, datetime(2099, 2, 1, tzinfo=UTC)) == 0


def test_all_routes_have_disclosure_and_meter(client):
    connection, _ = client
    for path in (
        "/health",
        "/v1/showback",
        "/v1/unit-costs",
        "/v1/anomalies",
        "/not-real",
        "/v1/forecasts/not-real",
        "/v1/showback?method=bad",
        "/v1/showback?month=1900-01",
    ):
        result = connection.get(path)
        assert result.json()["statement"] == STATEMENT
        assert "x-shadow-cost-usd" in result.headers
    assert connection.get("/health").json()["meter_median_usd"] is not None
    assert (
        connection.get("/v1/showback?team=search&method=direct").json()["rows"][0]["team"]
        == "search"
    )


def test_bad_requests_and_missing_persistence(client, tmp_path, monkeypatch):
    connection, _ = client
    assert connection.post("/v1/estimate", json={}).status_code == 422
    bad = {
        "price_id": "missing",
        "requests_per_day": 1,
        "seconds_per_request": "1",
        "capacity_per_replica": 1,
    }
    assert connection.post("/v1/estimate", json=bad).status_code == 422
    assert (
        connection.post(
            "/v1/forecasts",
            json={
                "book": "platform",
                "team": "search",
                "period": "2000-01",
                "point_usd": "1",
                "lower_usd": "0",
                "upper_usd": "2",
                "data_cutoff": "1999-12-31",
            },
        ).status_code
        == 422
    )
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("MLSPEND_SALT", raising=False)
    with TestClient(create_app(manifest_path=tmp_path / "absent.json")) as empty:
        assert empty.get("/health").json()["status"] == "configuration_required"
        for path in ("/v1/showback", "/v1/unit-costs", "/v1/anomalies", "/v1/forecasts/x"):
            assert empty.get(path).status_code == 503
        good = {**bad, "price_id": "azure-t4"}
        assert empty.post("/v1/estimate", json=good).status_code == 503


def test_budget_is_atomic_and_resets_with_hour(tmp_path):
    store = Store("sqlite:///" + str(tmp_path / "budget.sqlite"), SALT)
    with ThreadPoolExecutor(max_workers=8) as pool:
        accepted = list(pool.map(lambda _: store.permit("127.0.0.1", 3600), range(80)))
    assert sum(accepted) == 60
    assert store.permit("127.0.0.1", 7200)
    with store.engine.connect() as connection:
        values = connection.execute(
            text("select client_hash from mlspend_client_budget")
        ).fetchall()
    assert all("127.0.0.1" not in row[0] for row in values)
    with pytest.raises(ValueError):
        Store("sqlite://", "short")


def test_api_budget_returns_429(client):
    connection, _ = client
    responses = [connection.get("/v1/unit-costs") for _ in range(61)]
    assert all(r.status_code == 200 for r in responses[:60])
    assert responses[-1].status_code == 429


def test_estimate_capacity_threshold():
    book = PriceBook()
    request = EstimateRequest(
        price_id="azure-cpu",
        requests_per_day=86401,
        seconds_per_request="1",
        capacity_per_replica=1,
        minimum_replicas=0,
        days=1,
    )
    assert estimate_workload(request, book)["replicas"] == 2


@pytest.mark.postgres
def test_postgres_independent_connection():
    import os

    url = os.environ.get("MLSPEND_TEST_DATABASE_URL")
    if not url:
        pytest.skip("MLSPEND_TEST_DATABASE_URL is not configured")
    first = Store(url, SALT)
    second = Store(url, SALT)
    identifier = first.append("estimate", {}, {"statement": STATEMENT})
    assert second.get(identifier) is not None

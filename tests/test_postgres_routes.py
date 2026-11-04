import os
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from packages.api.app import create_app
from packages.api.storage import Store
from packages.core.io import ROOT
from packages.prices.book import PriceBook
from packages.stretch.guardrail import BudgetRequest, Guardrail, TrainingRequest

pytestmark = pytest.mark.postgres
SALT = "test-only-postgres-salt-not-a-credential"


@pytest.fixture
def postgres_url():
    url = os.environ.get("MLSPEND_TEST_DATABASE_URL")
    if not url:
        pytest.skip("MLSPEND_TEST_DATABASE_URL is not configured")
    return url


def test_postgres_budget_is_atomic(postgres_url):
    store = Store(postgres_url, SALT)
    client = str(uuid4())
    try:
        with ThreadPoolExecutor(max_workers=8) as pool:
            allowed = list(pool.map(lambda _: store.permit(client, 3600), range(80)))
        assert sum(allowed) == 60
        assert store.permit(client, 7200)
    finally:
        store.engine.dispose()


def test_postgres_dashboard_and_estimate_routes(postgres_url):
    # The health SELECT can pass while request-budget SQL fails. Exercise a metered route.
    with TestClient(create_app(postgres_url, SALT + str(uuid4()))) as client:
        assert client.get("/health").json()["status"] == "ready"
        assert client.get("/v1/showback").status_code == 200
        response = client.post(
            "/v1/estimate",
            json={
                "price_id": "azure-t4",
                "requests_per_day": 17,
                "seconds_per_request": "0.1",
                "capacity_per_replica": 1,
                "minimum_replicas": 1,
                "days": 1,
            },
        )
        assert response.status_code == 200
        identifier = response.json()["id"]
        assert client.get("/v1/estimates/" + identifier).json()["estimate"]["id"] == identifier


def test_postgres_training_admission_conserves_budget(postgres_url):
    from decimal import Decimal

    store = Store(postgres_url, SALT)
    guard = Guardrail(store.engine)
    budget = guard.create_budget(BudgetRequest(limit_usd=Decimal("1")))
    book = PriceBook(ROOT / "data/prices/expanded")
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(
            pool.map(
                lambda _: guard.admit(
                    budget["id"], TrainingRequest(request_id=uuid4(), hours=Decimal("1")), book
                ),
                range(20),
            )
        )
    assert sum(r["reserved_micro"] for r in results) <= 1000000
    assert any(r["accepted"] for r in results)
    assert any(not r["accepted"] for r in results)
    assert all(r["remaining_after_micro"] >= 0 for r in results)


def test_postgres_training_http_decision_is_saved(postgres_url):
    with TestClient(create_app(postgres_url, SALT + str(uuid4()))) as client:
        budget = client.post("/v1/simulation/budgets", json={"limit_usd": "1"})
        assert budget.status_code == 200
        path = "/v1/simulation/budgets/" + budget.json()["id"] + "/admissions"
        payload = {"request_id": str(uuid4()), "hours": "1", "price_id": "azure-t4"}
        accepted = client.post(path, json=payload)
        assert accepted.status_code == 200
        assert accepted.json()["accepted"]
        replay = client.post(path, json=payload)
        assert replay.json()["replayed"]
        assert replay.json()["remaining_after_micro"] == accepted.json()["remaining_after_micro"]
        refused = client.post(
            path, json={**payload, "request_id": str(uuid4()), "hours": "48", "attempts": 3}
        )
        assert refused.status_code == 409
        assert not refused.json()["accepted"]

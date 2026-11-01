from fastapi.testclient import TestClient

from packages.api.app import create_app
from packages.api.storage import Store

SALT = "test-only-hosting-salt-not-a-credential"


def test_estimate_readback_survives_new_application(tmp_path):
    url = "sqlite:///" + str(tmp_path / "persistent.sqlite")
    first = TestClient(create_app(url, SALT))
    response = first.post(
        "/v1/estimate",
        json={
            "price_id": "azure-t4",
            "requests_per_day": 10,
            "seconds_per_request": "0.1",
            "capacity_per_replica": 1,
            "minimum_replicas": 1,
            "days": 30,
        },
    )
    assert response.status_code == 200
    identifier = response.json()["id"]
    second = TestClient(create_app(url, SALT))
    recovered = second.get("/v1/estimates/" + identifier)
    assert recovered.status_code == 200
    assert recovered.json()["estimate"]["id"] == identifier
    assert second.get("/health").json()["database"] == "connected"
    assert Store(url, SALT).get(identifier) is not None


def test_unconfigured_estimate_readback_refuses():
    client = TestClient(create_app())
    assert client.get("/v1/estimates/nonexistent").status_code == 503


def test_dashboard_is_served_by_deployment_entrypoint():
    from index import app

    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert "THE COST LEDGER" in response.text
    assert client.get("/data.json").json()["allocation"]
    assert client.get("/health").status_code == 200

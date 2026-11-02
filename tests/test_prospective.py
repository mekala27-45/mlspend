import json
from datetime import UTC, date, datetime

import pytest
from fastapi.testclient import TestClient

from packages.api.app import create_app
from packages.api.storage import Store
from packages.core.contracts import ForecastRequest
from packages.forecast.prospective import forecast
from packages.forecast.scoring import score_forecast

SALT = "prospective-test-salt-not-a-credential"


def payload(team="ads", simulation_id="unit-simulation-a"):
    return {
        "book": "platform",
        "team": team,
        "period": "2026-01",
        "data_cutoff": "2025-12-31",
        "point_usd": "10",
        "lower_usd": "8",
        "upper_usd": "13",
        "clock": "simulation",
        "simulation_id": simulation_id,
        "plan_digest": "a" * 64,
    }


def test_simulation_contract_requires_complete_separate_identity():
    for changes in (
        {"book": "portfolio"},
        {"simulation_id": None},
        {"plan_digest": None},
        {"clock": "calendar"},
        {"data_cutoff": "2026-01-01"},
    ):
        with pytest.raises(ValueError):
            ForecastRequest(**{**payload(), **changes})


def test_simulation_close_is_atomic_isolated_and_uses_real_recording_time(tmp_path):
    url = "sqlite:///" + str(tmp_path / "close.sqlite")
    store = Store(url, SALT)
    independent = Store(url, SALT)
    with TestClient(create_app(url, SALT)) as client:
        ids = [
            client.post("/v1/forecasts", json=payload(team)).json()["id"]
            for team in ("ads", "search")
        ]
        other = client.post(
            "/v1/forecasts", json=payload(simulation_id="unit-simulation-b")
        ).json()["id"]
        real = store.append("forecast", {"book": "portfolio", "team": "ads"}, {}, "2026-01")
        assert all(independent.get(identifier)["actual_micro"] is None for identifier in ids)
        assert client.get("/v1/forecasts/" + ids[0]).json()["score"] is None
        with pytest.raises(ValueError, match="has not closed"):
            store.close_simulation(
                "2026-01",
                "unit-simulation-a",
                {"platform:ads": 12000000},
                datetime(2026, 1, 31, tzinfo=UTC),
            )
        with pytest.raises(ValueError, match="Missing actual"):
            store.close_simulation(
                "2026-01",
                "unit-simulation-a",
                {"platform:ads": 12000000},
                datetime(2026, 2, 1, tzinfo=UTC),
            )
        assert all(independent.get(identifier)["actual_micro"] is None for identifier in ids)
        with pytest.raises(ValueError, match="integer"):
            store.close_simulation(
                "2026-01",
                "unit-simulation-a",
                {"platform:ads": True},
                datetime(2026, 2, 1, tzinfo=UTC),
            )
        before = datetime.now(UTC)
        actuals = {"platform:ads": 12000000, "platform:search": 16000000}
        assert (
            store.close_simulation(
                "2026-01", "unit-simulation-a", actuals, datetime(2026, 2, 1, tzinfo=UTC)
            )
            == 2
        )
        assert (
            store.close_simulation(
                "2026-01", "unit-simulation-a", actuals, datetime(2026, 2, 1, tzinfo=UTC)
            )
            == 0
        )
        for identifier in ids:
            row = independent.get(identifier)
            assert before <= datetime.fromisoformat(row["scored_at"]) <= datetime.now(UTC)
            assert client.get("/v1/forecasts/" + identifier).json()["score"] == score_forecast(row)
        assert independent.get(other)["actual_micro"] is None
        assert independent.get(real)["actual_micro"] is None
        assert client.get("/v1/forecasts/" + ids[0]).json()["score"]["covered"] is True
        assert client.get("/v1/forecasts/" + ids[1]).json()["score"]["covered"] is False
        with pytest.raises(ValueError, match="cannot be revised"):
            store.close_simulation(
                "2026-01",
                "unit-simulation-a",
                {**actuals, "platform:ads": 0},
                datetime(2026, 2, 1, tzinfo=UTC),
            )
        with pytest.raises(ValueError, match="No forecasts"):
            store.close_simulation(
                "2026-01", "missing-simulation", actuals, datetime(2026, 2, 1, tzinfo=UTC)
            )
    store.engine.dispose()
    independent.engine.dispose()


def test_calendar_close_never_selects_simulation_records(tmp_path):
    store = Store("sqlite:///" + str(tmp_path / "calendar.sqlite"), SALT)
    identifier = store.append("simulation_forecast", payload(), {}, "2026-01")
    assert store.close_period("2026-01", {}, datetime(2026, 2, 1, tzinfo=UTC)) == 0
    assert store.get(identifier)["scored_at"] is None


def test_forecast_uses_prior_costs_and_score_keeps_exact_money():
    history = [
        {"team": "ads", "month": f"2025-{i:02d}", "cost_micro": 1000000 * i} for i in range(1, 13)
    ]
    result = forecast(history, "ads", 0.8)
    assert result == {"point_usd": "11", "lower_usd": "9", "upper_usd": "13"}
    with pytest.raises(ValueError):
        forecast(history[:4], "ads", 0.8)
    with pytest.raises(ValueError, match="Insufficient"):
        forecast(history, "ads", 0.99)
    score = score_forecast(
        {
            "payload": json.dumps(payload()),
            "actual_micro": 10000001,
            "scored_at": date.today().isoformat(),
        }
    )
    assert score["absolute_error_usd"] == "0.000001"


def test_issue_then_close_pipeline_requires_persistence_before_outcomes(tmp_path, monkeypatch):
    from packages.core.io import read_json
    from packages.evaluation import prospective
    from packages.truth import prospective as truth

    url = "sqlite:///" + str(tmp_path / "pipeline.sqlite")
    api = create_app(url, SALT)
    history = [
        {"team": team, "month": f"2025-{i:02d}", "cost_micro": i * 1000000}
        for team in ("ads", "search")
        for i in range(1, 13)
    ]
    plan = {
        "teams": ["ads", "search"],
        "period": "2026-01",
        "data_cutoff": "2025-12-31",
        "coverage": 0.8,
        "seed": 17,
        "simulated_close": "2026-02-01T00:00:00+00:00",
        "limits": ["Test fixture"],
    }
    monkeypatch.setattr(prospective, "registered_inputs", lambda: (plan, history, "a" * 64))
    monkeypatch.setattr(prospective, "connection", lambda: Store(url, SALT))
    monkeypatch.setattr(prospective.httpx, "Client", lambda **kwargs: TestClient(api))
    monkeypatch.setenv("GITHUB_RUN_ID", "12345678")
    monkeypatch.setenv("GITHUB_RUN_ATTEMPT", "1")
    monkeypatch.setenv("GITHUB_SHA", "fixture")
    issued = tmp_path / "issued.json"
    closed = tmp_path / "close.json"

    def outcomes_after_persistence(*args):
        records = read_json(issued)["records"]
        assert len(records) == 2
        for record in records:
            assert api.state.store.get(record["id"])["actual_micro"] is None
        return {"platform:ads": 12000000, "platform:search": 16000000}

    monkeypatch.setattr(truth, "outcomes", outcomes_after_persistence)
    prospective.issue(issued)
    assert read_json(issued)["outcomes_generated"] is False
    prospective.close(issued, closed)
    result = read_json(closed)
    assert result["total_scored"] == 2
    assert result["idempotent_replay_updates"] == 0
    assert result["calendar_records_unchanged"] is True
    assert [r["score"]["covered"] for r in result["rows"]] == [True, False]


def test_registered_observations_cannot_drift_or_include_the_target(tmp_path, monkeypatch):
    from packages.core.io import digest, write_json
    from packages.evaluation import prospective

    monkeypatch.setattr(prospective, "FOLDER", tmp_path)
    history = [{"month": "2025-12", "team": "ads", "cost_micro": 100}]
    plan = {"period": "2026-01", "history_digest": digest(history)}
    write_json(tmp_path / "plan.json", plan)
    write_json(tmp_path / "history.json", history)
    write_json(
        tmp_path / "registration.json",
        {"plan_digest": digest(plan), "history_digest": digest(history)},
    )
    assert prospective.registered_inputs()[0] == plan
    history[0]["cost_micro"] = 101
    write_json(tmp_path / "history.json", history)
    with pytest.raises(ValueError, match="registration drift"):
        prospective.registered_inputs()
    history[0]["month"] = "2026-01"
    plan["history_digest"] = digest(history)
    write_json(tmp_path / "history.json", history)
    write_json(tmp_path / "plan.json", plan)
    write_json(
        tmp_path / "registration.json",
        {"plan_digest": digest(plan), "history_digest": digest(history)},
    )
    with pytest.raises(ValueError, match="Future observations"):
        prospective.registered_inputs()

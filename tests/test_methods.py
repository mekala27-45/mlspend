from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta

import pytest

from packages.core.io import write_json
from packages.detect.detector import choose_threshold, score_series
from packages.evaluation.score import score_incidents, score_owners
from packages.evaluation.statistics import benjamini_hochberg, cluster_interval, sign_randomization
from packages.forecast.models import backtest, conformal_radius, predict, select_method
from packages.optimize.commitments import expected_cost, optimize
from packages.optimize.recommendations import recommend


def test_forecast_never_reads_future():
    series = [100 + 10 * math.sin(i * 2 * math.pi / 7) + i * 0.05 for i in range(150)]
    first = backtest(series, 100, ["seasonal_naive", "trend"])
    changed = series[:]
    changed[130] = 100000
    second = backtest(changed, 100, ["seasonal_naive", "trend"])
    assert first["method"] == second["method"]
    assert first["rows"][:30] == second["rows"][:30]
    assert first["rows"][30]["point"] == second["rows"][30]["point"]
    assert len(first["rows"]) == 50
    assert all(r["lower"] <= r["point"] <= r["upper"] for r in first["rows"])


def test_forecast_boundaries_and_constant_coverage():
    result = backtest([100.0] * 100, 70, ["seasonal_naive", "trend"])
    assert result["coverage"] == 1 and result["mae"] == 0
    assert predict([100] * 28, "seasonal_naive", 8) == 100
    assert select_method([100] * 60, ["trend", "seasonal_naive"])[0] == "seasonal_naive"
    with pytest.raises(ValueError):
        predict([1], "trend")
    with pytest.raises(ValueError):
        predict([1] * 30, "bad")
    with pytest.raises(ValueError):
        select_method([1], ["trend"])
    with pytest.raises(ValueError):
        backtest([1] * 70, 70, ["trend"])
    with pytest.raises(ValueError):
        conformal_radius([], 0.9)
    with pytest.raises(ValueError):
        conformal_radius([1], 0.99)
    assert conformal_radius([2] * 20, 0.9) == 2


def test_detector_ignores_seasonal_mondays_but_finds_spike():
    start = datetime(2025, 1, 6, tzinfo=UTC)
    rows = []
    for hour in range(24 * 60):
        timestamp = start + timedelta(hours=hour)
        value = 200 if timestamp.weekday() == 0 else 100
        rows.append(
            {
                "timestamp": timestamp.isoformat(),
                "resource": "a",
                "team": "search",
                "cost_micro": value,
            }
        )
    clean = score_series(rows)
    assert max(r["score"] for r in clean) == 0
    rows[-1]["cost_micro"] = 2000
    scored = score_series(rows)
    assert scored[-1]["score"] > 9
    threshold, rates = choose_threshold(scored, "2025-02-20", [3, 5, 9], 0.02)
    assert threshold == 3 and rates["3"] == 0
    with pytest.raises(ValueError):
        choose_threshold([], "2025-02-20", [3], 0.02)


def test_commitment_known_optimum_and_regret():
    result = optimize([2, 2, 2, 8], [2, 2, 2, 8], 1, 0.5)
    assert result["level"] == 2
    assert result["regret_per_hour"] == 0
    assert expected_cost([2, 2], 2, 1, 0.5) == 1
    assert result["coverage"] == pytest.approx(8 / 14)
    assert result["utilization"] == 1
    with pytest.raises(ValueError):
        expected_cost([], 1, 1, 0.5)
    with pytest.raises(ValueError):
        expected_cost([1], 1, 1, 2)


def test_recommendation_does_not_call_capacity_cash():
    values = [{"resource": "x", "requested": 4, "used": 1, "pool": "cpu"}] * 24
    output = recommend(values, 1.25, {"cpu": 1000000})
    assert output[0]["target_units"] == 1.25
    assert output[0]["cash_savings_micro"] is None
    assert output[0]["capacity_value_micro"] == 66000000
    with pytest.raises(ValueError):
        recommend(values, 0.5, {"cpu": 1})


def test_statistical_utilities():
    assert benjamini_hochberg({"a": 0.01, "b": 0.04, "c": 0.03}) == pytest.approx(
        {"a": 0.03, "b": 0.04, "c": 0.04}
    )
    assert cluster_interval({"a": [2, 2], "b": [2]}, 19) == (2, 2)
    assert cluster_interval({"a": [1], "b": [5]}, 19) == cluster_interval({"b": [5], "a": [1]}, 19)
    assert sign_randomization([1] * 6) == pytest.approx(2 / 64)
    for values in ({}, {"a": -1}):
        with pytest.raises(ValueError):
            benjamini_hochberg(values)
    with pytest.raises(ValueError):
        cluster_interval({}, 1)
    with pytest.raises(ValueError):
        sign_randomization([])


def test_independent_event_scores_include_missed_cost(tmp_path):
    start = "2025-09-01T00:00:00+00:00"
    after = "2025-09-01T01:00:00+00:00"
    path = tmp_path / "truth.json"
    write_json(
        path,
        {
            "incidents": [{"id": "x", "start": start, "end": "2025-09-02T00:00:00+00:00"}],
            "incident_hours": [
                {
                    "timestamp": start,
                    "resource": "a",
                    "incident_id": "x",
                    "incremental_asset_micro": 5,
                },
                {
                    "timestamp": after,
                    "resource": "a",
                    "incident_id": "x",
                    "incremental_asset_micro": 5,
                },
            ],
            "counterfactual_savings_micro": {"x": 10},
            "owners": {"a": "search", "b": "ads"},
        },
    )
    output = score_incidents(path, [{"timestamp": after, "resource": "a"}], "2025-09-01")
    assert (
        output["event_recall"] == 1
        and output["median_delay_hours"] == 1
        and output["burned_micro"] == 10
    )
    missed = score_incidents(path, [], "2025-09-01")
    assert (
        missed["event_recall"] == 0
        and missed["burned_micro"] == 10
        and missed["median_delay_hours"] is None
    )
    assert score_owners(path, {"a": "search", "b": "unallocated"})["recall"] == 0.5

import pytest

from packages.detect.expanded import alerts, residuals, select


def test_detects_spike_and_sustained_small_shift():
    scores = [0.0] * 20 + [2.0] * 10
    assert not any(alerts(scores, 5, "seasonal_mad"))
    assert any(alerts(scores, 5, "positive_cusum"))
    assert alerts([None, 0, 20], 5, "seasonal_mad") == [False, False, True]


def test_seasonal_residual_never_uses_future_data():
    series = [10.0] * 60
    assert residuals(series, 7, 4)[:50] == residuals(series[:50] + [999.0] * 10, 7, 4)[:50]
    series[50] = 100
    assert residuals(series, 7, 4)[50] > 10


def test_empty_calibration_rejected_and_boundary_reported():
    config = {
        "methods": ["seasonal_mad"],
        "threshold_candidates": [3, 5, 7],
        "cusum_drift": 0.5,
        "false_alarm_budget": 0.02,
    }
    with pytest.raises(ValueError, match="No normal"):
        select([None], [False], config)
    result = select([0.0] * 20, [True] * 20, config)
    assert result["budget_met"]
    assert not result["interior"]

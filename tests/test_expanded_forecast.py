from datetime import date

import pytest

from packages.core.io import ROOT, read_json
from packages.forecast.expanded import budgets, features, horizon


def test_features_do_not_read_target_or_future_workload():
    costs = list(range(100))
    a = features(costs, costs, date(2025, 1, 1), 56)
    changed = costs[:56] + [999999] * 44
    assert features(changed, changed, date(2025, 1, 1), 56) == a
    with pytest.raises(ValueError):
        features(costs, costs, date(2025, 1, 1), 12)


def test_boost_forecast_is_nonnegative_and_uses_only_given_history():
    config = read_json(ROOT / "evaluation/v2/plan.json")["forecast"]
    costs = [100.0 + i / 10 + (i % 7) * 3 for i in range(70)]
    result = horizon(costs, costs, date(2025, 1, 1), "gradient_boosting", 7, config)
    assert len(result) == 7
    assert all(0 < value < 200 for value in result)
    assert result == horizon(costs, costs, date(2025, 1, 1), "gradient_boosting", 7, config)


def test_budget_uses_last_development_month_and_resets():
    config = {"monthly_multiplier": 1.1, "warning_fraction": 0.8, "critical_fraction": 1}
    result = budgets([10.0] * 100, date(2025, 1, 1), 59, config)
    assert result["budget"] == pytest.approx(28 * 10 * 1.1)
    assert result["rows"][0]["spent"] == 10
    assert result["rows"][31]["spent"] == 10

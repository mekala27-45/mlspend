"""Rolling-origin forecasts with calendar and strictly lagged workload features."""

from __future__ import annotations

import calendar
import math
from collections.abc import Sequence
from datetime import date, timedelta
from statistics import mean
from typing import Any

from packages.forecast.models import conformal_radius, predict


def features(
    costs: Sequence[float], workloads: Sequence[float], start: date, index: int
) -> list[float]:
    if index < 28 or len(costs) < index or len(workloads) < index:
        raise ValueError("Features require strictly prior history")
    day = start + timedelta(days=index)
    return [
        index,
        day.weekday(),
        day.month,
        math.sin(day.weekday() * 2 * math.pi / 7),
        math.cos(day.weekday() * 2 * math.pi / 7),
        costs[index - 1],
        costs[index - 7],
        costs[index - 28],
        mean(costs[index - 7 : index]),
        mean(costs[index - 28 : index]),
        workloads[index - 7],
        mean(workloads[index - 7 : index]),
    ]


def fit_boost(
    costs: Sequence[float], workload: Sequence[float], start: date, config: dict[str, Any]
) -> Any:
    from sklearn.ensemble import GradientBoostingRegressor

    if len(costs) < 56:
        raise ValueError("Boosting requires eight weeks of history")
    model = GradientBoostingRegressor(random_state=0, loss="squared_error", **config)
    model.fit([features(costs, workload, start, i) for i in range(28, len(costs))], costs[28:])
    return model


def daily(
    costs: Sequence[float],
    workload: Sequence[float],
    start: date,
    development_days: int,
    config: dict[str, Any],
) -> dict[str, Any]:
    if len(costs) != len(workload) or not config["minimum_history_days"] < development_days < len(
        costs
    ):
        raise ValueError("Aligned series with development and holdout required")
    predictions: dict[str, list[tuple[int, float]]] = {name: [] for name in config["candidates"]}
    model = None
    for i in range(config["minimum_history_days"], len(costs)):
        if model is None or (i - config["minimum_history_days"]) % config["refit_every_days"] == 0:
            model = fit_boost(costs[:i], workload[:i], start, config["gradient_boosting"])
        for name in predictions:
            if name == "gradient_boosting":
                point = max(0.0, float(model.predict([features(costs, workload, start, i)])[0]))
            else:
                point = predict(costs[:i], "trend" if name == "trend_seasonal" else name)
            predictions[name].append((i, point))
    losses = {
        name: mean(abs(costs[i] - p) for i, p in values if i < development_days)
        for name, values in predictions.items()
    }
    selected = min(losses, key=lambda name: (losses[name], name))
    errors: list[float] = []
    rows = []
    for i, point in predictions[selected]:
        if i >= development_days:
            radius = conformal_radius(
                errors[-config["calibration_days"] :], config["interval_coverage"]
            )
            lower, upper = max(0.0, point - radius), point + radius
            baseline = predict(costs[:i], "seasonal_naive")
            rows.append(
                {
                    "date": (start + timedelta(days=i)).isoformat(),
                    "point": point,
                    "lower": lower,
                    "upper": upper,
                    "actual": costs[i],
                    "covered": lower <= costs[i] <= upper,
                    "naive": baseline,
                }
            )
        errors.append(abs(costs[i] - point))
    return {
        "method": selected,
        "development_mae": losses,
        "mae": mean(abs(r["actual"] - r["point"]) for r in rows),
        "coverage": mean(r["covered"] for r in rows),
        "rows": rows,
        "interval_kind": "rolling finite-sample conformal, serial dependence not guaranteed",
        "predictions": predictions,
    }


def horizon(
    costs: Sequence[float],
    workload: Sequence[float],
    start: date,
    method: str,
    days: int,
    config: dict[str, Any],
) -> list[float]:
    """Recursive calendar forecast; never reads demand from the future horizon."""
    history, work = list(costs), list(workload)
    model = (
        fit_boost(history, work, start, config["gradient_boosting"])
        if method == "gradient_boosting"
        else None
    )
    result = []
    for _ in range(days):
        point = (
            max(0.0, float(model.predict([features(history, work, start, len(history))])[0]))
            if model is not None
            else predict(history, "trend" if method == "trend_seasonal" else method)
        )
        result.append(point)
        history.append(point)
        work.append(work[-7])
    return result


def monthly(
    costs: Sequence[float],
    workload: Sequence[float],
    start: date,
    development_days: int,
    method: str,
    config: dict[str, Any],
) -> list[dict[str, Any]]:
    rows = []
    for index in range(development_days, len(costs)):
        day = start + timedelta(days=index)
        if day.day != 1:
            continue
        days = calendar.monthrange(day.year, day.month)[1]
        if index + days > len(costs):
            continue
        errors = []
        # Completed prior horizons only, including the final day in the cutoff.
        for origin in range(max(56, index - 84), index - days + 1):
            forecast = horizon(costs[:origin], workload[:origin], start, method, days, config)
            errors.append(abs(sum(costs[origin : origin + days]) - sum(forecast)))
        radius = conformal_radius(errors, config["interval_coverage"])
        point = sum(horizon(costs[:index], workload[:index], start, method, days, config))
        actual = sum(costs[index : index + days])
        lower, upper = max(0.0, point - radius), point + radius
        rows.append(
            {
                "period": day.strftime("%Y-%m"),
                "data_cutoff": (day - timedelta(days=1)).isoformat(),
                "method": method,
                "point": point,
                "lower": lower,
                "upper": upper,
                "actual": actual,
                "covered": lower <= actual <= upper,
                "calibration_origins": len(errors),
            }
        )
    return rows


def budgets(
    costs: Sequence[float], start: date, development_days: int, config: dict[str, Any]
) -> dict[str, Any]:
    cutoff = start + timedelta(days=development_days)
    prior = cutoff - timedelta(days=1)
    reference_start = (prior.replace(day=1) - start).days
    limit = sum(costs[reference_start:development_days]) * config["monthly_multiplier"]
    rows = []
    accumulated = 0.0
    for i in range(development_days, len(costs)):
        day = start + timedelta(days=i)
        if day.day == 1:
            accumulated = 0
        accumulated += costs[i]
        days = calendar.monthrange(day.year, day.month)[1]
        burn = accumulated / day.day
        projected = burn * days
        rows.append(
            {
                "date": day.isoformat(),
                "budget": limit,
                "spent": accumulated,
                "daily_burn": burn,
                "projected_month_end": projected,
                "projected_exhaustion_day": math.ceil(limit / burn) if burn else None,
                "severity": "critical"
                if projected >= limit * config["critical_fraction"]
                else ("warning" if projected >= limit * config["warning_fraction"] else "normal"),
            }
        )
    return {"reference_period": prior.strftime("%Y-%m"), "budget": limit, "rows": rows}

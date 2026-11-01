from __future__ import annotations

import math
from collections.abc import Sequence
from statistics import mean


def predict(history: Sequence[float], method: str, horizon: int = 1) -> float:
    if len(history) < 28 or horizon < 1:
        raise ValueError("At least four weeks of history required")
    index = len(history) + horizon - 1
    offset = (index - len(history)) % 7
    seasonal = history[-7 + offset]
    if method == "seasonal_naive":
        return max(0, seasonal)
    if method != "trend":
        raise ValueError("Unknown forecasting method")
    weeks = [
        mean(history[-28 + i * 7 : -28 + (i + 1) * 7] if i < 3 else history[-7:]) for i in range(4)
    ]
    slope = sum((i - 1.5) * (value - mean(weeks)) for i, value in enumerate(weeks)) / 5
    return max(0, seasonal + slope * math.ceil(horizon / 7))


def conformal_radius(errors: Sequence[float], coverage: float) -> float:
    if not errors or not 0 < coverage < 1:
        raise ValueError("Calibration errors and coverage required")
    ordered = sorted(abs(v) for v in errors)
    rank = math.ceil((len(ordered) + 1) * coverage)
    if rank > len(ordered):
        raise ValueError("Too few calibration errors for finite conformal interval")
    return ordered[rank - 1]


def select_method(
    values: Sequence[float], candidates: Sequence[str]
) -> tuple[str, dict[str, float]]:
    if len(values) < 56 or not candidates:
        raise ValueError("Need development history and candidates")
    losses = {
        name: mean(abs(values[i] - predict(values[:i], name)) for i in range(28, len(values)))
        for name in sorted(candidates)
    }
    return min(losses, key=lambda name: (losses[name], name)), losses


def backtest(
    values: Sequence[float], development_days: int, candidates: Sequence[str], coverage: float = 0.9
) -> dict[str, object]:
    if len(values) <= development_days:
        raise ValueError("No held-out observations")
    selected, development = select_method(values[:development_days], candidates)
    errors = [abs(values[i] - predict(values[:i], selected)) for i in range(28, development_days)]
    rows = []
    for index in range(development_days, len(values)):
        point = predict(values[:index], selected)
        radius = conformal_radius(errors[-56:], coverage)
        lower, upper = max(0, point - radius), point + radius
        rows.append(
            {
                "index": index,
                "actual": values[index],
                "point": point,
                "lower": lower,
                "upper": upper,
                "covered": lower <= values[index] <= upper,
            }
        )
        errors.append(abs(values[index] - point))
    return {
        "method": selected,
        "development_mae": development,
        "rows": rows,
        "mae": mean(abs(float(r["actual"]) - float(r["point"])) for r in rows),
        "coverage": mean(bool(r["covered"]) for r in rows),
        "interval_kind": "rolling empirical conformal; serial dependence may reduce coverage",
    }

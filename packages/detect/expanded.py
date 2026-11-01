"""Observed-only seasonal residuals and a one-sided change-point statistic."""

from __future__ import annotations

from collections.abc import Sequence
from statistics import median
from typing import Any


def residuals(values: Sequence[float], season: int = 168, weeks: int = 4) -> list[float | None]:
    if season < 1 or weeks < 2:
        raise ValueError("Positive season and at least two periods required")
    result: list[float | None] = [None] * min(season * weeks, len(values))
    for i in range(season * weeks, len(values)):
        history = [values[i - season * lag] for lag in range(1, weeks + 1)]
        center = median(history)
        scale = max(1.4826 * median(abs(x - center) for x in history), abs(center) * 0.02, 0.000001)
        result.append((values[i] - center) / scale)
    return result


def alerts(
    scores: Sequence[float | None], threshold: float, method: str, drift: float = 0.5
) -> list[bool]:
    if threshold <= 0 or method not in {"seasonal_mad", "positive_cusum"}:
        raise ValueError("Valid detector and positive threshold required")
    state = 0.0
    result = []
    for score in scores:
        if score is None:
            result.append(False)
            continue
        state = max(0, state + score - drift)
        hit = score > threshold if method == "seasonal_mad" else state > threshold
        result.append(hit)
        if hit and method == "positive_cusum":
            state = 0.0
    return result


def select(
    scores: Sequence[float | None], normal_development: Sequence[bool], config: dict[str, Any]
) -> dict[str, Any]:
    """The evaluator supplies only development labels; no truth files are opened."""
    if len(scores) != len(normal_development):
        raise ValueError("Calibration labels must align")
    denominator = sum(
        normal and score is not None
        for normal, score in zip(normal_development, scores, strict=True)
    )
    if not denominator:
        raise ValueError("No normal development observations to calibrate")
    choices = []
    for method in config["methods"]:
        for threshold in config["threshold_candidates"]:
            found = alerts(scores, threshold, method, config["cusum_drift"])
            false_alarm = (
                sum(hit and normal for hit, normal in zip(found, normal_development, strict=True))
                / denominator
            )
            choices.append(
                {"method": method, "threshold": threshold, "false_alarm_rate": false_alarm}
            )
    accepted = [r for r in choices if r["false_alarm_rate"] <= config["false_alarm_budget"]]
    # Prefer seasonal residuals when equally sensitive. Calibration never sees holdout events.
    chosen = (
        min(accepted, key=lambda r: (r["threshold"], r["method"] != "seasonal_mad"))
        if accepted
        else max(choices, key=lambda r: r["threshold"])
    )
    return {
        **chosen,
        "budget_met": bool(accepted),
        "interior": min(config["threshold_candidates"])
        < chosen["threshold"]
        < max(config["threshold_candidates"]),
        "curve": choices,
        "calibration_normal_points": denominator,
    }

"""Registered supplemental forecast using only previously observed monthly costs."""

from __future__ import annotations

import math
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Any


def forecast(history: list[dict[str, Any]], team: str, coverage: float) -> dict[str, str]:
    rows = sorted((r for r in history if r["team"] == team), key=lambda r: r["month"])
    values = [Decimal(r["cost_micro"]) for r in rows]
    if len(values) < 12 or not 0 < coverage < 1:
        raise ValueError("Twelve prior months and a valid coverage level are required")
    errors = sorted(
        abs(values[i] - sum(values[i - 3 : i], Decimal(0)) / 3) for i in range(3, len(values))
    )
    rank = math.ceil((len(errors) + 1) * coverage)
    if rank > len(errors):
        raise ValueError("Insufficient prior calibration residuals")
    point = (sum(values[-3:], Decimal(0)) / 3).quantize(Decimal(1), rounding=ROUND_HALF_EVEN)
    radius = errors[rank - 1].to_integral_value(rounding="ROUND_CEILING")
    return {
        key: str(value / 1000000)
        for key, value in {
            "point_usd": point,
            "lower_usd": max(Decimal(0), point - radius),
            "upper_usd": point + radius,
        }.items()
    }

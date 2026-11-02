"""Derive scores from immutable forecasts and separately recorded actuals."""

from __future__ import annotations

import json
from decimal import Decimal
from typing import Any


def score_forecast(row: dict[str, Any]) -> dict[str, Any] | None:
    if row.get("scored_at") is None or row.get("actual_micro") is None:
        return None
    payload = json.loads(row["payload"])
    actual = Decimal(row["actual_micro"]) / Decimal(1000000)
    point, lower, upper = (Decimal(payload[key]) for key in ("point_usd", "lower_usd", "upper_usd"))
    return {
        "clock": payload.get("clock", "calendar"),
        "simulation_id": payload.get("simulation_id"),
        "actual_usd": str(actual),
        "signed_error_usd": str(actual - point),
        "absolute_error_usd": str(abs(actual - point)),
        "covered": lower <= actual <= upper,
        "interval_width_usd": str(upper - lower),
    }

"""Energy-based carbon estimates. Money is never converted into electricity."""

from __future__ import annotations

from decimal import Decimal
from typing import Any


def gpu_carbon(device_hours: Decimal, source: dict[str, Any], pue: Decimal) -> dict[str, str]:
    watts = Decimal(source["device"]["nameplate_watts"])
    intensity = Decimal(source["grid"]["co2e_lb_per_mwh"]) * Decimal(source["kg_per_lb"]) / 1000
    if (
        any(not v.is_finite() for v in (device_hours, watts, intensity, pue))
        or device_hours < 0
        or watts <= 0
        or intensity < 0
        or pue < 1
    ):
        raise ValueError("Finite nonnegative energy inputs and PUE at least one required")
    energy = device_hours * watts / 1000 * pue
    return {
        "kwh_estimate": str(energy),
        "kg_co2e_estimate": str(energy * intensity),
        "grid_kg_co2e_per_kwh": str(intensity),
        "pue_assumption": str(pue),
        "status": "estimated GPU electricity only; total footprint unknown",
    }


def unknown_carbon(reason: str) -> dict[str, Any]:
    return {
        "kg_co2e_estimate": None,
        "kwh_estimate": None,
        "status": "not estimated",
        "reason": reason,
    }

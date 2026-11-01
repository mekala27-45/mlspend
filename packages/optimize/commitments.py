from __future__ import annotations

from collections.abc import Sequence
from statistics import mean

from packages.allocation.shapley import quantile


def expected_cost(usage: Sequence[float], level: float, on_demand: float, reserved: float) -> float:
    if not usage or min(usage) < 0 or level < 0 or not 0 < reserved < on_demand:
        raise ValueError("Invalid commitment inputs")
    return mean(level * reserved + max(0, value - level) * on_demand for value in usage)


def optimize(
    development: Sequence[float], heldout: Sequence[float], on_demand: float, reserved: float
) -> dict[str, object]:
    candidates = sorted({0.0, *development})
    level = min(candidates, key=lambda c: (expected_cost(development, c, on_demand, reserved), c))
    optimum = min(expected_cost(heldout, c, on_demand, reserved) for c in sorted({0.0, *heldout}))
    curve = [
        {"level": c, "expected_cost": expected_cost(development, c, on_demand, reserved)}
        for c in sorted({0.0, level, *[quantile(development, i / 20) for i in range(21)]})
    ]
    chosen = expected_cost(heldout, level, on_demand, reserved)
    lower, upper = level * 0.8, level * 1.2
    consumption = sum(heldout)
    covered = sum(min(level, value) for value in heldout)
    return {
        "level": level,
        "heldout_cost_per_hour": chosen,
        "regret_per_hour": chosen - optimum,
        "minus20_regret_per_hour": expected_cost(heldout, lower, on_demand, reserved) - optimum,
        "plus20_regret_per_hour": expected_cost(heldout, upper, on_demand, reserved) - optimum,
        "coverage": covered / consumption if consumption else None,
        "utilization": covered / (level * len(heldout)) if level else None,
        "interior": min(development) < level < max(development),
        "curve": curve,
    }

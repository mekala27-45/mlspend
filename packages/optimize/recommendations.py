from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Sequence
from typing import Any

from packages.allocation.shapley import quantile


def recommend(
    rows: Sequence[dict[str, Any]], headroom: float, rates: dict[str, float]
) -> list[dict[str, Any]]:
    if headroom < 1:
        raise ValueError("Headroom cannot be below current usage")
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[row["resource"]].append(row)
    output = []
    for resource, values in sorted(groups.items()):
        requested = quantile([float(r["requested"]) for r in values], 0.95)
        used = quantile([float(r["used"]) for r in values], 0.95)
        target = math.ceil(used * headroom * 4) / 4
        released = max(0, requested - target)
        if released:
            rate = rates[values[0]["pool"]]
            output.append(
                {
                    "resource": resource,
                    "kind": "rightsizing",
                    "requested_units_p95": requested,
                    "target_units": target,
                    "capacity_value_micro": round(released * rate * len(values)),
                    "cash_savings_micro": None,
                    "reason": "Released reservations only save cash when a node is removed. This capacity value is an upper bound, not a realized saving.",
                }
            )
    return output

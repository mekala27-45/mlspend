from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from statistics import median
from typing import Any


def score_series(rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """Compare each resource to earlier observations in its hour-of-week."""
    histories: dict[tuple[str, int], list[float]] = defaultdict(list)
    results = []
    for row in sorted(rows, key=lambda r: (r["timestamp"], r["resource"])):
        from datetime import datetime

        dt = datetime.fromisoformat(row["timestamp"])
        key = (row["resource"], dt.weekday() * 24 + dt.hour)
        history = histories[key][-8:]
        value = float(row["cost_micro"])
        if len(history) >= 4:
            center = median(history)
            scale = max(1, 1.4826 * median(abs(v - center) for v in history), center * 0.10)
            score = (value - center) / scale
            results.append(
                {
                    "timestamp": row["timestamp"],
                    "resource": row["resource"],
                    "team": row["team"],
                    "actual_micro": int(value),
                    "expected_micro": center,
                    "score": score,
                }
            )
        histories[key].append(value)
    return results


def choose_threshold(
    scores: Sequence[dict[str, Any]],
    development_end: str,
    candidates: Sequence[float],
    alert_budget: float,
) -> tuple[float, dict[str, float]]:
    development = [row for row in scores if row["timestamp"][:10] < development_end]
    if not development or not candidates or not 0 <= alert_budget < 1:
        raise ValueError("No development scores or invalid budget")
    rates = {
        str(t): sum(row["score"] >= t for row in development) / len(development)
        for t in sorted(candidates)
    }
    passing = [t for t in sorted(candidates) if rates[str(t)] <= alert_budget]
    return (passing[0] if passing else max(candidates)), rates

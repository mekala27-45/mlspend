"""New synthetic outcomes, imported only by the evaluation close stage."""

from __future__ import annotations

from decimal import ROUND_HALF_EVEN, Decimal
from random import Random
from typing import Any


def outcomes(history: list[dict[str, Any]], seed: int, teams: list[str]) -> dict[str, int]:
    random = Random(seed)
    common = random.randint(-500, 500)
    result = {}
    for team in sorted(teams):
        latest = max((r for r in history if r["team"] == team), key=lambda r: r["month"])
        amount = (
            Decimal(latest["cost_micro"]) * (10000 + common + random.randint(-1500, 2000)) / 10000
        )
        result["platform:" + team] = int(amount.quantize(Decimal(1), rounding=ROUND_HALF_EVEN))
    return result

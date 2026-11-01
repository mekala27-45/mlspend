from __future__ import annotations

import itertools
import math
from collections.abc import Callable, Sequence


def shapley(
    players: Sequence[str], coalition_cost: Callable[[frozenset[str]], float]
) -> dict[str, float]:
    names = sorted(set(players))
    if not names or len(names) > 10:
        raise ValueError("Exact Shapley needs between one and ten unique players")
    if abs(coalition_cost(frozenset())) > 1e-12:
        raise ValueError("Empty coalition must cost zero")
    count = len(names)
    costs: dict[frozenset[str], float] = {}
    for n in range(count + 1):
        for coalition in itertools.combinations(names, n):
            costs[frozenset(coalition)] = coalition_cost(frozenset(coalition))
    result = dict.fromkeys(names, 0.0)
    for player in names:
        others = [p for p in names if p != player]
        for size in range(count):
            weight = math.factorial(size) * math.factorial(count - size - 1) / math.factorial(count)
            for subset in itertools.combinations(others, size):
                key = frozenset(subset)
                result[player] += weight * (costs[key | {player}] - costs[key])
    return result


def quantile(values: Sequence[float], level: float) -> float:
    if not values or not 0 <= level <= 1:
        raise ValueError("Nonempty values and valid quantile required")
    ordered = sorted(values)
    position = (len(ordered) - 1) * level
    lower = math.floor(position)
    upper = math.ceil(position)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)

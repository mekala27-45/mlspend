from __future__ import annotations

import random
from collections.abc import Mapping, Sequence
from statistics import mean

from packages.allocation.shapley import quantile


def benjamini_hochberg(pvalues: Mapping[str, float]) -> dict[str, float]:
    if not pvalues or any(not 0 <= value <= 1 for value in pvalues.values()):
        raise ValueError("Nonempty valid p-values required")
    ordered = sorted(pvalues, key=lambda key: (pvalues[key], key))
    result = {}
    running = 1.0
    for index in range(len(ordered) - 1, -1, -1):
        key = ordered[index]
        running = min(running, pvalues[key] * len(ordered) / (index + 1))
        result[key] = running
    return result


def cluster_interval(
    clusters: Mapping[str, Sequence[float]], seed: int, repeats: int = 400
) -> tuple[float, float]:
    if not clusters or repeats < 20 or any(not values for values in clusters.values()):
        raise ValueError("Nonempty clusters and sufficient repeats required")
    rng = random.Random(seed)
    names = sorted(clusters)
    bootstrap = []
    for _ in range(repeats):
        drawn = [rng.choice(names) for _ in names]
        bootstrap.append(mean(value for key in drawn for value in clusters[key]))
    return quantile(bootstrap, 0.025), quantile(bootstrap, 0.975)


def sign_randomization(differences: Sequence[float]) -> float:
    import itertools

    if not differences or len(differences) > 18:
        raise ValueError("Exact paired test accepts one to eighteen cluster differences")
    observed = abs(mean(differences))
    values = [
        abs(mean(sign * value for sign, value in zip(signs, differences, strict=True)))
        for signs in itertools.product((-1, 1), repeat=len(differences))
    ]
    return sum(value >= observed - 1e-12 for value in values) / len(values)

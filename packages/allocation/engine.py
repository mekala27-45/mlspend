from __future__ import annotations

from collections.abc import Mapping

from packages.core.money import apportion


def allocate(
    direct: Mapping[str, int],
    overhead: int,
    usage: Mapping[str, float],
    reference: Mapping[str, float],
) -> dict[str, dict[str, int]]:
    if set(direct) != set(usage) or set(direct) != set(reference):
        raise ValueError("Allocation methods must use the same owners")
    if any(v < 0 for v in direct.values()):
        raise ValueError("Negative direct spend")
    weights = {
        "even": dict.fromkeys(direct, 1.0),
        "direct": {k: float(v) for k, v in direct.items()},
        "usage": dict(usage),
        "shapley": dict(reference),
    }
    result = {}
    for method, method_weights in weights.items():
        shares = apportion(overhead, method_weights)
        result[method] = {team: direct[team] + shares[team] for team in sorted(direct)}
        if sum(result[method].values()) != sum(direct.values()) + overhead:
            raise AssertionError("Allocation does not reconcile")
    return result


def infer_owner(resource: str, namespace: str, network: str, teams: set[str]) -> tuple[str, float]:
    """Two independent metadata fields are needed; the resource name alone is insufficient."""
    candidate = namespace if namespace in teams else ""
    if candidate and network == f"net-{candidate}":
        return candidate, 1.0
    return "unallocated", 0.0


def allocate_models(
    bills: Mapping[str, int], direct_by_owner: Mapping[str, Mapping[str, int]]
) -> dict[str, int]:
    """Split each owner's statement once, including costs with no inferred owner."""
    if set(bills) != set(direct_by_owner):
        raise ValueError("Model weights must cover every billed owner")
    result: dict[str, int] = {}
    for owner in sorted(bills):
        if bills[owner] == 0 and not direct_by_owner[owner]:
            continue
        shares = apportion(bills[owner], direct_by_owner[owner])
        for model, amount in shares.items():
            result[model] = result.get(model, 0) + amount
    if sum(result.values()) != sum(bills.values()):
        raise AssertionError("Model costs do not reconcile")
    return result

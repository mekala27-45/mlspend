import math


def unit_cost(
    cost_micro: int,
    requests: int,
    used_capacity: float,
    available_capacity: float,
    capacity_per_replica: float,
    replica_cost_micro: int,
    increment: int = 1000,
) -> dict[str, float | int | None]:
    if (
        min(cost_micro, requests, used_capacity, available_capacity, replica_cost_micro) < 0
        or capacity_per_replica <= 0
        or increment <= 0
    ):
        raise ValueError("Invalid unit cost inputs")
    if used_capacity > available_capacity:
        raise ValueError("Used capacity exceeds available capacity")
    replicas = math.ceil(
        max(0, used_capacity + increment - available_capacity) / capacity_per_replica
    )
    return {
        "average_micro_per_1000": cost_micro * 1000 / requests if requests else None,
        "marginal_micro_per_1000": replicas * replica_cost_micro,
        "extra_replicas": replicas,
    }

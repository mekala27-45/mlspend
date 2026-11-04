"""Integer GPU slices, deterministic packing and conserved allocation."""

from __future__ import annotations

import hashlib
import math
from collections.abc import Mapping
from typing import Any

from packages.allocation.shapley import shapley
from packages.core.money import apportion


def pack(requests: Mapping[str, int], denominator: int = 8) -> list[list[str]]:
    if denominator < 1 or any(
        type(v) is not int or not 0 < v <= denominator for v in requests.values()
    ):
        raise ValueError("Each job must request a positive integer number of slices up to one GPU")
    bins: list[list[str]] = []
    free: list[int] = []
    for job, amount in sorted(requests.items(), key=lambda row: (-row[1], row[0])):
        position = next((i for i, available in enumerate(free) if available >= amount), len(bins))
        if position == len(bins):
            bins.append([])
            free.append(denominator)
        bins[position].append(job)
        free[position] -= amount
    return bins


def allocate_pool(
    requests: Mapping[str, int], devices: int, rate_micro: int, denominator: int = 8
) -> dict[str, dict[str, int]]:
    if not requests:
        if devices:
            raise ValueError("Idle devices require an explicit owner")
        return {method: {} for method in ("even", "direct", "usage", "custom", "shapley")}
    if rate_micro < 0 or devices * denominator < sum(requests.values()):
        raise ValueError("Invalid price or insufficient physical capacity")
    names = sorted(requests)
    total = devices * rate_micro
    reference = shapley(
        names, lambda coalition: float(math.ceil(sum(requests[n] for n in coalition) / denominator))
    )
    weights = {
        "even": dict.fromkeys(names, 1.0),
        "direct": dict.fromkeys(names, float(rate_micro)),
        "usage": {n: float(requests[n]) for n in names},
        "custom": {n: float(i + 1) for i, n in enumerate(names)},
        "shapley": reference,
    }
    return {method: apportion(total, values) for method, values in weights.items()}


def run_study(plan: dict[str, Any], rate_micro: int) -> dict[str, Any]:
    rows = []
    totals: dict[str, dict[str, dict[str, int]]] = {}
    for hour in range(plan["hours"]):
        requests = {
            team: 1
            + int.from_bytes(
                hashlib.sha256(f"{plan['seed']}:{hour}:{team}".encode()).digest()[:2], "big"
            )
            % plan["fraction_denominator"]
            for team in plan["teams"]
        }
        bins = pack(requests, plan["fraction_denominator"])
        for scenario, devices in (("dedicated", len(requests)), ("shared", len(bins))):
            allocation = allocate_pool(requests, devices, rate_micro, plan["fraction_denominator"])
            scenario_totals = totals.setdefault(
                scenario, {method: dict.fromkeys(plan["teams"], 0) for method in allocation}
            )
            for method, bills in allocation.items():
                if sum(bills.values()) != devices * rate_micro:
                    raise AssertionError("Allocation lost money")
                for team, amount in bills.items():
                    scenario_totals[method][team] += amount
            rows.append(
                {
                    "hour": hour,
                    "scenario": scenario,
                    "devices": devices,
                    "requested_slices": sum(requests.values()),
                    "idle_slices": devices * plan["fraction_denominator"] - sum(requests.values()),
                    "cost_micro": devices * rate_micro,
                    "allocations": allocation,
                }
            )
        assigned = [job for group in bins for job in group]
        if sorted(assigned) != sorted(requests) or any(
            sum(requests[j] for j in group) > plan["fraction_denominator"] for group in bins
        ):
            raise AssertionError("Invalid GPU placement")
    return {
        "mode": "registered synthetic experiment",
        "hours": plan["hours"],
        "rows": rows,
        "allocations": totals,
        "totals": {
            s: sum(r["cost_micro"] for r in rows if r["scenario"] == s)
            for s in ("dedicated", "shared")
        },
        "assumptions": plan["assumptions"],
        "shapley_basis": "Exact coalition values of the fungible-slice capacity lower bound; used as weights for the actual packed bill. Packing efficiency is not asserted optimal.",
        "direct_basis": "Each job's dedicated one-device reference cost; equal here because the hardware and duration are identical.",
        "custom_basis": "Predeclared sorted team weights from one through six.",
    }

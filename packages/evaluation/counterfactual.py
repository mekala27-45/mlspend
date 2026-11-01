"""Evaluation alone reruns the simulator and reads its sealed outcomes."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

from packages.core.io import ROOT, digest, read_json, write_json
from packages.prices.book import PriceBook
from packages.simulator.expanded import ACTIONS, simulate


def summarize(
    book: PriceBook,
    actions: frozenset[str],
    hours: int | None = None,
    incidents: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    monthly: dict[str, int] = defaultdict(int)
    resources: dict[str, int] = defaultdict(int)
    hourly: dict[str, int] = defaultdict(int)
    for row in simulate(book, actions, hours, incidents):
        monthly[row["timestamp"][:7]] += row["cost_micro"]
        resources[row["resource"]] += row["cost_micro"]
        hourly[row["timestamp"]] += row["cost_micro"]
    return {
        "monthly_micro": dict(monthly),
        "resource_micro": dict(resources),
        "hourly_micro": dict(hourly),
        "total_micro": sum(monthly.values()),
    }


def rerun(destination: Path, hours: int | None = None) -> dict[str, Any]:
    book = PriceBook(ROOT / "data/prices/expanded")
    baseline = summarize(book, frozenset(), hours)
    actions = {action: summarize(book, frozenset([action]), hours) for action in ACTIONS}
    combined = summarize(book, frozenset(ACTIONS), hours)
    incidents = read_json(ROOT / "config/expanded-incidents.json")
    incident_costs = {}
    incident_hourly = {}
    for incident in incidents:
        without = summarize(
            book, frozenset(), hours, [r for r in incidents if r["id"] != incident["id"]]
        )
        incident_costs[incident["id"]] = baseline["total_micro"] - without["total_micro"]
        incident_hourly[incident["id"]] = {
            hour: value - without["hourly_micro"].get(hour, 0)
            for hour, value in baseline["hourly_micro"].items()
            if value != without["hourly_micro"].get(hour, 0)
        }
    oracle = summarize(
        book, frozenset(ACTIONS), hours, [r for r in incidents if r["kind"] == "sku_change"]
    )
    result = {
        "baseline": baseline,
        "actions": actions,
        "combined": combined,
        "incident_avoidable_micro": incident_costs,
        "incident_hourly_micro": incident_hourly,
        "oracle_total_micro": oracle["total_micro"],
        "price_digest": book.digest,
        "procedure": "Full deterministic simulation rerun for each action and incident removal; exogenous random draws keyed by seed, hour, owner and purpose",
        "hours": hours or 8760,
    }
    write_json(destination / "sealed/counterfactuals.json", result)
    return result


def grade(recommendations: list[dict[str, Any]], truth: dict[str, Any]) -> dict[str, Any]:
    graded = []
    totals: dict[str, float] = defaultdict(float)
    for row in recommendations:
        key = row["resource"]
        actual = truth["baseline"]["resource_micro"].get(key, 0) - truth["actions"][row["action"]][
            "resource_micro"
        ].get(key, 0)
        totals[row["action"]] += row["estimated_annual_micro"]
        graded.append(
            {
                **row,
                "true_resource_annual_micro": actual,
                "resource_error_micro": row["estimated_annual_micro"] - actual,
                "monthly_interval_covers_resource_saving": row["monthly_lower_micro"]
                <= actual / 12
                <= row["monthly_upper_micro"],
            }
        )
    action_rows = []
    for action, scenario in truth["actions"].items():
        actual = truth["baseline"]["total_micro"] - scenario["total_micro"]
        action_rows.append(
            {
                "action": action,
                "estimated_annual_micro": totals[action],
                "true_platform_annual_micro": actual,
                "error_micro": totals[action] - actual,
                "capacity_externality_micro": actual
                - sum(r["true_resource_annual_micro"] for r in graded if r["action"] == action),
            }
        )
    recovered = truth["baseline"]["total_micro"] - truth["combined"]["total_micro"]
    incident_waste = sum(max(0, value) for value in truth["incident_avoidable_micro"].values())
    avoidable = max(0, truth["baseline"]["total_micro"] - truth["oracle_total_micro"])
    return {
        "rows": graded,
        "actions": action_rows,
        "joint_recovered_micro": recovered,
        "incident_avoidable_micro": incident_waste,
        "recovery_share_of_baseline": recovered / truth["baseline"]["total_micro"],
        "total_avoidable_micro": avoidable,
        "share_of_total_waste_recovered": recovered / avoidable if avoidable else None,
        "truth_digest": digest(truth),
        "overlap_note": "Joint saving comes from one combined rerun. Incident-removal effects and standalone action savings are not additive; no summed savings claim.",
    }

from __future__ import annotations

import math
from collections import defaultdict
from typing import Any

from packages.allocation.engine import allocate, allocate_models, infer_owner
from packages.allocation.shapley import quantile, shapley
from packages.core.io import ROOT, STATEMENT, digest, read_json, write_json
from packages.detect.detector import choose_threshold, score_series
from packages.evaluation.score import score_incidents, score_owners
from packages.forecast.models import backtest
from packages.optimize.commitments import optimize
from packages.optimize.recommendations import recommend
from packages.prices.book import PriceBook
from packages.simulator.generate import generate
from packages.unit.economics import unit_cost
from packages.warehouse.build import build, load_lines


def run() -> dict[str, Any]:
    destination = ROOT / "data/generated"
    plan = read_json(ROOT / "evaluation/plan.json")
    if digest(plan) != read_json(ROOT / "evaluation/registration.json")["plan_digest"]:
        raise ValueError("Registered plan drift; refusing held-out evaluation")
    config = read_json(ROOT / "config/simulator.json")
    generation = generate(destination)
    reconciliation = build(destination, destination / "warehouse.duckdb")
    charges = load_lines(destination / "charges.jsonl.gz")
    telemetry = load_lines(destination / "telemetry.jsonl.gz")
    book = PriceBook()
    teams = sorted(config["teams"])
    predictions = {}
    tagged_before = sum(row["cost_micro"] for row in telemetry if row["team"] != "unallocated")
    for row in telemetry:
        if row["team"] == "unallocated":
            inferred, _ = infer_owner(row["resource"], row["namespace"], row["network"], set(teams))
            predictions[row["resource"]] = inferred
            row["team"] = inferred
    tagged_after = sum(row["cost_micro"] for row in telemetry if row["team"] != "unallocated")
    direct_total = sum(row["cost_micro"] for row in telemetry)
    by_month: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in telemetry:
        by_month[row["timestamp"][:7]].append(row)
    charge_months: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in charges:
        charge_months[row["ChargePeriodStart"][:7]].append(row)
    allocations = []
    units = []
    idle_rows = []
    daily: dict[tuple[str, str], int] = defaultdict(int)
    for row in telemetry:
        daily[(row["timestamp"][:10], row["team"])] += row["cost_micro"]
    for month, values in sorted(by_month.items()):
        direct = {team: sum(r["cost_micro"] for r in values if r["team"] == team) for team in teams}
        unallocated = sum(r["cost_micro"] for r in values if r["team"] == "unallocated")
        overhead = sum(
            r["EffectiveCostMicro"] for r in charge_months[month] if r["x_CostKind"] != "workload"
        )
        usage = {
            team: sum(max(r["requested"], r["used"]) for r in values if r["team"] == team)
            for team in teams
        }
        hourly: dict[tuple[str, str, str], float] = defaultdict(float)
        for row in values:
            hourly[(row["timestamp"], row["pool"], row["team"])] += max(
                row["requested"], row["used"]
            )
        hours = sorted({r["timestamp"] for r in values})
        rates = {pool: float(book.get(p["price_id"]).usd) for pool, p in config["pools"].items()}

        def coalition_cost(
            coalition: frozenset[str],
            hourly: dict[tuple[str, str, str], float] = hourly,
            hours: list[str] = hours,
            rates: dict[str, float] = rates,
        ) -> float:
            if not coalition:
                return 0.0
            return sum(
                math.ceil(
                    quantile(
                        [
                            sum(hourly[(hour, pool, team)] for team in sorted(coalition))
                            for hour in hours
                        ],
                        0.95,
                    )
                )
                * rate
                * len(hours)
                for pool, rate in rates.items()
            )

        reference = shapley(teams, coalition_cost)
        bills = allocate(direct, overhead, usage, reference)
        assert all(
            sum(method.values()) + unallocated
            == sum(r["EffectiveCostMicro"] for r in charge_months[month])
            for method in bills.values()
        )
        for team in teams:
            allocations.append(
                {
                    "month": month,
                    "team": team,
                    "direct_micro": direct[team],
                    "methods": {method: costs[team] for method, costs in bills.items()},
                    "shapley_coalition_value_usd": reference[team],
                    "method_of_record": plan["allocation_method"],
                }
            )
        allocations.append(
            {
                "month": month,
                "team": "unallocated",
                "direct_micro": unallocated,
                "methods": dict.fromkeys(bills, unallocated),
                "shapley_coalition_value_usd": None,
                "method_of_record": plan["allocation_method"],
            }
        )
        for pool in config["pools"]:
            pool_rows = [
                r
                for r in charge_months[month]
                if r["x_Pool"] == pool and r["x_CostKind"] != "shared"
            ]
            idle = sum(r["EffectiveCostMicro"] for r in pool_rows if r["x_CostKind"] == "idle")
            total = sum(r["EffectiveCostMicro"] for r in pool_rows)
            idle_rows.append(
                {
                    "month": month,
                    "pool": pool,
                    "idle_micro": idle,
                    "asset_micro": total,
                    "idle_share": idle / total if total else None,
                }
            )
        model_weights: dict[str, dict[str, int]] = {owner: {} for owner in [*teams, "unallocated"]}
        for row in values:
            weights = model_weights[row["team"]]
            weights[row["model"]] = weights.get(row["model"], 0) + row["cost_micro"]
        model_costs = allocate_models({**bills["usage"], "unallocated": unallocated}, model_weights)
        for model in sorted({r["model"] for r in values if r["kind"] == "inference"}):
            model_rows = [r for r in values if r["model"] == model]
            loaded = model_costs[model]
            last = max(model_rows, key=lambda r: r["timestamp"])
            requests = sum(r["requests"] for r in model_rows)
            capacity = max(last["requested"], last["used"]) * 16000
            result = unit_cost(
                loaded,
                requests,
                min(last["requests"], capacity),
                capacity,
                16000,
                round(rates[last["pool"]] * 1000000),
            )
            units.append(
                {
                    "month": month,
                    "model": model,
                    "requests": requests,
                    "loaded_micro": loaded,
                    "marginal_window": "next hour at final observed utilization",
                    **result,
                }
            )
    dates = sorted({day for day, _ in daily})
    development_days = sum(day < plan["development_end_exclusive"] for day in dates)
    forecasts = []
    for team in teams:
        values = [float(daily[(day, team)]) for day in dates]
        forecast = backtest(
            values, development_days, plan["forecast_candidates"], plan["forecast_interval"]
        )
        for row in forecast["rows"]:
            row["day"] = dates[row["index"]]
        forecasts.append({"team": team, **forecast})
    scores = score_series(telemetry)
    threshold, selection = choose_threshold(
        scores,
        plan["development_end_exclusive"],
        plan["detector_candidates"],
        plan["false_alarm_budget"],
    )
    alerts = [
        r
        for r in scores
        if r["score"] >= threshold and r["timestamp"][:10] >= plan["heldout_start"]
    ]
    detector = score_incidents(destination / "sealed/truth.json", alerts, plan["heldout_start"])
    detector.update(threshold=threshold, development_alert_fractions=selection, alerts=alerts)
    commitments = []
    for pool, p in sorted(config["pools"].items()):
        hours_usage: dict[str, float] = defaultdict(float)
        for row in telemetry:
            if row["pool"] == pool:
                hours_usage[row["timestamp"]] += max(row["requested"], row["used"])
        development = [
            value
            for hour, value in sorted(hours_usage.items())
            if hour[:10] < plan["heldout_start"]
        ]
        heldout = [
            value
            for hour, value in sorted(hours_usage.items())
            if hour[:10] >= plan["heldout_start"]
        ]
        rate = float(book.get(p["price_id"]).usd)
        commitments.append(
            {
                "pool": pool,
                "price_id": p["price_id"],
                "discount_basis": "simulated contract discount, not a provider offer",
                **optimize(development, heldout, rate, rate * (1 - plan["commitment_discount"])),
            }
        )
    rates_micro = {
        pool: float(book.get(p["price_id"]).usd) * 1000000 for pool, p in config["pools"].items()
    }
    heldout_rows = [r for r in telemetry if r["timestamp"][:10] >= plan["heldout_start"]]
    recommendations = recommend(heldout_rows, plan["rightsizing_headroom"], rates_micro)
    monthly = [
        {
            "month": month,
            "billed_micro": sum(r["BilledCostMicro"] for r in values),
            "effective_micro": sum(r["EffectiveCostMicro"] for r in values),
        }
        for month, values in sorted(charge_months.items())
    ]
    latest = monthly[-1]["month"]
    moves = [
        {
            "team": r["team"],
            "month": r["month"],
            "range_micro": max(r["methods"].values()) - min(r["methods"].values()),
        }
        for r in allocations
    ]
    portfolio = {
        "status": "not measured",
        "rows": [],
        "reason": "Actions fetch has not run; absence is not zero usage",
    }
    portfolio_path = ROOT / "results/portfolio-usage.json"
    if portfolio_path.exists():
        report = read_json(portfolio_path)
        lock = read_json(ROOT / "data/portfolio/lock.json")
        if digest(report) != lock["report_digest"]:
            raise ValueError("Portfolio evidence changed after promotion")
        portfolio = {key: value for key, value in report.items() if key not in ("jobs", "visited")}
        portfolio["evidence"] = lock
    manifest = {
        "version": "0.1.0-dev",
        "statement": STATEMENT,
        "status": "deployed working demonstration; mandatory analytical requirements remain",
        "generation": generation,
        "price_digest": book.digest,
        "plan_digest": digest(plan),
        "latest_month": latest,
        "monthly": monthly,
        "allocation": allocations,
        "allocation_note": "Three direct-plus-overhead methods and Shapley-weighted overhead. The exact coalition values are shown separately; the fourth column is not a Shapley allocation of the entire invoice.",
        "largest_method_move": max(moves, key=lambda r: r["range_micro"]),
        "idle": idle_rows,
        "tag_coverage": {
            "before": tagged_before / direct_total,
            "after": tagged_after / direct_total,
            **score_owners(destination / "sealed/truth.json", predictions),
        },
        "unit_costs": units,
        "forecasts": forecasts,
        "detector": detector,
        "recommendations": recommendations,
        "commitments": commitments,
        "reconciliation": reconciliation,
        "portfolio": portfolio,
        "prices": [row.model_dump(mode="json") for row in book.rows],
        "daily": [
            {"day": day, "team": team, "cost_micro": cost}
            for (day, team), cost in sorted(daily.items())
        ],
    }
    write_json(ROOT / "results/manifest.json", manifest)
    write_json(ROOT / "results/reconcile.json", reconciliation)
    write_json(
        ROOT / "results/provenance.json",
        {"generation": generation, "manifest_digest": digest(manifest), "statement": STATEMENT},
    )
    from packages.render.documents import render

    render(manifest)
    return {
        "charge_rows": generation["charge_rows"],
        "manifest_digest": digest(manifest),
        "latest_month": latest,
    }


if __name__ == "__main__":
    print(run())

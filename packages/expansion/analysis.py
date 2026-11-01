from __future__ import annotations

import math
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any

import duckdb

from packages.allocation.shapley import quantile, shapley
from packages.core.money import apportion
from packages.forecast.expanded import budgets, daily, monthly
from packages.optimize.expanded import commitment
from packages.prices.book import PriceBook


def owner_sql(teams: list[str]) -> str:
    names = ",".join("'" + team + "'" for team in teams)
    return f"CASE WHEN team='unallocated' AND namespace IN ({names}) AND network='net-' || namespace THEN namespace ELSE team END"


def analyze(
    directory: Path, book: PriceBook, plan: dict[str, Any], forecasts: bool = True
) -> dict[str, Any]:
    teams = plan["teams"]
    with duckdb.connect(str(directory / "warehouse.duckdb")) as connection:
        connection.execute("SET TimeZone='UTC'")
        contract_count = connection.execute(
            "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='marts' AND table_name='stg_observed'"
        ).fetchone()
        assert contract_count is not None
        contracted = bool(contract_count[0])
        connection.execute(
            "CREATE OR REPLACE VIEW owned AS SELECT *, "
            + owner_sql(teams)
            + " AS owner FROM "
            + ("marts.stg_observed" if contracted else "priced")
        )
        connection.execute(
            "CREATE OR REPLACE VIEW daily_cost AS SELECT CAST(timestamp AS DATE) AS day, owner, service, SUM(cost_micro)::BIGINT AS cost_micro, SUM(requests)::BIGINT AS requests FROM owned GROUP BY 1,2,3"
        )
        months = [
            r[0]
            for r in connection.execute(
                "SELECT DISTINCT strftime(timestamp, '%Y-%m') FROM owned ORDER BY 1"
            ).fetchall()
        ]
        allocations: list[dict[str, Any]] = []
        units: list[dict[str, Any]] = []
        idle: list[dict[str, Any]] = []
        commitments: list[dict[str, Any]] = []
        for month in months:
            direct = {team: 0 for team in [*teams, "unallocated"]}
            usage = dict.fromkeys(teams, 0.0)
            overhead = 0
            records = connection.execute(
                "SELECT owner, kind, SUM(cost_micro), SUM(greatest(requested,used)) FROM owned WHERE strftime(timestamp,'%Y-%m')=? GROUP BY 1,2",
                [month],
            ).fetchall()
            for owner, _kind, amount, used in records:
                if owner == "shared":
                    overhead += int(amount)
                else:
                    direct[owner] += int(amount)
                    if owner in usage:
                        usage[owner] += float(used)
            hourly: dict[tuple[str, str, str], float] = defaultdict(float)
            rows = connection.execute(
                "SELECT timestamp, pool, owner, SUM(greatest(requested,used)) FROM owned WHERE strftime(timestamp,'%Y-%m')=? AND pool IN ('azure-t4','azure-a100','azure-v100') AND kind='workload' AND NOT ends_with(price_id,'-spot') GROUP BY 1,2,3",
                [month],
            ).fetchall()
            hours = sorted({str(r[0]) for r in rows})
            for timestamp, pool, owner, value in rows:
                hourly[(str(timestamp), pool, owner)] = float(value)
            rates = {
                pool: float(book.get(pool).usd) for pool in ("azure-t4", "azure-a100", "azure-v100")
            }

            def coalition(
                coalition_teams: frozenset[str],
                hourly: dict[tuple[str, str, str], float] = hourly,
                hours: list[str] = hours,
                rates: dict[str, float] = rates,
            ) -> float:
                if not coalition_teams:
                    return 0
                return sum(
                    math.ceil(
                        quantile(
                            [
                                sum(hourly[(hour, pool, team)] for team in sorted(coalition_teams))
                                for hour in hours
                            ],
                            plan["shapley_capacity_percentile"],
                        )
                    )
                    * len(hours)
                    * rate
                    for pool, rate in rates.items()
                )

            reference = shapley(teams, coalition)
            weights = {
                "even": dict.fromkeys(teams, 1.0),
                "direct": {team: float(direct[team]) for team in teams},
                "usage": usage,
                "custom": plan["custom_weights"],
                "shapley": reference,
            }
            bills = {
                method: {
                    team: direct[team] + share
                    for team, share in apportion(overhead, method_weights).items()
                }
                for method, method_weights in weights.items()
            }
            expected = overhead + sum(direct.values())
            for method in bills:
                assert sum(bills[method].values()) + direct["unallocated"] == expected
            for team in [*teams, "unallocated"]:
                allocations.append(
                    {
                        "month": month,
                        "team": team,
                        "direct_micro": direct[team],
                        "usage_weight": usage.get(team, 0),
                        "custom_weight": plan["custom_weights"].get(team, 0),
                        "methods": {
                            method: values.get(team, direct["unallocated"])
                            for method, values in bills.items()
                        },
                        "capacity_shapley_usd": reference.get(team),
                        "method_of_record": "usage",
                    }
                )
                model_rows = connection.execute(
                    "SELECT model, service, SUM(cost_micro), SUM(requests), SUM(coalesce(completed_runs,0)), SUM(coalesce(failed_runs,0)) FROM owned WHERE strftime(timestamp,'%Y-%m')=? AND owner=? GROUP BY 1,2",
                    [month, team],
                ).fetchall()
                by_model = {
                    model: int(amount)
                    for model, service, amount, requests, runs, failed in model_rows
                    if service in {"inference", "llm", "training", "notebook"}
                }
                if not by_model:
                    continue
                statement = bills["usage"].get(team, direct["unallocated"])
                loaded = apportion(statement, by_model)
                for model, service, amount, requests, runs, failed in model_rows:
                    if model not in loaded:
                        continue
                    denominator = int(runs) if service == "training" else int(requests)
                    last = connection.execute(
                        "SELECT requested, used, price_id FROM owned WHERE model=? AND owner=? AND strftime(timestamp,'%Y-%m')=? ORDER BY timestamp DESC LIMIT 1",
                        [model, team, month],
                    ).fetchone()
                    assert last is not None
                    marginal = None
                    if service == "inference":
                        additional = max(
                            0, math.ceil(float(last[1]) + 1000 / 18000) - math.ceil(float(last[0]))
                        )
                        marginal = additional * float(book.get(last[2]).usd) * 1000000
                    components = {
                        kind: int(total)
                        for kind, total in connection.execute(
                            "SELECT token_kind,SUM(cost_micro) FROM owned WHERE model=? AND owner=? AND strftime(timestamp,'%Y-%m')=? AND service='llm' GROUP BY 1",
                            [model, team, month],
                        ).fetchall()
                    }
                    if components:
                        components["allocated_support"] = loaded[model] - sum(components.values())
                    units.append(
                        {
                            "month": month,
                            "team": team,
                            "model": model,
                            "service": service,
                            "direct_micro": int(amount),
                            "fully_loaded_micro": loaded[model],
                            "outputs": denominator,
                            "cost_micro_per_output": loaded[model] / denominator
                            if denominator
                            else None,
                            "micro_per_1000_predictions": loaded[model] * 1000 / denominator
                            if denominator and service == "inference"
                            else None,
                            "marginal_micro_next_1000": marginal,
                            "failed_runs": int(failed),
                            "components_micro": components,
                        }
                    )
            idle.extend(
                {
                    "month": month,
                    "pool": pool,
                    "idle_micro": int(amount),
                    "asset_micro": int(asset),
                    "idle_share": int(amount) / int(asset) if asset else 0,
                }
                for pool, amount, asset in connection.execute(
                    "SELECT pool,COALESCE(SUM(cost_micro) FILTER(WHERE kind='idle'),0),SUM(cost_micro) FROM owned WHERE strftime(timestamp,'%Y-%m')=? AND pool IS NOT NULL GROUP BY 1",
                    [month],
                ).fetchall()
            )

        start = date.fromisoformat(plan["start"])
        dev_days = (date.fromisoformat(plan["development_end_exclusive"]) - start).days
        forecast_rows, budget_rows = [], []
        if forecasts:
            groups = [("team", team) for team in teams] + [
                ("service", r[0])
                for r in connection.execute(
                    "SELECT DISTINCT service FROM owned ORDER BY 1"
                ).fetchall()
            ]
            for kind, key in groups:
                column = "owner" if kind == "team" else "service"
                values = connection.execute(
                    f"SELECT day,SUM(cost_micro)/1000000.0,SUM(requests) FROM daily_cost WHERE {column}=? GROUP BY 1 ORDER BY 1",
                    [key],
                ).fetchall()
                if len(values) <= dev_days:
                    continue
                costs, workload = [float(r[1]) for r in values], [float(r[2]) for r in values]
                result = daily(costs, workload, start, dev_days, plan["forecast"])
                month_rows = monthly(
                    costs, workload, start, dev_days, result["method"], plan["forecast"]
                )
                result.pop("predictions")
                forecast_rows.append({"grain": kind, "key": key, **result, "monthly": month_rows})
                budget_rows.append(
                    {"grain": kind, "key": key, **budgets(costs, start, dev_days, plan["budgets"])}
                )
        for pool in ("azure-t4", "azure-a100", "azure-v100"):
            values = connection.execute(
                "SELECT timestamp,SUM(greatest(requested,used)) FROM owned WHERE pool=? AND kind='workload' AND NOT ends_with(price_id,'-spot') GROUP BY 1 ORDER BY 1",
                [pool],
            ).fetchall()
            if len(values) <= dev_days * 24:
                continue
            offer = (
                pool + "-reserved-1y"
                if any(p.id == pool + "-reserved-1y" for p in book.rows)
                else pool + "-savings-1y"
            )
            commitments.append(
                {
                    "pool": pool,
                    "offer_id": offer,
                    **commitment(
                        [float(r[1]) for r in values],
                        dev_days * 24,
                        plan["commitment"]["candidate_capacity"],
                        float(book.get(offer).usd),
                        float(book.get(pool).usd),
                    ),
                }
            )
        coverage = connection.execute(
            "SELECT SUM(cost_micro) FILTER(WHERE team<>'unallocated'), SUM(cost_micro) FILTER(WHERE owner<>'unallocated'), SUM(cost_micro) FROM owned WHERE kind='workload'"
        ).fetchone()
        assert coverage is not None
        experiments = [
            {
                "experiment_id": key,
                "cost_micro": int(cost),
                "completed_runs": int(completed),
                "failed_runs": int(failed),
            }
            for key, cost, completed, failed in connection.execute(
                "SELECT experiment_id,SUM(cost_micro),SUM(completed_runs),SUM(failed_runs) FROM owned WHERE service='training' GROUP BY 1 ORDER BY 1"
            ).fetchall()
        ]
    return {
        "largest_method_move": max(
            (
                {
                    "team": row["team"],
                    "month": row["month"],
                    "range_micro": max(row["methods"].values()) - min(row["methods"].values()),
                }
                for row in allocations
            ),
            key=lambda row: row["range_micro"],
        ),
        "allocation": allocations,
        "units": units,
        "idle": idle,
        "forecasts": forecast_rows,
        "budgets": budget_rows,
        "commitments": commitments,
        "experiments": experiments,
        "tag_coverage": {"before": coverage[0] / coverage[2], "after": coverage[1] / coverage[2]},
        "unit_policy": "Direct prediction, answer, training and notebook models receive each owner statement in proportion to direct cost. Shared support is allocated once; no denominator is invented for idle notebooks. Marginal inference uses simulated throughput of 18000 requests per node-hour.",
    }

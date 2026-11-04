"""Derive optional results and public claims without touching baseline results."""

from __future__ import annotations

import argparse
import json
from decimal import Decimal
from pathlib import Path
from typing import Any

from packages.core.io import ROOT, STATEMENT, canonical, digest, read_json, write_json
from packages.core.money import microdollars
from packages.prices.book import PriceBook
from packages.stretch.carbon import gpu_carbon, unknown_carbon
from packages.stretch.catalog import export_tables
from packages.stretch.sharing import run_study


def derive(root: Path) -> dict[str, Any]:
    plan = read_json(root / "evaluation/stretch/plan.json")
    registration = read_json(root / "evaluation/stretch/registration.json")
    if digest(plan) != registration["plan_digest"]:
        raise ValueError("Stretch registration drift")
    book = PriceBook(root / "data/prices/expanded")
    source = read_json(root / "data/carbon/source.json")
    sharing = run_study(
        plan["gpu_sharing"], microdollars(book.get(plan["gpu_sharing"]["price_id"]).usd)
    )
    for row in sharing["rows"]:
        row["carbon"] = gpu_carbon(Decimal(row["devices"]), source, Decimal(plan["carbon"]["pue"]))
    carbon = {}
    for scenario in ("dedicated", "shared"):
        hours = sum(r["devices"] for r in sharing["rows"] if r["scenario"] == scenario)
        carbon[scenario] = {
            **gpu_carbon(Decimal(hours), source, Decimal(plan["carbon"]["pue"])),
            "device_hours": hours,
            "sensitivity": [
                gpu_carbon(Decimal(hours), source, Decimal(pue))
                for pue in plan["carbon"]["pue_sensitivity"]
            ],
        }
    return {
        "plan_digest": registration["plan_digest"],
        "price_digest": book.digest,
        "carbon_source_digest": digest(source),
        "sharing": sharing,
        "carbon": carbon,
        "price_history": {"status": "pending future observation", **plan["price_observation"]},
        "baseline_carbon": unknown_carbon(
            "The released baseline does not include measured energy or verified complete device power models"
        ),
        "statement": STATEMENT,
    }


def web_data(result: dict[str, Any]) -> dict[str, Any]:
    sharing = result["sharing"]
    summary = [
        [
            s,
            result["carbon"][s]["device_hours"],
            f"${sharing['totals'][s] / 1e6:,.2f}",
            f"{Decimal(result['carbon'][s]['kg_co2e_estimate']):.3f}",
        ]
        for s in ("dedicated", "shared")
    ]
    allocations = [
        [
            scenario,
            method,
            team,
            f"${amount / 1e6:,.2f}",
            f"{Decimal(result['carbon'][scenario]['kg_co2e_estimate']) * amount / sharing['totals'][scenario]:.3f}",
        ]
        for scenario, methods in sharing["allocations"].items()
        for method, teams in methods.items()
        for team, amount in teams.items()
    ]
    return {
        "source_digest": digest(result),
        "pages": {
            "extensions": {
                "title": "Share capacity. Keep the accounts exact.",
                "intro": "A separately registered experiment compares dedicated and fractional GPU placement for the same hourly jobs. Carbon estimates cover modeled GPU electricity only.",
                "limit": "Sharing assumes no interference or quality loss and capacity that can shrink each hour. GPU nameplate power and PUE are assumptions. The regional grid factor is a proxy; the total footprint is unknown. No production savings are claimed.",
                "sections": [
                    {
                        "title": "The same jobs, two placements",
                        "headers": ["Scenario", "Device-hours", "Cost", "GPU kg CO2e estimate"],
                        "rows": summary,
                        "note": "One week of synthetic work at the locked T4 rate; PUE 1.2 and EPA eGRID2023 SRVC intensity.",
                    },
                    {
                        "title": "Every allocation policy conserves the bill",
                        "headers": ["Scenario", "Policy", "Team", "Cost", "GPU kg CO2e estimate"],
                        "rows": allocations,
                        "note": "Carbon follows the same allocation share on identical hardware. Direct weights are equal dedicated-job costs. Custom team weights are predeclared. Shapley uses the ideal fungible-slice capacity reference.",
                    },
                ],
            },
            "price-history": {
                "title": "Hold usage still. Observe the price change.",
                "intro": "A price change comparison needs two independent observations. The same portfolio quantities will be priced against both locked snapshots.",
                "limit": "There is no month-later observation yet. Missing rates, stale sources and changed units remain unpriced. Candidate prices are reviewed before promotion; the released price book remains fixed.",
                "sections": [
                    {
                        "title": "Observation calendar",
                        "headers": ["Observation", "Date", "Status"],
                        "rows": [
                            ["Baseline", result["price_history"]["baseline_date"], "Locked"],
                            [
                                "Second fetch",
                                result["price_history"]["not_before"],
                                "Pending future observation",
                            ],
                        ],
                        "note": "The collector refuses to treat an early snapshot as the required comparison.",
                    }
                ],
            },
        },
        "statement": STATEMENT,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = derive(ROOT)
    generated = {"results/stretch/manifest.json": result, "web/stretch.json": web_data(result)}
    for name, content in generated.items():
        path = ROOT / name
        if args.check:
            if not path.exists() or path.read_bytes() != canonical(content):
                raise ValueError("Stretch claim drift: " + name)
        else:
            write_json(path, content)
    if not args.check:
        export_tables(ROOT, read_json(ROOT / "results/expanded/manifest.json"), result)
    print(
        json.dumps(
            {
                "status": "pass",
                "digest": digest(result),
                "scenario_cost_micro": result["sharing"]["totals"],
                "price_observation": result["price_history"]["status"],
            }
        )
    )


if __name__ == "__main__":
    main()

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
from scripts.compare_price_history import comparison_for


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
    history = {"status": "pending future observation", **plan["price_observation"]}
    comparison_path = root / "results/stretch/price-comparison.json"
    if comparison_path.exists():
        saved = read_json(comparison_path)
        verified = comparison_for(root, root / saved["after_book"])
        if saved != verified:
            raise ValueError("Price comparison differs from locked prices or frozen usage")
        history.update(verified)
    return {
        "plan_digest": registration["plan_digest"],
        "price_digest": book.digest,
        "carbon_source_digest": digest(source),
        "sharing": sharing,
        "carbon": carbon,
        "price_history": history,
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
    output = {
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
    history = result["price_history"]
    if history["status"] == "observed comparison":
        page = output["pages"]["price-history"]
        portfolio = history["portfolio"]
        page["limit"] = (
            portfolio["scope"] + " These are list-price counterfactuals, not paid invoice changes."
        )
        page["sections"] = [
            {
                "title": "The same portfolio quantities at two prices",
                "headers": ["Scope", "Before cost", "After cost", "Change"],
                "rows": [
                    [
                        f"{portfolio['matched_rows']} matched rows; {portfolio['unpriced_rows']} unpriced",
                        f"${Decimal(portfolio['before_subtotal_micro']) / 1000000:,.2f}",
                        f"${Decimal(portfolio['after_subtotal_micro']) / 1000000:,.2f}",
                        f"${Decimal(portfolio['after_subtotal_micro'] - portfolio['before_subtotal_micro']) / 1000000:,.2f}",
                    ]
                ],
                "note": portfolio["scope"],
            },
            {
                "title": "Observed rates",
                "headers": ["Price", "Unit", "Before USD", "After USD", "Change USD", "Status"],
                "rows": [
                    [
                        r["price_id"],
                        r.get("unit", "Unknown"),
                        r["before_usd"],
                        r["after_usd"],
                        r["change_usd"],
                        r["status"],
                    ]
                    for r in history["prices"]
                ],
                "note": "Only identical provider, SKU, region, term and unit identities with fresh evidence are comparable.",
            },
        ]
    return output


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
    notes = extension_notes(result).encode()
    notes_path = ROOT / "docs/STRETCH.md"
    if args.check:
        if notes_path.read_bytes() != notes:
            raise ValueError("Stretch documentation drift")
    else:
        notes_path.write_bytes(notes)
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


def extension_notes(result: dict[str, Any]) -> str:
    sharing = result["sharing"]
    dedicated = Decimal(sharing["totals"]["dedicated"]) / 1000000
    shared = Decimal(sharing["totals"]["shared"]) / 1000000
    due = result["price_history"]["not_before"]
    observation_note = (
        "The December comparison remains outstanding; no complete optional release is claimed before it exists."
        if result["price_history"]["status"] == "pending future observation"
        else "The month-later comparison is recorded; only its matched subset is priced."
    )
    return f"""# Optional MLSpend extensions

The required release stays immutable. These features follow the separate plan in `evaluation/stretch/plan.json`; earlier platform outcomes were already known, so this is an engineering extension without a new confirmatory statistical claim.

| Feature | State and scope |
| --- | --- |
| Fractional GPU sharing | Implemented and tested on the registered synthetic workload; all allocation policies conserve integer microdollars. |
| Carbon alongside cost | GPU electricity estimate with a published regional proxy, nameplate power and explicit PUE sensitivity. Total footprint stays unknown. |
| Training budget guardrail | Deployed simulation accounts with atomic reservations, request replay and refusal above remaining forecast budget. No job is launched. |
| Readback warehouse | Pinned public showback table, generated combined lock and validated catalog; discovery, guarded SQL and numeric readback pass in the consumer integration. |
| Container and release hardening | Non-root container, read-only filesystem smoke test, restricted database grants and immutable baseline release. |
| Price history | {result["price_history"]["status"]}; the required second observation cannot precede {due}. |

## Derived results and limits

The synthetic sharing study prices dedicated placement at ${dedicated:,.6f} and shared placement at ${shared:,.6f} for identical hourly work. This assumes no interference, no quality loss and capacity that shrinks each hour. It is not measured production savings. The Shapley allocation uses an ideal fungible-slice capacity reference, then reconciles to the actual packed bill.

Modeled GPU carbon is {Decimal(result["carbon"]["dedicated"]["kg_co2e_estimate"]):.6f} kg CO2e for dedicated placement and {Decimal(result["carbon"]["shared"]["kg_co2e_estimate"]):.6f} kg CO2e for shared placement. The EPA grid region is a proxy for the modeled cloud region; the provider's actual facility is unknown. CPU, memory, storage, network, embodied emissions and token endpoints remain unestimated. No conversion from dollars to energy is used.

## Verify and use

Run `python -m scripts.build_stretch --check` to check the registered plan, generated claims and this document. Run the stretch accounting, catalog and training guardrail tests with pytest. The normal CI also exercises PostgreSQL persistence, the restricted container, strict types, browser behavior, dbt and repeat builds.

The deployed API accepts `POST /v1/simulation/budgets` and `POST /v1/simulation/budgets/{{budget_id}}/admissions`. Forecasts use the locked hourly rate, GPUs, duration and attempts, rounded upward to microdollars. Save a request UUID and reuse its exact payload after an uncertain response. A changed payload under the same UUID is refused. Budgets are isolated public demonstrations, not production accounts; storage, network and runtime overruns are outside the forecast.

Readback setup and the consumer check are documented in [its MLSpend guide](https://github.com/mekala27-45/readback/blob/mlspend-warehouse/docs/MLSPEND.md). The optional combined lock leaves its registered warehouse evaluation as the default. The deterministic natural-language floor retains its earlier question families; query MLSpend through the MCP tools or a tool-calling client. Select one allocation policy before summing showback cost.

Evidence: [core checks](https://github.com/mekala27-45/mlspend/actions/runs/41919675811), [live admission and replay](https://github.com/mekala27-45/mlspend/actions/runs/41920849070), and [consumer integration](https://github.com/mekala27-45/readback/actions/runs/41921146040). A separate database query confirmed one accepted decision, one refused decision and exactly the accepted reservation after the live replay.

## Month-later price observation

The scheduled collector preserves a candidate and its provider evidence. It cannot promote an early observation. After {due}, review the captured provider SKU, region, term, tier and unit before copying the candidate into a new directory under `data/prices`.

```sh
python -m scripts.promote_expanded_prices --directory data/prices/next --version next --run-url SOURCE_RUN_URL --reviewed-pages data/prices/next/reviewed-pages.json
python -m scripts.compare_price_history --after data/prices/next
python -m scripts.build_stretch
```

The reviewed-pages file is a list of Price records transcribed from the captured GitHub and Vercel pages. Its source URLs, hashes and retrieval dates must match the candidate. Omit this option to retain the earlier page rates, which remain stale for the comparison.

The new book and comparison are immutable once written. The comparison holds the original portfolio quantities fixed and rederives the price-history page from both locks. Missing quantities, stale rows and changed identities stay unpriced. Carried GitHub and Vercel rows retain their original retrieval dates and cannot count as fresh observations without new reviewed evidence. {observation_note}

{STATEMENT}
"""


if __name__ == "__main__":
    main()

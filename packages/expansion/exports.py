from __future__ import annotations

import csv
from collections import defaultdict
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

from packages.allocation.engine import infer_owner
from packages.core.io import STATEMENT, write_json
from packages.core.money import apportion
from packages.focus.export import contract_row, cost_row, parquet
from packages.prices.book import PriceBook
from packages.simulator.expanded import read_observed


def allocated_records(
    source: Path, allocation: list[dict[str, Any]], teams: list[str]
) -> Iterator[dict[str, Any]]:
    weights: dict[str, dict[str, float]] = defaultdict(dict)
    for item in allocation:
        if item["team"] in teams:
            weights[item["month"]][item["team"]] = item["usage_weight"]
    for row in read_observed(source):
        if row["team"] == "unallocated":
            row["team"], _ = infer_owner(
                row["resource"], row["namespace"], row["network"], set(teams)
            )
        if row["team"] != "shared":
            yield row
            continue
        shares = weights[row["timestamp"][:7]]
        allocation_micro = apportion(row["cost_micro"], shares)
        billed = apportion(row.get("billed_micro", row["cost_micro"]), shares)
        denominator = sum(shares.values())
        for team, weight in sorted(shares.items()):
            ratio = weight / denominator if denominator else 1 / len(shares)
            yield {
                **row,
                "id": row["id"] + "-" + team,
                "origin_id": row["id"],
                "team": team,
                "cost_micro": allocation_micro[team],
                "billed_micro": billed[team],
                "pricing_quantity": row["pricing_quantity"] * ratio,
                "allocated_ratio": ratio,
            }


def csv_file(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError("Empty finance extract")
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def workbook(path: Path, allocations: list[dict[str, Any]]) -> None:
    document = Workbook()
    sheet = document.active
    assert sheet is not None
    sheet.title = "Allocation"
    sheet.append(["MLSpend simulated allocation workbook"])
    sheet.append(["Method", "usage"])
    sheet.append([STATEMENT])
    sheet.append(
        [
            "Changing B2 recomputes the overhead allocation for each month. Source money remains fixed."
        ]
    )
    sheet.append(
        [
            "Month",
            "Team",
            "Direct USD",
            "Usage weight",
            "Custom weight",
            "Monthly overhead USD",
            "Policy weight",
            "Allocated overhead USD",
            "Statement USD",
            "Recorded usage USD",
            "Usage reconciliation USD",
        ]
    )
    rule = DataValidation(type="list", formula1='"even,direct,usage,custom"')
    sheet.add_data_validation(rule)
    rule.add(sheet["B2"])
    totals: dict[str, float] = defaultdict(float)
    for row in allocations:
        totals[row["month"]] += (row["methods"]["usage"] - row["direct_micro"]) / 1000000
    for index, row in enumerate(allocations, 6):
        sheet.append(
            [
                row["month"],
                row["team"],
                row["direct_micro"] / 1000000,
                row["usage_weight"],
                row["custom_weight"],
                totals[row["month"]],
                f'=IF(B{index}="unallocated",0,IF($B$2="even",1,IF($B$2="direct",C{index},IF($B$2="custom",E{index},D{index}))))',
                f"=IFERROR(F{index}*G{index}/SUMIF(A$6:A${len(allocations) + 5},A{index},G$6:G${len(allocations) + 5}),0)",
                f"=C{index}+H{index}",
                row["methods"]["usage"] / 1000000,
                f'=IF($B$2="usage",I{index}-J{index},0)',
            ]
        )
    for cell in sheet[5]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="253A52")
    for column in ("C", "F", "H", "I", "J", "K"):
        for cell in sheet[column][5:]:
            cell.number_format = "#,##0.00;[Red](#,##0.00)"
    for column in "ABCDEFGHIJK":
        sheet.column_dimensions[column].width = 22
    sheet.column_dimensions["B"].width = 18
    sheet.freeze_panes = "C6"
    sheet.auto_filter.ref = f"A5:K{len(allocations) + 5}"
    document.calculation.fullCalcOnLoad = True
    document.save(path)


def export_all(
    directory: Path,
    target: Path,
    analysis: dict[str, Any],
    book: PriceBook,
    teams: list[str],
    focus: bool = True,
) -> dict[str, Any]:
    target.mkdir(parents=True, exist_ok=True)
    allocations = [
        {
            "month": r["month"],
            "team": r["team"],
            "direct_usd": r["direct_micro"] / 1000000,
            **{method + "_usd": value / 1000000 for method, value in r["methods"].items()},
        }
        for r in analysis["allocation"]
    ]
    csv_file(target / "allocation.csv", allocations)
    csv_file(
        target / "unit-costs.csv",
        [
            {key: value for key, value in r.items() if key != "components_micro"}
            for r in analysis["units"]
        ],
    )
    csv_file(target / "training-experiments.csv", analysis["experiments"])
    workbook(target / "allocation.xlsx", analysis["allocation"])
    (target / "powerbi-measures.dax").write_text(
        "Effective USD = SUM(Allocation[usage_usd])\nDirect USD = SUM(Allocation[direct_usd])\nShared USD = [Effective USD] - [Direct USD]\nCost per Output = DIVIDE(SUM(UnitCosts[fully_loaded_micro]), SUM(UnitCosts[outputs])) / 1000000\n",
        encoding="utf-8",
    )
    (target / "powerbi-import.pq").write_text(
        'let\n  Source = Csv.Document(File.Contents(ExportFolder & "allocation.csv"),[Delimiter=",",Encoding=65001,QuoteStyle=QuoteStyle.Csv]),\n  Headers = Table.PromoteHeaders(Source),\n  Typed = Table.TransformColumnTypes(Headers,{{"month",type text},{"team",type text},{"usage_usd",Currency.Type},{"direct_usd",Currency.Type}})\nin Typed\n',
        encoding="utf-8",
    )
    (target / "tableau-calculations.txt").write_text(
        "Effective USD: SUM([usage_usd])\nShared USD: SUM([usage_usd])-SUM([direct_usd])\nCost per output: IF SUM([outputs]) > 0 THEN SUM([fully_loaded_micro])/1000000/SUM([outputs]) END\nImport allocation.csv with month and team as dimensions. Import unit-costs.csv separately; join only at matching grain to avoid duplicated spend.\n",
        encoding="utf-8",
    )
    (target / "README.md").write_text(
        "# Finance extracts\n\n"
        + STATEMENT
        + "\n\nThe CSV files use UTF-8 and explicit units. Set ExportFolder in Power Query. The workbook has live formulas and recalculates on opening; its reconciliation column can differ below one microdollar per allocation because the production ledger uses integer largest remainders. Power BI and Tableau formulas avoid averaging row-level unit costs.\n",
        encoding="utf-8",
    )
    counts = {}
    if focus:
        counts["CostAndUsage"] = parquet(
            (cost_row(row, book) for row in read_observed(directory / "observed.jsonl.gz")),
            target / "CostAndUsage.parquet",
            "CostAndUsage",
        )
        counts["ContractCommitment"] = parquet(
            [
                contract_row("simulated-t4-contract", "azure-t4", book),
                contract_row("simulated-a100-contract-3y", "azure-a100", book, years=3),
            ],
            target / "ContractCommitment.parquet",
            "ContractCommitment",
        )
        counts["AllocatedCostAndUsage"] = parquet(
            (
                cost_row(row, book)
                for row in allocated_records(
                    directory / "observed.jsonl.gz", analysis["allocation"], teams
                )
            ),
            target / "AllocatedCostAndUsage.parquet",
            "CostAndUsage",
        )
    result = {
        "focus_rows": counts,
        "allocation_rows": len(allocations),
        "unit_rows": len(analysis["units"]),
        "files": sorted(
            [
                "allocation.csv",
                "allocation.xlsx",
                "unit-costs.csv",
                "training-experiments.csv",
                "powerbi-measures.dax",
                "powerbi-import.pq",
                "tableau-calculations.txt",
                "README.md",
                "manifest.json",
            ]
            + (
                [
                    "CostAndUsage.parquet",
                    "ContractCommitment.parquet",
                    "AllocatedCostAndUsage.parquet",
                ]
                if focus
                else []
            )
        ),
    }
    write_json(target / "manifest.json", result)
    return result

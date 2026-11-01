"""Run the official supported rules against every row of all delivered FOCUS files."""

import json
import subprocess
from pathlib import Path

import duckdb

from scripts.audit_focus import audit


def main() -> None:
    source = Path("tmp/full-study/exports/expanded")
    output = Path("results/full-focus")
    output.mkdir(parents=True, exist_ok=True)
    criteria = "ACCOUNT_NAMING_SUPPORTED,AVAILABILITY_ZONE_SUPPORTED,COMMITMENT_DISCOUNT_SUPPORTED,CONTRACT_COMMITMENTS_SUPPORTED,DATA_GENERATOR_SPLIT_COST_ALLOCATION_SUPPORTED,MULTIPLE_PRICING_CATEGORIES_SUPPORTED,NEGOTIATED_PRICING_SUPPORTED,PUBLIC_PRICE_LIST_SUPPORTED,USAGE_MEASUREMENT_SUPPORTED,UNIT_PRICING_SUPPORTED,SUB_ACCOUNT_SUPPORTED,BILLING_BASED_ON_PROVISIONED_RESOURCES_SUPPORTED,RESOURCE_TYPE_ASSIGNMENT_SUPPORTED,REGION_SUPPORTED,TAGGING_SUPPORTED"
    reports = []
    with duckdb.connect() as connection:
        source_totals = (
            connection.read_parquet(str(source / "CostAndUsage.parquet"))
            .aggregate("sum(EffectiveCost), sum(BilledCost)")
            .fetchall()
        )
        allocated_totals = (
            connection.read_parquet(str(source / "AllocatedCostAndUsage.parquet"))
            .aggregate("sum(EffectiveCost), sum(BilledCost)")
            .fetchall()
        )
        if source_totals != allocated_totals:
            raise AssertionError("Allocated FOCUS export does not conserve source money")
        invalid_ratios = connection.execute(
            """SELECT count(*) FROM (
                SELECT json_extract_string(AllocatedMethodDetails, '$.x_OriginId') AS origin,
                       sum(CAST(json_extract(AllocatedMethodDetails, '$.Elements[0].AllocatedRatio') AS DOUBLE)) AS ratio
                FROM read_parquet(?) WHERE AllocatedMethodDetails IS NOT NULL
                GROUP BY origin HAVING origin IS NULL OR abs(ratio - 1) > 1e-12
            )""",
            [str(source / "AllocatedCostAndUsage.parquet")],
        ).fetchall()[0][0]
        if invalid_ratios:
            raise AssertionError("Allocated FOCUS ratios do not sum to one per origin")
        (output / "conservation.json").write_text(
            json.dumps(
                {
                    "status": "pass",
                    "effective_usd": str(source_totals[0][0]),
                    "billed_usd": str(source_totals[0][1]),
                    "invalid_origin_ratios": invalid_ratios,
                }
            )
            + "\n",
            encoding="utf-8",
        )
    for name in ("CostAndUsage", "AllocatedCostAndUsage"):
        target = output / name
        target.mkdir(parents=True, exist_ok=True)
        with duckdb.connect() as connection:
            connection.read_parquet(str(source / (name + ".parquet"))).create_view("input")
            count = connection.execute("SELECT count(*) FROM input").fetchall()[0][0]
            assert count > 500000
            compat = target / "compatible.parquet"
            connection.sql(
                "SELECT *, ServiceProviderName AS ProviderName, HostProviderName AS PublisherName FROM input"
            ).write_parquet(str(compat))
        for dataset in ("CostAndUsage", "ContractCommitment"):
            file = compat if dataset == "CostAndUsage" else source / "ContractCommitment.parquet"
            with (target / (dataset + ".log")).open("w") as log:
                subprocess.run(
                    [
                        ".focus-validator/bin/focus-validator",
                        "--data-file",
                        str(file),
                        "--validate-version",
                        "1.3.0.1",
                        "--focus-dataset",
                        dataset,
                        "--applicability-criteria",
                        criteria,
                        "--output-type",
                        "unittest",
                        "--output-destination",
                        str(target / (dataset + ".xml")),
                    ],
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    check=True,
                )
        reports.append({"export": name, "rows": count, **audit(target)})
        compat.unlink()
    (output / "summary.json").write_text(json.dumps(reports, indent=2) + "\n")
    print(json.dumps(reports))


if __name__ == "__main__":
    main()

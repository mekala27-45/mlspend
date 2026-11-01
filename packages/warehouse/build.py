from __future__ import annotations

import gzip
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import duckdb


def load_lines(path: Path) -> list[dict[str, Any]]:
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        return [json.loads(line) for line in stream]


def violation(row: dict[str, Any]) -> list[str]:
    rules = []
    required = (
        "ChargePeriodStart",
        "ChargePeriodEnd",
        "BillingCurrency",
        "BilledCostMicro",
        "EffectiveCostMicro",
        "ResourceId",
        "x_Team",
        "x_Model",
        "x_Pool",
        "x_PriceId",
    )
    if any(key not in row or row[key] is None for key in required):
        return ["required_fields"]
    if row["BillingCurrency"] != "USD":
        rules.append("currency")
    if row["BilledCostMicro"] < 0:
        rules.append("negative_billed")
    if row["EffectiveCostMicro"] < 0:
        rules.append("negative_effective")
    if row["ChargePeriodEnd"] <= row["ChargePeriodStart"]:
        rules.append("period_order")
    if not row["ResourceId"]:
        rules.append("resource")
    if not row["x_Team"]:
        rules.append("owner")
    if not row["x_Model"]:
        rules.append("model")
    if not row["x_PriceId"]:
        rules.append("price")
    if row.get("x_CostKind") not in ("workload", "idle", "shared"):
        rules.append("cost_kind")
    return rules


def build(source: Path, database: Path) -> dict[str, Any]:
    connection = duckdb.connect(str(database))
    connection.execute("SET TimeZone='UTC'")
    connection.execute(
        "CREATE OR REPLACE TABLE source_charges AS SELECT * FROM read_json_auto(?)",
        [str(source / "charges.jsonl.gz")],
    )
    connection.execute(
        "CREATE OR REPLACE TABLE telemetry AS SELECT * FROM read_json_auto(?)",
        [str(source / "telemetry.jsonl.gz")],
    )
    rows = load_lines(source / "charges.jsonl.gz")
    failures = [{"row": i, "rules": violation(row)} for i, row in enumerate(rows) if violation(row)]
    if failures:
        connection.close()
        raise ValueError(f"Quarantine rejected {len(failures)} rows; no silent removal")
    connection.execute("""CREATE OR REPLACE TABLE charges AS SELECT
        CAST(ChargePeriodStart AS TIMESTAMPTZ) AS charge_start,
        substring(CAST(ChargePeriodStart AS VARCHAR),1,10) AS day,
        substring(CAST(ChargePeriodStart AS VARCHAR),1,7) AS month,
        x_Team AS team, x_Model AS model, x_Pool AS pool, ResourceId AS resource,
        x_CostKind AS kind, x_PriceId AS price_id,
        CAST(BilledCostMicro AS BIGINT) AS billed_micro,
        CAST(EffectiveCostMicro AS BIGINT) AS effective_micro
        FROM source_charges""")
    grains = {"team": "x_Team", "model": "x_Model", "month": "month", "day": "day"}
    checks = []
    for grain, key in grains.items():
        expected: dict[str, list[int]] = defaultdict(lambda: [0, 0, 0])
        for row in rows:
            group = (
                row["ChargePeriodStart"][: 7 if grain == "month" else 10]
                if grain in ("month", "day")
                else row[key]
            )
            expected[group][0] += row["BilledCostMicro"]
            expected[group][1] += row["EffectiveCostMicro"]
            expected[group][2] += 1
        # grain is selected only from this fixed mapping, never request data.
        actual = {
            str(r[0]): [int(r[1]), int(r[2]), int(r[3])]
            for r in connection.execute(
                f"SELECT {grain}, sum(billed_micro), sum(effective_micro), count(*) FROM charges GROUP BY {grain}"
            ).fetchall()
        }
        checks.append(
            {
                "grain": grain,
                "groups": len(expected),
                "matches": actual == dict(expected),
                "tolerance_micro": 0,
            }
        )
    if not all(c["matches"] for c in checks):
        raise AssertionError("Independent source reconciliation failed")
    connection.execute(
        "CREATE OR REPLACE TABLE daily AS SELECT day, team, pool, kind, sum(effective_micro)::BIGINT cost_micro FROM charges GROUP BY ALL"
    )
    connection.execute(
        "CREATE OR REPLACE TABLE monthly AS SELECT month, team, pool, kind, sum(effective_micro)::BIGINT cost_micro FROM charges GROUP BY ALL"
    )
    connection.execute("COPY charges TO ? (FORMAT PARQUET)", [str(source / "charges.parquet")])
    connection.close()
    return {
        "checks": checks,
        "quarantined_rows": 0,
        "rows": len(rows),
        "total_micro": sum(r["BilledCostMicro"] for r in rows),
        "engine": duckdb.__version__,
    }

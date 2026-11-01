"""Contracted ingestion, explicit quarantine and independent grouped reconciliation."""

from __future__ import annotations

import copy
from collections import defaultdict
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import duckdb

from packages.core.io import canonical, write_json
from packages.core.money import microdollars
from packages.prices.book import PriceBook
from packages.simulator.expanded import read_observed


def violations(row: dict[str, Any], book: PriceBook, seen: set[str]) -> list[str]:
    errors = []
    for key in (
        "id",
        "timestamp",
        "team",
        "model",
        "resource",
        "price_id",
        "cost_micro",
        "pricing_quantity",
    ):
        if row.get(key) is None or row.get(key) == "":
            errors.append("required:" + key)
    if errors:
        return errors
    if row["id"] in seen:
        errors.append("duplicate:id")
    try:
        timestamp = datetime.fromisoformat(row["timestamp"])
        if timestamp.utcoffset() != timedelta(0):
            errors.append("timestamp:utc")
    except (ValueError, TypeError):
        errors.append("timestamp:parse")
    try:
        quantity = Decimal(str(row["pricing_quantity"]))
        if not quantity.is_finite() or quantity < 0:
            errors.append("quantity:finite_nonnegative")
    except Exception:
        errors.append("quantity:parse")
    if not isinstance(row["cost_micro"], int) or row["cost_micro"] < 0:
        errors.append("cost:nonnegative_integer")
    try:
        price = book.get(row["price_id"])
        if (
            not errors
            and row["kind"] != "purchase"
            and abs(
                microdollars(price.usd * Decimal(str(row["pricing_quantity"]))) - row["cost_micro"]
            )
            > 1
        ):
            errors.append("cost:quantity_times_rate")
    except ValueError:
        errors.append("price:unknown")
    return errors


def injected_defects(sample: dict[str, Any]) -> list[dict[str, Any]]:
    """Producer fault injection exercises the real ingestion path, not only assertions."""
    changes = [
        {"id": None},
        {"id": sample["id"]},
        {"price_id": "absent-sku"},
        {"cost_micro": None},
        {"pricing_quantity": -1},
        {"team": None},
        {"timestamp": "not-a-date"},
        {"timestamp": "2025-01-01T00:00:00+05:30"},
        {"cost_micro": -1},
        {"pricing_quantity": "NaN"},
    ]
    result = []
    for i, change in enumerate(changes):
        row = copy.deepcopy(sample)
        row.update(id=f"injected-{i}")
        row.update(change)
        result.append(row)
    return result


def ingest(directory: Path, book: PriceBook) -> dict[str, Any]:
    accepted_path = directory / "accepted.jsonl"
    quarantine = []
    seen: set[str] = set()
    # Aggregate the original Python records before loading them through SQL.
    independent: dict[str, dict[str, list[int]]] = {
        grain: defaultdict(lambda: [0, 0, 0]) for grain in ("team", "model", "month", "day")
    }
    sample = None
    with accepted_path.open("wb") as stream:
        for row in read_observed(directory / "observed.jsonl.gz"):
            sample = sample or row
            errors = violations(row, book, seen)
            if errors:
                quarantine.append({"source": "simulator", "row": row, "errors": errors})
                continue
            seen.add(row["id"])
            price = book.get(row["price_id"])
            row["price_effective_date"] = price.effective_date.isoformat()
            row["pricing_as_of"] = price.retrieved_date.isoformat()
            stream.write(canonical(row))
            for grain, key in {
                "team": row["team"],
                "model": row["model"],
                "month": row["timestamp"][:7],
                "day": row["timestamp"][:10],
            }.items():
                independent[grain][key][0] += 1
                independent[grain][key][1] += row["cost_micro"]
                independent[grain][key][2] += row.get("billed_micro", row["cost_micro"])
        if sample is None:
            raise ValueError("No source rows")
        for row in injected_defects(sample):
            errors = violations(row, book, seen)
            if not errors:
                raise AssertionError("An injected ingestion defect escaped quarantine")
            quarantine.append({"source": "producer_fault_injection", "row": row, "errors": errors})
    write_json(directory / "quarantine.json", quarantine)
    prices_path = directory / "prices.json"
    write_json(prices_path, [p.model_dump(mode="json") for p in book.rows])
    database = directory / "warehouse.duckdb"
    checks = []
    with duckdb.connect(str(database)) as connection:
        connection.execute("SET TimeZone='UTC'")
        connection.execute(
            "CREATE OR REPLACE TABLE observed AS SELECT * FROM read_json_auto(?, sample_size=-1)",
            [str(accepted_path)],
        )
        connection.execute(
            "CREATE OR REPLACE TABLE prices AS SELECT * FROM read_json_auto(?)", [str(prices_path)]
        )
        connection.execute(
            "CREATE OR REPLACE VIEW priced AS SELECT o.*, p.usd::DECIMAL(38,12) AS unit_rate FROM observed o JOIN prices p ON o.price_id=p.id AND o.price_effective_date=p.effective_date AND p.effective_date <= o.pricing_as_of"
        )
        observed_count = connection.execute("SELECT COUNT(*) FROM observed").fetchone()
        joined_count = connection.execute("SELECT COUNT(*) FROM priced").fetchone()
        assert observed_count is not None and joined_count is not None
        count, priced_count = observed_count[0], joined_count[0]
        if count != priced_count or not count:
            raise AssertionError("Effective-date join lost or duplicated charges")
        for grain, expression in {
            "team": "team",
            "model": "model",
            "month": "strftime(timestamp, '%Y-%m')",
            "day": "strftime(timestamp, '%Y-%m-%d')",
        }.items():
            actual = {
                str(key): [int(number), int(amount), int(billed)]
                for key, number, amount, billed in connection.execute(
                    f"SELECT {expression}, COUNT(*), SUM(cost_micro), SUM(COALESCE(billed_micro,cost_micro)) FROM priced GROUP BY 1"
                ).fetchall()
            }
            expected = dict(independent[grain])
            if actual != expected:
                raise AssertionError("Independent grouped reconciliation failed: " + grain)
            checks.append(
                {
                    "grain": grain,
                    "groups": len(actual),
                    "count_difference": 0,
                    "cost_difference_micro": 0,
                    "billed_difference_micro": 0,
                    "tolerance_micro": 1,
                }
            )
    accepted_path.unlink()
    return {
        "accepted": count,
        "quarantined": len(quarantine),
        "fault_injections": sum(r["source"] == "producer_fault_injection" for r in quarantine),
        "source_defects": sum(r["source"] == "simulator" for r in quarantine),
        "checks": checks,
        "effective_date_join_rows": priced_count,
    }

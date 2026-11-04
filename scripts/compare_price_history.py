"""Reprice the frozen public usage against a reviewed second locked snapshot."""

from __future__ import annotations

import argparse
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from packages.core.io import ROOT, digest, read_json, write_json
from packages.prices.book import PriceBook
from packages.stretch.prices import compare_prices, reprice_usage


def comparison_for(root: Path, directory: Path) -> dict[str, Any]:
    directory = directory.resolve()
    if not directory.is_relative_to((root / "data/prices").resolve()):
        raise ValueError("The reviewed book must be versioned in data/prices")
    before = PriceBook(root / "data/prices/expanded")
    after = PriceBook(directory)
    due = date.fromisoformat(
        read_json(root / "evaluation/stretch/plan.json")["price_observation"]["not_before"]
    )
    if datetime.now(UTC).date() < due:
        raise ValueError("The required month-later price observation is not due")
    if any(p.retrieved_date > datetime.now(UTC).date() for p in after.rows):
        raise ValueError("A source cannot have a future observation date")
    comparison = compare_prices(before, after, due)
    if not any(r["status"] == "matched" for r in comparison):
        raise ValueError("No fresh comparable price observations")
    portfolio = read_json(root / "results/portfolio-usage.json")
    ledgers = read_json(root / "results/committed-ledgers.json")
    usage: list[dict[str, Any]] = [
        {
            "id": str(r["job_id"]),
            "repository": r["repository"],
            "kind": "Actions job",
            "price_id": r["price_id"],
            "quantity": r["minutes"],
            "unit": "minute",
            "source_url": r["source_url"],
        }
        for r in portfolio["jobs"]
    ]
    usage.extend(
        {
            "id": str(i),
            "repository": r["repository"],
            "kind": r["kind"],
            "price_id": r.get("price_id"),
            "quantity": r.get("pricing_quantity"),
            "unit": r.get("pricing_unit"),
            "source_url": r["source_url"],
            "original_status": r.get("price_status", "unpriced"),
            "window_status": r.get("in_window"),
        }
        for i, r in enumerate(ledgers["rows"])
    )
    return {
        "after_book": directory.relative_to(root.resolve()).as_posix(),
        "before_digest": before.digest,
        "after_digest": after.digest,
        "usage_digest": digest(usage),
        "prices": comparison,
        "portfolio": reprice_usage(usage, comparison),
        "status": "observed comparison",
        "not_before": str(due),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--after", type=Path, required=True, help="Reviewed, versioned locked book")
    args = parser.parse_args()
    output = comparison_for(ROOT, args.after)
    target = ROOT / "results/stretch/price-comparison.json"
    if target.exists() and read_json(target) != output:
        raise ValueError("A comparison already exists; create a new version")
    write_json(target, output)
    print(
        {
            "matched_prices": sum(r["status"] == "matched" for r in output["prices"]),
            "usage_rows": len(output["portfolio"]["rows"]),
            "status": output["status"],
        }
    )


if __name__ == "__main__":
    main()

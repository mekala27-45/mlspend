from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

from packages.core.contracts import Price
from packages.core.io import ROOT, digest, read_json, write_json


def initialize_observed_book() -> None:
    source = read_json(ROOT / "data/prices/observed.json")
    rows = []
    for raw in source["rows"]:
        record = {k: v for k, v in raw.items() if k != "source_record"}
        record.update(
            service="Compute",
            region="eastus"
            if raw["provider"] == "Azure"
            else ("iad1" if raw["provider"] == "Vercel" else "global"),
            term="on_demand",
            retrieved_date=source["retrieved_date"],
            source_digest=digest(raw["source_record"]),
            source_kind="retrieval_snapshot",
        )
        rows.append(Price.model_validate(record).model_dump(mode="json"))
    book = {"rows": rows, "provenance": source["provenance"]}
    destination = ROOT / "data/prices/book.json"
    if destination.exists() and read_json(destination) != book:
        raise ValueError("Existing price book differs. Use an explicit promotion.")
    write_json(destination, book)
    write_json(
        ROOT / "data/prices/lock.json",
        {
            "book_digest": digest(book),
            "source_digest": digest(source),
            "mode": "browser-observed excerpts; Actions promotion pending",
        },
    )


class PriceBook:
    def __init__(self, directory: Path = ROOT / "data/prices") -> None:
        book = read_json(directory / "book.json")
        lock = read_json(directory / "lock.json")
        if digest(book) != lock["book_digest"] or not book["rows"]:
            raise ValueError("Price lock is missing, empty or invalid")
        self.digest = str(lock["book_digest"])
        self.rows = [Price.model_validate(row) for row in book["rows"]]
        keys = [(p.id, p.effective_date) for p in self.rows]
        if len(set(keys)) != len(keys):
            raise ValueError("Ambiguous price versions")

    def get(self, identifier: str, on: date | None = None, unit: str | None = None) -> Price:
        candidates = [
            p for p in self.rows if p.id == identifier and (on is None or p.effective_date <= on)
        ]
        if not candidates:
            raise ValueError(f"No sourced price in force: {identifier}")
        price = max(candidates, key=lambda p: p.effective_date)
        if unit is not None and price.unit != unit:
            raise ValueError(f"Expected {unit}; price is per {price.unit}")
        return price


def normalized_rate(
    amount: Decimal, unit: str, term_hours: int | None = None
) -> tuple[Decimal, str]:
    if amount < 0 or not amount.is_finite():
        raise ValueError("Invalid rate")
    if term_hours is not None:
        if term_hours <= 0:
            raise ValueError("Term must be positive")
        return amount / term_hours, "hour"
    units = {
        "1 Hour": (Decimal(1), "hour"),
        "1 GB/Month": (Decimal(1), "gb_month"),
        "1M tokens": (Decimal(1), "million_tokens"),
        "1000 tokens": (Decimal(1000), "million_tokens"),
        "minute": (Decimal(1), "minute"),
    }
    if unit not in units:
        raise ValueError(f"Unsupported source unit: {unit}")
    multiplier, target = units[unit]
    return amount * multiplier, target

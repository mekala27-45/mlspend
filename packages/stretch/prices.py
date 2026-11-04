"""Compare independently locked price snapshots without changing historical usage."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

from packages.core.contracts import Price
from packages.core.money import microdollars
from packages.prices.book import PriceBook


def compare_prices(before: PriceBook, after: PriceBook, not_before: date) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for identifier in sorted({p.id for p in before.rows} | {p.id for p in after.rows}):
        row: dict[str, Any] = {
            "price_id": identifier,
            "before_usd": None,
            "after_usd": None,
            "change_usd": None,
            "status": "unmatched",
        }
        try:
            old, new = before.get(identifier), after.get(identifier)
        except ValueError:
            rows.append(row)
            continue
        row.update(
            before_usd=str(old.usd),
            before_source=old.source_url,
            after_source=new.source_url,
            unit=old.unit,
        )

        def identity(p: Price) -> tuple[str, str, str, str, str]:
            return p.provider, p.sku, p.region, p.term, p.unit

        if identity(old) != identity(new):
            row["status"] = "identity or unit changed; not comparable"
        elif new.retrieved_date < not_before:
            row["status"] = "new observation is not yet due or is stale"
        else:
            row.update(
                after_usd=str(new.usd),
                change_usd=str(new.usd - old.usd),
                status="matched",
                before_observed=str(old.retrieved_date),
                after_observed=str(new.retrieved_date),
            )
        rows.append(row)
    return rows


def reprice_usage(usage: list[dict[str, Any]], comparison: list[dict[str, Any]]) -> dict[str, Any]:
    prices = {r["price_id"]: r for r in comparison}
    output: list[dict[str, Any]] = []
    for item in usage:
        row = {**item, "before_micro": None, "after_micro": None, "change_micro": None}
        price = prices.get(item.get("price_id"))
        if (
            not price
            or price["status"] != "matched"
            or item.get("quantity") is None
            or item.get("unit") != price["unit"]
        ):
            row["status"] = "not priced: missing comparable price or measured quantity"
        else:
            quantity = Decimal(str(item["quantity"]))
            if not quantity.is_finite() or quantity < 0:
                raise ValueError("Usage must be finite and nonnegative")
            old = microdollars(quantity * Decimal(price["before_usd"]))
            new = microdollars(quantity * Decimal(price["after_usd"]))
            row.update(
                before_micro=old,
                after_micro=new,
                change_micro=new - old,
                status="same usage at two observed prices",
            )
        output.append(row)
    matched = [r for r in output if r["after_micro"] is not None]
    return {
        "rows": output,
        "matched_rows": len(matched),
        "unpriced_rows": len(output) - len(matched),
        "before_subtotal_micro": sum(r["before_micro"] for r in matched),
        "after_subtotal_micro": sum(r["after_micro"] for r in matched),
        "scope": "Matched rows only. Unknown costs are not zero. Quantities are unchanged.",
    }

"""Promote a verified Actions Azure artifact while preserving the previous snapshot."""

from __future__ import annotations

import argparse
import shutil
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from packages.core.contracts import Price
from packages.core.io import ROOT, digest, read_json, write_json
from packages.prices.book import normalized_rate


def promote(evidence: Path, run_url: str, artifact_digest: str) -> None:
    source = read_json(evidence / "results/fetched-prices.json")
    request = read_json(ROOT / "requests/prices.json")
    if source["request_digest"] != digest(request) or not source["rows"]:
        raise ValueError("Price evidence does not match the committed request")
    directory = ROOT / "data/prices"
    old = read_json(directory / "book.json")
    old_lock = read_json(directory / "lock.json")
    if old.get("version") == 2:
        raise ValueError("Version two already exists; use a new reviewed promotion version")
    mappings = {
        "Standard_D4s_v5": "azure-cpu",
        "Standard_NC24ads_A100_v4": "azure-a100",
        "Standard_NC4as_T4_v3": "azure-t4",
    }
    rows = [row for row in old["rows"] if row["provider"] != "Azure"]
    fetched = set()
    for row in source["rows"]:
        raw = row["raw"]
        if digest(raw) != row["source_row_digest"]:
            raise ValueError("Fetched price row digest changed")
        cache = read_json(evidence / "tmp/http-cache" / (digest(row["source_url"]) + ".json"))
        if raw not in cache["body"]["Items"]:
            raise ValueError("A normalized price is absent from the cached provider page")
        term = row["term"]
        suffix = ""
        hours = None
        if term in ("1 Year", "3 Years"):
            hours = 8760 if term == "1 Year" else 26280
            suffix = "-reserved-1y" if hours == 8760 else "-reserved-3y"
        elif "Spot" in raw["meterName"]:
            suffix = "-spot"
        elif "Low Priority" in raw["meterName"]:
            suffix = "-low-priority"
        elif term != "Consumption":
            raise ValueError("Unrecognized contract term")
        amount, unit = normalized_rate(Decimal(row["amount"]), row["unit"], hours)
        identifier = mappings[row["sku"]] + suffix
        fetched.add(identifier)
        price = Price(
            id=identifier,
            provider="Azure",
            service="Compute",
            sku=row["sku"],
            region=row["region"],
            unit=unit,
            usd=amount,
            term=term if suffix else "on_demand",
            effective_date=datetime.fromisoformat(row["effective_date"]).date(),
            retrieved_date=datetime.fromisoformat(source["retrieved_at"]).date(),
            source_url=row["source_url"],
            source_digest=cache["response_digest"],
            source_kind="provider_response",
        )
        rows.append(price.model_dump(mode="json"))
    if not set(mappings.values()).issubset(fetched):
        raise ValueError("Not all simulated on-demand SKUs were fetched")
    write_json(directory / "history/v1-book.json", old)
    write_json(directory / "history/v1-lock.json", old_lock)
    shutil.copytree(evidence, directory / "evidence/v2", dirs_exist_ok=True)
    book = {
        "version": 2,
        "rows": sorted(rows, key=lambda r: (r["id"], r["effective_date"])),
        "provenance": "Azure rates fetched in Actions; GitHub and Vercel rates retain their explicitly labeled retrieved excerpts. AWS, storage, network and model-token rates remain outside this book.",
    }
    write_json(directory / "book.json", book)
    write_json(
        directory / "lock.json",
        {
            "version": 2,
            "book_digest": digest(book),
            "source_digest": digest(source),
            "previous_book_digest": old_lock["book_digest"],
            "run_url": run_url,
            "artifact_sha256": artifact_digest,
            "mode": "Actions Azure promotion with separately labeled manual excerpts",
        },
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence", type=Path)
    parser.add_argument("--run-url", required=True)
    parser.add_argument("--artifact-digest", required=True)
    args = parser.parse_args()
    promote(args.evidence, args.run_url, args.artifact_digest)

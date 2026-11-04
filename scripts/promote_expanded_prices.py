"""Reviewed promotion into a new book; existing books and registrations stay intact."""

from __future__ import annotations

import argparse
from collections import defaultdict
from decimal import Decimal
from pathlib import Path
from typing import Any

from packages.core.contracts import Price
from packages.core.io import ROOT, digest, read_json, write_json
from packages.prices.book import PriceBook


def reviewed_page_rows(
    raw: list[dict[str, Any]], source: dict[str, Any], prior: PriceBook
) -> list[Price]:
    rows = [Price.model_validate(row) for row in raw]
    if len({row.id for row in rows}) != len(rows):
        raise ValueError("Duplicate reviewed page rate")
    for row in rows:
        if row.provider not in {"GitHub", "Vercel"} or prior.get(row.id).provider != row.provider:
            raise ValueError("Reviewed page rows must identify an existing GitHub or Vercel rate")
        page = source["pages"][row.provider.lower()]
        if (
            str(row.retrieved_date) != source["retrieved_at"][:10]
            or row.source_digest != page["sha256"]
            or row.source_url != page["url"]
            or row.source_kind != "retrieval_snapshot"
        ):
            raise ValueError("Reviewed page rate does not identify the captured provider evidence")
    return rows


def promote(
    directory: Path, version: str, run_url: str, reviewed_pages: Path | None = None
) -> None:
    directory = directory.resolve()
    if not directory.is_relative_to((ROOT / "data/prices").resolve()):
        raise ValueError("New books must be versioned under data/prices")
    if (directory / "lock.json").exists():
        raise ValueError("Expanded book is already locked; create a new version")
    source = read_json(directory / "candidate.json")
    retrieved = source["retrieved_at"][:10]
    rows: list[dict[str, Any]] = []
    identifiers = {
        "Standard_NC4as_T4_v3": "azure-t4",
        "Standard_NC24ads_A100_v4": "azure-a100",
        "Standard_NC6s_v3": "azure-v100",
        "Standard_D4s_v5": "azure-cpu",
    }

    def add(
        identifier: str,
        amount: Decimal,
        unit: str,
        provider: str,
        sku: str,
        service: str,
        region: str,
        term: str,
        effective: str,
        url: str,
        evidence_digest: str,
    ) -> None:
        rows.append(
            Price(
                id=identifier,
                usd=amount,
                unit=unit,
                provider=provider,
                sku=sku,
                service=service,
                region=region,
                term=term,
                effective_date=effective[:10],
                retrieved_date=retrieved,
                source_url=url,
                source_digest=evidence_digest,
                source_kind="provider_response",
            ).model_dump(mode="json")
        )

    for item in source["azure"]:
        raw = item["raw"]
        if digest(raw) != item["source_row_digest"]:
            raise ValueError("Azure evidence changed")
        sku = raw["armSkuName"]
        amount = Decimal(str(raw["retailPrice"]))
        identifier = identifiers.get(sku)
        unit, term, service = "hour", "on_demand", "Compute"
        if identifier:
            if raw["type"] == "Reservation":
                years = int(raw["reservationTerm"].split()[0])
                amount /= years * 8760
                identifier += f"-reserved-{years}y"
                term = raw["reservationTerm"]
            elif "Spot" in raw["meterName"]:
                identifier += "-spot"
                term = "spot"
            elif "Low Priority" in raw["meterName"]:
                identifier += "-low-priority"
                term = "low_priority"
            for saving in raw.get("savingsPlan", []):
                years = int(saving["term"].split()[0])
                add(
                    identifiers[sku] + f"-savings-{years}y",
                    Decimal(str(saving["retailPrice"])),
                    "hour",
                    "Azure",
                    sku,
                    "Compute",
                    "eastus",
                    "savings_plan_" + saving["term"],
                    raw["effectiveStartDate"],
                    item["source_url"],
                    item["source_row_digest"],
                )
        elif (
            raw["meterName"]
            in {"Hot LRS Data Stored", "Cool LRS Data Stored", "Cold LRS Data Stored"}
            and raw["tierMinimumUnits"] == 0
        ):
            identifier = "azure-storage-" + raw["meterName"].split()[0].lower()
            unit, service, sku = "gb_month", "Storage", raw["meterName"]
        elif (
            raw["meterName"] == "Standard Data Transfer Out"
            and raw["productName"] == "Rtn Preference: MGN"
            and raw["tierMinimumUnits"] == 100
        ):
            identifier, unit, service, sku = "azure-egress", "gb", "Networking", raw["meterName"]
        else:
            continue
        add(
            identifier,
            amount,
            unit,
            "Azure",
            sku,
            service,
            "eastus",
            term,
            raw["effectiveStartDate"],
            item["source_url"],
            item["source_row_digest"],
        )

    aws = source["aws"]
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for raw in aws["raw_rows"]:
        if raw["Currency"] != "USD":
            raise ValueError("Unexpected AWS currency")
        if raw["operation"] != "RunInstances":
            continue
        if raw["TermType"] == "OnDemand" and raw["Unit"] == "Hrs":
            add(
                "aws-" + raw["Instance Type"],
                Decimal(raw["PricePerUnit"]),
                "hour",
                "AWS",
                raw["Instance Type"],
                "Compute",
                "us-east-1",
                "on_demand",
                raw["EffectiveDate"],
                aws["source_url"],
                aws["response_sha256"],
            )
        elif raw["TermType"] == "Reserved":
            groups[(raw["SKU"], raw["OfferTermCode"])].append(raw)
    for group in groups.values():
        raw = group[0]
        years = int(raw["LeaseContractLength"].removesuffix("yr"))
        hourly = sum((Decimal(r["PricePerUnit"]) for r in group if r["Unit"] == "Hrs"), Decimal(0))
        upfront = sum(
            (Decimal(r["PricePerUnit"]) for r in group if r["Unit"] == "Quantity"), Decimal(0)
        )
        identifier = (
            "aws-"
            + raw["Instance Type"]
            + "-"
            + raw["OfferingClass"]
            + "-"
            + raw["PurchaseOption"].lower().replace(" ", "-")
            + f"-{years}y"
        )
        add(
            identifier,
            hourly + upfront / (years * 8760),
            "hour",
            "AWS",
            raw["Instance Type"],
            "Compute",
            "us-east-1",
            f"reserved_{years}y_" + raw["PurchaseOption"],
            raw["EffectiveDate"],
            aws["source_url"],
            aws["response_sha256"],
        )

    # The first row for each model in the captured page is Standard, short context.
    page = source["pages"]["openai"]
    for model in ("gpt-6.1-terra", "gpt-6-luna"):
        line = next(line for line in page["candidate_lines"] if line.split("|")[1].strip() == model)
        cells = [cell.strip() for cell in line.split("|")]
        for direction, column in (("input", 2), ("output", 3), ("cached", 4)):
            amount = Decimal(cells[column].removeprefix("$"))
            add(
                "openai-" + model + "-" + direction,
                amount,
                "million_tokens",
                "OpenAI",
                model + " " + direction,
                "AI and Machine Learning",
                "global",
                "standard_short_context",
                retrieved,
                page["url"],
                page["sha256"],
            )

    prior = PriceBook()
    reviewed = (
        reviewed_page_rows(read_json(reviewed_pages), source, prior) if reviewed_pages else []
    )
    replacements = {row.id: row for row in reviewed}
    rows.extend(
        replacements.get(p.id, p).model_dump(mode="json")
        for p in prior.rows
        if p.provider in {"GitHub", "Vercel"}
    )
    keys = [(r["id"], r["effective_date"]) for r in rows]
    if len(keys) != len(set(keys)):
        raise ValueError(
            f"Ambiguous effective-dated source prices: {[key for key in set(keys) if keys.count(key) > 1]}"
        )
    book = {
        "version": version,
        "rows": sorted(rows, key=lambda r: (r["id"], r["effective_date"])),
        "provenance": "Reviewed Actions provider responses and Standard short-context provider pricing table. Prior GitHub and Vercel excerpt rows retain their original evidence. GB-month storage and paid marginal egress tiers exclude free allowances; full tier schedule retained in candidate.",
    }
    write_json(directory / "book.json", book)
    write_json(
        directory / "lock.json",
        {
            "version": version,
            "book_digest": digest(book),
            "candidate_digest": digest(source),
            "prior_book_digest": prior.digest,
            "reviewed_pages_digest": digest([row.model_dump(mode="json") for row in reviewed]),
            "run_url": run_url,
            "review": "Checked Azure meter, region, tier and term; combined AWS upfront plus recurring dimensions per offer; checked OpenAI Standard short-context table order against the published page.",
        },
    )
    print({"prices": len(rows), "book_digest": digest(book)})


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument(
        "--run-url", required=True, help="Evidence run containing the reviewed candidate"
    )
    parser.add_argument(
        "--reviewed-pages",
        type=Path,
        help="Reviewed GitHub/Vercel Price rows tied to candidate page hashes",
    )
    args = parser.parse_args()
    promote(args.directory, args.version, args.run_url, args.reviewed_pages)

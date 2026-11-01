"""Reviewed promotion into a new book; existing books and registrations stay intact."""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from typing import Any

from packages.core.contracts import Price
from packages.core.io import ROOT, digest, read_json, write_json
from packages.prices.book import PriceBook


def promote() -> None:
    directory = ROOT / "data/prices/expanded"
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
    rows.extend(p.model_dump(mode="json") for p in prior.rows if p.provider in {"GitHub", "Vercel"})
    keys = [(r["id"], r["effective_date"]) for r in rows]
    if len(keys) != len(set(keys)):
        raise ValueError(
            f"Ambiguous effective-dated source prices: {[key for key in set(keys) if keys.count(key) > 1]}"
        )
    book = {
        "version": "expanded-1",
        "rows": sorted(rows, key=lambda r: (r["id"], r["effective_date"])),
        "provenance": "Reviewed Actions provider responses and Standard short-context provider pricing table. Prior GitHub and Vercel excerpt rows retain their original evidence. GB-month storage and paid marginal egress tiers exclude free allowances; full tier schedule retained in candidate.",
    }
    write_json(directory / "book.json", book)
    write_json(
        directory / "lock.json",
        {
            "version": "expanded-1",
            "book_digest": digest(book),
            "candidate_digest": digest(source),
            "prior_book_digest": prior.digest,
            "run_url": "https://github.com/mekala27-45/mlspend/actions/runs/41259427895",
            "review": "Checked Azure meter, region, tier and term; combined AWS upfront plus recurring dimensions per offer; checked OpenAI Standard short-context table order against the published page.",
        },
    )
    print({"prices": len(rows), "book_digest": digest(book)})


if __name__ == "__main__":
    promote()

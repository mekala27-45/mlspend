from __future__ import annotations

import calendar
import json
from collections.abc import Iterable
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import duckdb

from packages.core.io import ROOT, read_json
from packages.prices.book import PriceBook

SCHEMA = read_json(ROOT / "config/focus/1.4-columns.json")["datasets"]
UNITS = {"hour": "Hours", "gb_month": "GB-Months", "gb": "GB", "million_tokens": "1000000 Tokens"}


def utc(value: datetime) -> str:
    if value.tzinfo is None:
        raise ValueError("A FOCUS timestamp needs a timezone")
    return value.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def period(timestamp: str) -> tuple[str, str]:
    dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    start = dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return utc(start), utc(start + timedelta(days=calendar.monthrange(dt.year, dt.month)[1]))


def cost_row(observed: dict[str, Any], book: PriceBook) -> dict[str, Any]:
    price = book.get(observed["price_id"])
    timestamp = datetime.fromisoformat(observed["timestamp"])
    start, end = period(observed["timestamp"])
    cost = Decimal(observed["cost_micro"]) / 1000000
    quantity = Decimal(str(observed["pricing_quantity"]))
    list_price = Decimal(str(observed.get("list_unit_price", price.usd)))
    unit = UNITS.get(price.unit, price.unit)
    purchase = observed.get("charge_category") == "Purchase"
    unused = bool(observed.get("contract_id")) and observed["kind"] == "idle"
    row: dict[str, Any] = {
        key: None
        for key, spec in SCHEMA["CostAndUsage"].items()
        if spec["nullable"] or spec["level"] == "Mandatory"
    }
    row.update(
        BilledCost=str(Decimal(observed.get("billed_micro", observed["cost_micro"])) / 1000000),
        BillingAccountId="simulated-platform",
        BillingAccountName="MLSpend simulated platform",
        BillingAccountType="Billing Account",
        BillingCurrency="USD",
        BillingPeriodStart=start,
        BillingPeriodEnd=end,
        ChargeCategory=observed.get("charge_category", "Usage"),
        ChargeClass=None,
        ChargeDescription=f"Simulated {observed['service']} usage",
        ChargeFrequency="One-Time" if purchase else "Usage-Based",
        ChargePeriodStart=utc(timestamp),
        ChargePeriodEnd=utc(timestamp + timedelta(hours=1)),
        ConsumedQuantity=None if purchase or unused else str(quantity),
        ConsumedUnit=None if purchase or unused else unit,
        ContractedCost=str(list_price * quantity),
        ContractedUnitPrice=str(list_price),
        EffectiveCost=str(cost),
        HostProviderName=price.provider,
        InvoiceId="simulated-" + timestamp.strftime("%Y-%m"),
        InvoiceIssuerName=price.provider,
        ListCost=str(list_price * quantity),
        ListUnitPrice=str(list_price),
        PricingCategory="Standard",
        PricingCurrency="USD",
        PricingCurrencyContractedUnitPrice=str(list_price),
        PricingCurrencyListUnitPrice=str(list_price),
        PricingCurrencyEffectiveCost=str(cost),
        PricingQuantity=str(quantity),
        PricingUnit=unit,
        RegionId=price.region,
        RegionName=price.region,
        ResourceId=observed["resource"],
        ResourceName=observed["resource"],
        ResourceType=observed["service"],
        ServiceCategory={
            "storage": "Storage",
            "network": "Networking",
            "vector": "Databases",
            "llm": "AI and Machine Learning",
        }.get(observed["service"], "Compute"),
        ServiceName=observed["service"],
        ServiceProviderName=price.provider,
        ServiceSubcategory="Other ("
        + {
            "storage": "Storage",
            "network": "Networking",
            "vector": "Databases",
            "llm": "AI and Machine Learning",
        }.get(observed["service"], "Compute")
        + ")",
        SkuId=price.sku,
        SkuMeter=price.service + " Usage",
        SkuPriceId=price.id,
        SubAccountId=observed["team"],
        SubAccountName=observed["team"],
        SubAccountType="Project",
        Tags=json.dumps({"Team": observed["team"], "Model": observed.get("model", "shared")}),
        x_ChargeId=observed["id"],
        x_PriceSourceDigest=price.source_digest,
        x_Simulation=True,
        x_CostKind=observed["kind"],
    )
    if observed.get("contract_id"):
        contract = observed["contract_id"]
        row.update(
            CommitmentDiscountCategory="Usage",
            CommitmentDiscountId=contract,
            CommitmentDiscountName="Simulated one-year capacity reservation",
            CommitmentDiscountQuantity=str(quantity),
            CommitmentDiscountUnit=unit,
            CommitmentDiscountStatus=None if purchase else ("Unused" if unused else "Used"),
            CommitmentDiscountType="Reserved Instance",
            PricingCategory="Committed",
            ContractApplied=json.dumps(
                {
                    "Elements": [
                        {
                            "ContractId": contract,
                            "ContractCommitmentId": contract,
                            "ContractCommitmentAppliedCost": float(cost),
                            "ContractCommitmentAppliedQuantity": float(quantity),
                            "ContractCommitmentAppliedUnit": unit,
                        }
                    ]
                }
            ),
        )
        if purchase or unused:
            row["ResourceId"] = contract
    if observed.get("allocated_ratio") is not None:
        row.update(
            AllocatedMethodId="mlspend-usage-v2",
            AllocatedResourceId=observed["team"],
            AllocatedResourceName=observed["team"],
            AllocatedTags=json.dumps({"Team": observed["team"]}),
            AllocatedMethodDetails=json.dumps(
                {
                    "Elements": [
                        {"AllocatedRatio": observed["allocated_ratio"], "UsageUnit": "usage_share"}
                    ],
                    "x_OriginId": observed["origin_id"],
                }
            ),
        )
    return row


def contract_row(
    identifier: str, price_id: str, book: PriceBook, capacity: int = 1
) -> dict[str, Any]:
    reserved = book.get(price_id + "-reserved-1y")
    ondemand = book.get(price_id)
    cost = reserved.usd * 8760 * capacity
    row: dict[str, Any] = {
        key: None
        for key, spec in SCHEMA["ContractCommitment"].items()
        if spec["nullable"] or spec["level"] == "Mandatory"
    }
    row.update(
        BillingCurrency="USD",
        InvoiceIssuerName=reserved.provider,
        ServiceProviderName=reserved.provider,
        ContractId=identifier,
        ContractCommitmentId=identifier,
        ContractPeriodStart="2025-01-01T00:00:00Z",
        ContractPeriodEnd="2026-01-01T00:00:00Z",
        ContractCommitmentPeriodStart="2025-01-01T00:00:00Z",
        ContractCommitmentPeriodEnd="2026-01-01T00:00:00Z",
        ContractCommitmentCreated="2025-01-01T00:00:00Z",
        ContractCommitmentLastUpdated="2025-01-01T00:00:00Z",
        ContractCommitmentCategory="Usage",
        ContractCommitmentType="Reserved Instance",
        ContractCommitmentDescription="Simulated contract at a locked public offer; no purchase was made",
        ContractCommitmentCost=str(cost),
        ContractCommitmentQuantity=str(8760 * capacity),
        ContractCommitmentUnit="Hours",
        ContractCommitmentApplicability=json.dumps(
            {
                "InclusionOperator": "And",
                "Inclusions": [
                    {"Dimension": "SkuId", "Operator": "In", "Values": [ondemand.sku]},
                    {"Dimension": "RegionId", "Operator": "In", "Values": [ondemand.region]},
                ],
            }
        ),
        ContractCommitmentBenefitCategory="Discount",
        ContractCommitmentDiscountPercentage=str(1 - reserved.usd / ondemand.usd),
        ContractCommitmentDurationType="1 Year",
        ContractCommitmentFulfillmentInterval="Hourly",
        ContractCommitmentLifecycleStatus="Active",
        ContractCommitmentModel="Continuous",
        ContractCommitmentOfferCategory="Public",
        ContractCommitmentPaymentInterval="One-Time",
        ContractCommitmentPaymentModel="All Upfront",
        x_Simulation=True,
        x_PriceSourceDigest=reserved.source_digest,
    )
    return row


def validate_rows(rows: Iterable[dict[str, Any]], dataset: str) -> int:
    """Additional typed contracts. Official validator results are reported separately."""
    count = 0
    specs = SCHEMA[dataset]
    for row in rows:
        count += 1
        for name, spec in specs.items():
            if name not in row:
                if spec["level"] == "Mandatory":
                    raise ValueError(f"Missing mandatory column {name}")
                continue
            value = row[name]
            if value is None:
                if not spec["nullable"]:
                    raise ValueError(f"Null forbidden in {name}")
                continue
            if spec["type"] == "Decimal" and not Decimal(str(value)).is_finite():
                raise ValueError(f"Non-finite amount in {name}")
            if spec["type"] == "String" and (not isinstance(value, str) or not value.strip()):
                raise ValueError(f"Invalid string in {name}")
            if spec["type"] == "JSON" and not isinstance(json.loads(value), dict):
                raise ValueError(f"Invalid JSON object in {name}")
            if spec["type"] == "Date/Time":
                dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
                if dt.utcoffset() != timedelta(0):
                    raise ValueError(f"Timestamp must use UTC: {name}")
        if dataset == "ContractCommitment":
            if (
                row["ContractCommitmentModel"] == "Continuous"
                and row["ContractCommitmentFulfillmentInterval"] == "Full Period"
            ):
                raise ValueError("Continuous commitment cannot have full-period fulfillment")
            discount = row["ContractCommitmentDiscountPercentage"]
            if row["ContractCommitmentBenefitCategory"] == "Discount" and discount is None:
                raise ValueError("Discount contract requires discount percentage")
            if discount is not None and not 0 <= Decimal(discount) <= 1:
                raise ValueError("Discount percentage outside zero to one")
            scope = json.loads(row["ContractCommitmentApplicability"])
            if scope.get("IsGlobalScope") and scope.get("IsComplexScope"):
                raise ValueError("Conflicting applicability scopes")
            if not (scope.get("IsGlobalScope") or scope.get("IsComplexScope")) and not scope.get(
                "Inclusions"
            ):
                raise ValueError("Applicability scope has no inclusions")
        else:
            category, status = row["ChargeCategory"], row["CommitmentDiscountStatus"]
            if category != "Usage" or status == "Unused":
                if row["ConsumedQuantity"] is not None or row["ConsumedUnit"] is not None:
                    raise ValueError("Purchase or unused commitment cannot report consumption")
            if row["CommitmentDiscountId"] is None and status is not None:
                raise ValueError("Discount status without a discount identifier")
            if (
                row["CommitmentDiscountId"]
                and category == "Usage"
                and status not in {"Used", "Unused"}
            ):
                raise ValueError("Usage discount requires used or unused status")
            if category == "Purchase" and row["ChargeFrequency"] == "Usage-Based":
                raise ValueError("Purchase cannot have usage-based frequency")
            if row["ContractApplied"] is not None:
                elements = json.loads(row["ContractApplied"])["Elements"]
                if not elements or any(
                    not e.get("ContractId") or not e.get("ContractCommitmentId") for e in elements
                ):
                    raise ValueError("Contract application requires identifiers")
                if category == "Purchase" or status == "Unused":
                    if any(e["ContractCommitmentId"] != row["ResourceId"] for e in elements):
                        raise ValueError(
                            "Commitment purchase or unused resource must identify contract"
                        )
            if row["ChargePeriodStart"] >= row["ChargePeriodEnd"]:
                raise ValueError("Charge period must be positive")
            for field in ("ListCost", "ContractedCost"):
                price = row[field.replace("Cost", "UnitPrice")]
                if row["ChargeCategory"] == "Usage" and abs(
                    Decimal(row[field]) - Decimal(price) * Decimal(row["PricingQuantity"])
                ) > Decimal("0.000001"):
                    raise ValueError(f"Price-times-quantity mismatch in {field}")
    if not count:
        raise ValueError("Empty FOCUS dataset")
    return count


def parquet(rows: Iterable[dict[str, Any]], path: Path, dataset: str) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    jsonl = path.with_suffix(".jsonl")
    count = 0
    columns: set[str] = set()
    with jsonl.open("w", encoding="utf-8", newline="\n") as stream:
        for row in rows:
            count += validate_rows([row], dataset)
            columns.update(row)
            stream.write(json.dumps(row, allow_nan=False) + "\n")
    if not count:
        raise ValueError("Empty FOCUS export")
    expressions = []
    for name in sorted(columns):
        kind = SCHEMA[dataset].get(name, {}).get("type")
        target = "DECIMAL(38,12)" if kind == "Decimal" else "VARCHAR"
        expressions.append(f'CAST("{name}" AS {target}) AS "{name}"')
    with duckdb.connect() as connection:
        types = ",".join("'" + name + "':'VARCHAR'" for name in sorted(columns))
        connection.execute(
            "CREATE TABLE source AS SELECT * FROM read_json(?, columns={"
            + types
            + "}, maximum_object_size=16777216)",
            [str(jsonl)],
        )
        sql = "SELECT " + ",".join(expressions) + " FROM source"
        connection.sql(sql).write_parquet(str(path))
    jsonl.unlink()
    return count

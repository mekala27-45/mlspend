"""Collect public price evidence. This command never promotes its own output."""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import httpx

from packages.core.io import ROOT, digest, write_json
from packages.prices.client import SourceClient


def azure(client: SourceClient) -> list[dict[str, Any]]:
    filters = [
        f"armSkuName eq '{sku}' and armRegionName eq 'eastus'"
        for sku in ["Standard_NC4as_T4_v3", "Standard_NC24ads_A100_v4", "Standard_NC6s_v3", "Standard_D4s_v5"]
    ] + [
        "serviceName eq 'Storage' and armRegionName eq 'eastus' and productName eq 'Blob Storage'",
        "serviceName eq 'Bandwidth' and armRegionName eq 'eastus'",
    ]
    rows = []
    for query in filters:
        url = "https://prices.azure.com/api/retail/prices?" + urlencode({"$filter": query, "api-version": "2023-01-01-preview"})
        seen: set[str] = set()
        while url:
            if url in seen:
                raise ValueError("Provider pagination cycle")
            seen.add(url)
            page = client.get(url)
            for raw in page["Items"]:
                if raw["currencyCode"] == "USD" and "Windows" not in raw["productName"] and raw["type"] != "DevTestConsumption":
                    rows.append({"source_url": url, "raw": raw, "source_row_digest": digest(raw)})
            url = page.get("NextPageLink")
    return rows


def aws(destination: Path) -> dict[str, Any]:
    url = "https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonEC2/current/us-east-1/index.csv"
    path = destination / "aws-ec2-us-east-1.csv"
    h = hashlib.sha256()
    with httpx.stream("GET", url, timeout=180, follow_redirects=True) as response:
        response.raise_for_status()
        with path.open("wb") as stream:
            for block in response.iter_bytes():
                h.update(block)
                stream.write(block)
    rows = []
    with path.open(encoding="utf-8", newline="") as stream:
        for _ in range(5):
            next(stream)
        reader = csv.DictReader(stream)
        for raw in reader:
            if raw.get("Instance Type") in {"g4dn.xlarge", "g6.xlarge", "p4d.24xlarge"} and raw.get("Operating System") == "Linux" and raw.get("Tenancy") == "Shared" and raw.get("Pre Installed S/W") == "NA" and raw.get("CapacityStatus", "Used") == "Used":
                rows.append(raw)
    if not rows:
        raise ValueError("AWS catalog returned no selected Linux shared capacity prices")
    return {"source_url": url, "response_sha256": h.hexdigest(), "raw_rows": rows}


def main() -> None:
    cache = ROOT / "tmp/expanded-price-evidence"
    cache.mkdir(parents=True, exist_ok=True)
    client = SourceClient(cache)
    result: dict[str, Any] = {"version": 1, "retrieved_at": datetime.now(UTC).isoformat(), "promotion_status": "review_required"}
    result["azure"] = azure(client)
    result["aws"] = aws(cache)
    pages = {}
    for key, url in {
        "openai": "https://developers.openai.com/api/docs/pricing.md",
        "github": "https://docs.github.com/en/billing/reference/actions-runner-pricing",
        "vercel": "https://vercel.com/docs/pricing/serverless-functions",
    }.items():
        response = httpx.get(url, timeout=90, follow_redirects=True)
        response.raise_for_status()
        (cache / (key + ".txt")).write_bytes(response.content)
        pages[key] = {"url": url, "sha256": hashlib.sha256(response.content).hexdigest(), "bytes": len(response.content)}
        if key == "openai":
            # Record candidate lines for human review, never guess the pricing tier.
            pages[key]["candidate_lines"] = [line for line in response.text.splitlines() if "gpt-6.1-terra" in line or "gpt-6-luna" in line]
    result["pages"] = pages
    write_json(ROOT / "results/expanded-price-candidate.json", result)
    print(json.dumps({"azure_rows": len(result["azure"]), "aws_rows": len(result["aws"]["raw_rows"]), "openai": pages["openai"]}))


if __name__ == "__main__":
    main()

from __future__ import annotations

import math
from datetime import datetime
from decimal import Decimal
from typing import Any

from packages.core.money import microdollars
from packages.prices.book import PriceBook


def price_job(repository: str, job: dict[str, Any], book: PriceBook) -> dict[str, Any]:
    """Price a complete job, rounding each job separately; unknown runners stay unpriced."""
    start, end = job.get("started_at"), job.get("completed_at")
    labels = set(job.get("labels", []))
    result: dict[str, Any] = {
        "repository": repository,
        "job_id": job["id"],
        "source_url": job["html_url"],
        "started_at": start,
        "completed_at": end,
        "labels": sorted(labels),
        "conclusion": job.get("conclusion"),
        "minutes": None,
        "cost_micro": None,
        "price_id": None,
    }
    if not start or not end:
        result["status"] = "not completed; not priced"
        return result
    elapsed = (datetime.fromisoformat(end) - datetime.fromisoformat(start)).total_seconds()
    if elapsed < 0:
        raise ValueError("Job ends before it starts")
    result["minutes"] = math.ceil(elapsed / 60)
    supported = {"ubuntu-latest", "ubuntu-24.04", "ubuntu-22.04", "ubuntu-20.04"}
    if "self-hosted" in labels or not labels.intersection(supported):
        result["status"] = "runner has no verified paid equivalent in this price book"
        return result
    price = book.get("github-linux", unit="minute")
    result.update(
        status="shadow cost at list price",
        price_id=price.id,
        price_read_on=str(price.retrieved_date),
        price_source=price.source_url,
        cost_micro=microdollars(price.usd * Decimal(result["minutes"])),
    )
    return result

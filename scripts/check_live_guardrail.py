"""Verify deployed simulation admission, replay, refusal and request identity."""

from __future__ import annotations

import json
import os
import time
import uuid
from datetime import UTC, datetime
from decimal import Decimal

import httpx

from packages.core.io import ROOT, write_json
from packages.prices.book import PriceBook


def main() -> None:
    base = os.environ.get("MLSPEND_API_BASE", "https://mlspend.vercel.app").rstrip("/")
    book = PriceBook(ROOT / "data/prices/expanded")
    with httpx.Client(base_url=base, timeout=30) as client:
        for _attempt in range(12):
            response = client.get("/health")
            if response.status_code == 200 and response.json().get("database") == "connected":
                break
            time.sleep(2)
        response.raise_for_status()
        assert response.json()["price_digest"] == book.digest
        response = client.post("/v1/simulation/budgets", json={"limit_usd": "100"})
        response.raise_for_status()
        budget = response.json()
        route = f"/v1/simulation/budgets/{budget['id']}/admissions"
        request = {
            "request_id": str(uuid.uuid4()),
            "price_id": "azure-t4",
            "gpu_count": 1,
            "hours": "1",
            "attempts": 1,
        }
        accepted = client.post(route, json=request)
        assert accepted.status_code == 200
        first = accepted.json()
        expected = int(book.get("azure-t4").usd * Decimal(1000000))
        assert first["accepted"] and not first["replayed"] and first["forecast_micro"] == expected
        replay = client.post(route, json=request)
        assert replay.status_code == 200 and replay.json() == {**first, "replayed": True}
        mismatch = client.post(route, json={**request, "hours": "2"})
        assert mismatch.status_code == 409 and "different job" in mismatch.json()["detail"]
        sweep = {
            "request_id": str(uuid.uuid4()),
            "price_id": "azure-a100",
            "gpu_count": 8,
            "hours": "48",
            "attempts": 3,
        }
        refused = client.post(route, json=sweep)
        assert refused.status_code == 409 and not refused.json()["accepted"]
        assert refused.json()["remaining_after_micro"] == 100000000 - expected
        output = {
            "status": "pass",
            "recorded_at": datetime.now(UTC).isoformat(),
            "base_url": base,
            "source_commit": os.environ.get("GITHUB_SHA"),
            "budget_id": budget["id"],
            "accepted_request": request["request_id"],
            "refused_request": sweep["request_id"],
            "expected_reserved_micro": expected,
            "accepted": first,
            "refused": refused.json(),
            "replay": "same decision, no duplicate reservation",
            "changed_payload": "refused",
        }
        write_json(ROOT / "results/stretch/live-guardrail.json", output)
        print(json.dumps(output))


if __name__ == "__main__":
    main()

"""Check the public deployment and save one clearly identified smoke-test estimate."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen


def exchange(url: str, payload: dict[str, Any] | None = None) -> tuple[Any, dict[str, str]]:
    body = json.dumps(payload).encode() if payload is not None else None
    request = Request(
        url,
        data=body,
        headers={"Content-Type": "application/json", "User-Agent": "mlspend-hosted-check/1"},
        method="POST" if body is not None else "GET",
    )
    # POST is intentionally attempted once: a lost response does not imply a failed commit.
    with urlopen(request, timeout=45) as response:  # noqa: S310
        assert response.status == 200, f"Unexpected HTTP status for {url}"
        raw = response.read(2_000_000)
        headers = {key.lower(): value for key, value in response.headers.items()}
    if "application/json" in headers.get("content-type", ""):
        return json.loads(raw), headers
    return raw.decode("utf-8"), headers


def verify(base: str) -> dict[str, Any]:
    assert base.startswith("https://"), "Use the HTTPS deployment URL"
    base = base.rstrip("/")
    root = Path(__file__).resolve().parents[1]
    manifest = json.loads((root / "results/expanded/manifest.json").read_text(encoding="utf-8"))
    health, _ = exchange(base + "/health")
    assert health["status"] == "ready" and health["database"] == "connected"
    assert health["data_digest"] == manifest["generation"]["observed_sha256"]
    checks = []
    for route, key in [("showback", "rows"), ("unit-costs", "rows"), ("anomalies", "results")]:
        result, headers = exchange(base + "/v1/" + route)
        assert result[key], f"Empty {route} response"
        assert result["statement"] == manifest["statement"]
        assert Decimal(headers["x-shadow-cost-usd"]) >= 0
        checks.append(route)
    payload = {
        "price_id": "azure-t4",
        "requests_per_day": 17,
        "seconds_per_request": "0.1",
        "capacity_per_replica": 1,
        "minimum_replicas": 1,
        "days": 1,
    }
    estimate, headers = exchange(base + "/v1/estimate", payload)
    price = next(
        p
        for p in json.loads((root / "data/prices/expanded/book.json").read_text())["rows"]
        if p["id"] == payload["price_id"]
    )
    assert Decimal(estimate["shadow_cost_usd"]) == Decimal(price["usd"]) * 24
    identifier = estimate["id"]
    # A separate HTTP exchange proves the result is retrievable after the POST completed.
    recovered, _ = exchange(base + "/v1/estimates/" + identifier)
    row = recovered["estimate"]
    assert row["id"] == identifier and row["kind"] == "estimate"
    assert all(json.loads(row["payload"])[key] == value for key, value in payload.items())
    assert json.loads(row["result"])["shadow_cost_usd"] == estimate["shadow_cost_usd"]
    return {
        "checked_at": datetime.now(UTC).isoformat(),
        "base_url": base,
        "status": "passed",
        "checks": [
            "database health",
            *checks,
            "estimate POST and independent GET",
        ],
        "estimate_id": identifier,
        "estimate_payload": payload,
        "shadow_cost_usd": estimate["shadow_cost_usd"],
        "request_meter_usd": headers["x-shadow-cost-usd"],
        "data_digest": health["data_digest"],
        "price_digest": health["price_digest"],
        "limits": "HTTP checks only; browser rendering and provider billing are not verified here.",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="https://mlspend.vercel.app")
    parser.add_argument("--output", default="results/hosted-validation.json")
    args = parser.parse_args()
    evidence = verify(args.url)
    destination = Path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(evidence, indent=2))

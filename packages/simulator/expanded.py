"""Independent demand draws and re-runnable interventions for the amended study."""

from __future__ import annotations

import calendar
import gzip
import hashlib
import json
import math
from collections import defaultdict
from collections.abc import Iterator
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

from packages.core.io import ROOT, canonical, digest, file_digest, read_json, write_json
from packages.core.money import microdollars
from packages.prices.book import PriceBook

ACTIONS = (
    "rightsize",
    "spot",
    "remove_floor",
    "tier_storage",
    "deduplicate",
    "stop_notebook",
    "switch_model",
)


def noise(seed: int, hour: int, team: str, purpose: str) -> float:
    """Keyed draws ensure an intervention never shifts another workload's random stream."""
    value = hashlib.sha256(f"{seed}:{hour}:{team}:{purpose}".encode()).digest()
    return int.from_bytes(value[:8], "big") / 2**64


def protocol() -> dict[str, Any]:
    plan: dict[str, Any] = read_json(ROOT / "evaluation/v2/plan.json")
    if digest(plan) != read_json(ROOT / "evaluation/v2/registration.json")["plan_digest"]:
        raise ValueError("Amended protocol drift")
    return plan


def simulate(
    book: PriceBook,
    actions: frozenset[str] = frozenset(),
    hours: int | None = None,
    incident_override: list[dict[str, Any]] | None = None,
) -> Iterator[dict[str, Any]]:
    plan = protocol()
    incidents = (
        incident_override
        if incident_override is not None
        else read_json(ROOT / "config/expanded-incidents.json")
    )
    incidents = [
        {
            **r,
            "begin": datetime.fromisoformat(r["start"]),
            "finish": datetime.fromisoformat(r["end"]),
        }
        for r in incidents
    ]
    start = datetime.fromisoformat(plan["start"] + "T00:00:00+00:00")
    count = int(
        (datetime.fromisoformat(plan["end_exclusive"] + "T00:00:00+00:00") - start).total_seconds()
        / 3600
    )
    if hours is not None:
        count = min(count, hours)
    rates = {p.id: p for p in sorted(book.rows, key=lambda p: p.effective_date)}
    for hour in range(count):
        timestamp = start + timedelta(hours=hour)
        month_hours = calendar.monthrange(timestamp.year, timestamp.month)[1] * 24
        pool_units: dict[str, float] = defaultdict(float)
        index = 0

        def row(
            team: str,
            service: str,
            resource: str,
            price_id: str,
            quantity: float,
            kind: str = "workload",
            hour: int = hour,
            timestamp: datetime = timestamp,
            **extra: Any,
        ) -> dict[str, Any]:
            nonlocal index
            index += 1
            price = rates[price_id]
            owner_missing = noise(plan["seed"], hour, team, resource + "owner") < 0.14 or (
                team == "fraud"
                and any(
                    r["kind"] == "untagged_batch" and r["begin"] <= timestamp < r["finish"]
                    for r in incidents
                )
            )
            owner = "unallocated" if owner_missing and team != "shared" else team
            namespace = (
                team if noise(plan["seed"], hour, team, resource + "metadata") > 0.06 else "unknown"
            )
            return {
                "id": f"v2-{hour}-{index}",
                "timestamp": timestamp.isoformat(),
                "team": owner,
                "namespace": namespace,
                "network": "net-" + namespace,
                "resource": resource,
                "model": team + "-" + service + ("-v1" if timestamp.month < 7 else "-v2"),
                "service": service,
                "price_id": price_id,
                "sku": price.sku,
                "pricing_quantity": round(quantity, 9),
                "cost_micro": microdollars(price.usd * Decimal(str(round(quantity, 9)))),
                "kind": kind,
                "requests": 0,
                "requested": 0.0,
                "used": 0.0,
                **extra,
            }

        active: set[str] = set()
        for team_index, team in enumerate(plan["teams"]):
            active = {
                r["kind"]
                for r in incidents
                if r["team"] == team and r["begin"] <= timestamp < r["finish"]
            }
            weekly = 1.0 if timestamp.weekday() < 5 else 0.62
            demand = (
                (0.7 + 0.35 * math.sin((timestamp.hour - 8) / 24 * 2 * math.pi + team_index / 3))
                * weekly
                * (1 + hour / (8760 * 4))
            )
            demand *= 0.94 + 0.12 * noise(plan["seed"], hour, team, "demand")
            pool = ("azure-t4", "azure-a100", "azure-v100")[team_index % 3]
            if "sku_change" in active:
                pool = "azure-v100"
            used = demand * (0.7 + team_index / 10)
            requested = math.ceil(used * 1.9 * 4) / 4
            floor = 6.0 if "replica_floor" in active else 0.0
            if "rightsize" in actions:
                requested = (
                    math.ceil(used * plan["recommendations"]["rightsizing_headroom"] * 4) / 4
                )
            if "remove_floor" in actions:
                floor = 0
            units = max(used, requested, floor)
            pool_units[pool] += units
            yield row(
                team,
                "inference",
                team + "-endpoint",
                pool,
                units,
                requested=max(requested, floor),
                used=round(used, 6),
                requests=int(demand * 18000),
                minimum_replicas=floor,
                pool=pool,
                quality=0.94,
            )

            training = demand * 0.5
            retries = 0
            if "retry_sweep" in active:
                retries += 12
            if "spot_retry" in active:
                retries += 5
            if "untagged_batch" in active:
                training += 8
            spot = "spot" in actions or "spot_retry" in active
            if (
                spot
                and noise(plan["seed"], hour, team, "interruption")
                < plan["recommendations"]["spot_retry_probability"]
            ):
                retries += 1
            train_price = pool + "-spot" if spot else pool
            units = training * (1 + retries)
            if not spot:
                pool_units[pool] += units
            yield row(
                team,
                "training",
                team + "-training",
                train_price,
                units,
                requested=units,
                used=units * 0.9,
                pool=pool,
                run_id=f"{team}-run-{hour}",
                experiment_id=f"{team}-experiment-{hour // 24}",
                retries=retries,
                completed_runs=1,
                failed_runs=retries,
                training_base_hours=training,
                spot_eligible=True,
            )

            for service, multiplier in (("cpu", 0.18), ("vector", 0.12), ("warehouse", 0.2)):
                quantity = demand * multiplier
                yield row(
                    team,
                    service,
                    team + "-" + service,
                    "azure-cpu",
                    quantity,
                    requested=quantity,
                    used=quantity * 0.72,
                    requests=int(demand * 18000) if service == "cpu" else 0,
                    mapping="Dedicated self-hosted service priced as D4s v5 node-hours; not a managed-service quote",
                )

            stored_gb = 200 + team_index * 60 + hour / 20
            storage_price = (
                "azure-storage-cool"
                if "tier_storage" in actions and hour >= 30 * 24
                else "azure-storage-hot"
            )
            yield row(
                team,
                "storage",
                team + "-dataset",
                storage_price,
                stored_gb / month_hours,
                stored_gb=stored_gb,
                age_days=hour // 24,
                last_access_age_days=hour // 24,
                content_id=f"dataset-{team}",
                duplicate=False,
            )
            if "duplicate_storage" in active and "deduplicate" not in actions:
                yield row(
                    team,
                    "storage",
                    team + "-dataset-copy",
                    "azure-storage-hot",
                    stored_gb / month_hours,
                    stored_gb=stored_gb,
                    age_days=hour // 24,
                    last_access_age_days=hour // 24,
                    content_id=f"dataset-{team}",
                    duplicate=True,
                )
            egress_gb = demand * 0.5 + (700 if "egress" in active else 0)
            yield row(
                team,
                "network",
                team + "-export",
                "azure-egress",
                egress_gb,
                egress_gb=egress_gb,
                mapping="Paid marginal tier after account-level allowance; no free-tier billing claim",
            )

            answers = max(1, int(demand * 240))
            cached = int(answers * 1000 * 0.3)
            token_in, token_out = answers * 1000 - cached, answers * 150
            alternative_quality = 0.92 if team != "fraud" else 0.84
            model = (
                "gpt-6-luna"
                if "switch_model" in actions
                and alternative_quality >= plan["recommendations"]["minimum_quality"]
                else "gpt-6.1-terra"
            )
            for direction, tokens in (
                ("input", token_in),
                ("cached", cached),
                ("output", token_out),
            ):
                yield row(
                    team,
                    "llm",
                    team + "-answers-" + direction,
                    "openai-" + model + "-" + direction,
                    tokens / 1000000,
                    requests=answers if direction == "output" else 0,
                    tokens=tokens,
                    token_kind=direction,
                    quality=alternative_quality if model == "gpt-6-luna" else 0.95,
                    alternative_quality=alternative_quality,
                    quality_basis="Simulated task pass rate; not an observed provider benchmark",
                )

            if team == "research":
                idle_hours = (
                    (
                        timestamp
                        - next(
                            (r["begin"] for r in incidents if r["kind"] == "idle_notebook"),
                            timestamp,
                        )
                    ).total_seconds()
                    / 3600
                    if "idle_notebook" in active
                    else 0
                )
                notebook = 1.0 if 8 <= timestamp.hour <= 17 and timestamp.weekday() < 5 else 0.0
                if "idle_notebook" in active:
                    notebook = 1.0
                if (
                    "stop_notebook" in actions
                    and idle_hours >= plan["recommendations"]["idle_notebook_timeout_hours"]
                ):
                    notebook = 0
                pool_units["azure-a100"] += notebook
                yield row(
                    team,
                    "notebook",
                    "research-notebook",
                    "azure-a100",
                    notebook,
                    requested=notebook,
                    used=0.5 if idle_hours == 0 else 0,
                    idle_hours=idle_hours,
                    pool="azure-a100",
                )

        active = set()
        for pool, used_units in sorted(pool_units.items()):
            # Autoscaling acquires whole nodes. Idle is explicit before any overhead split.
            asset_units = max(4, math.ceil(used_units))
            idle = asset_units - used_units
            yield row(
                "shared",
                "capacity",
                "pool-" + pool,
                pool,
                idle,
                "idle",
                pool=pool,
                asset_units=asset_units,
                allocated_units=used_units,
            )
        yield row(
            "shared",
            "platform",
            "platform-services",
            "azure-cpu",
            2,
            "shared",
            mapping="Two simulated D4s v5 node-hours for scheduler and observability",
        )
        # One separately tracked reservation is unused. Its purchase is billed once;
        # every hourly amortization has effective cost and zero additional billed cost.
        yield row(
            "shared",
            "capacity",
            "simulated-t4-contract",
            "azure-t4-reserved-1y",
            1,
            "idle",
            pool="reserved-t4",
            contract_id="simulated-t4-contract",
            billed_micro=0,
            list_unit_price=str(rates["azure-t4"].usd),
        )
        if hour == 0:
            yield row(
                "shared",
                "capacity",
                "simulated-t4-contract",
                "azure-t4-reserved-1y",
                8760,
                "purchase",
                contract_id="simulated-t4-contract",
                charge_category="Purchase",
                cost_micro=0,
                billed_micro=microdollars(rates["azure-t4-reserved-1y"].usd * 8760),
                list_unit_price=str(rates["azure-t4-reserved-1y"].usd),
            )


def generate(destination: Path, hours: int | None = None) -> dict[str, Any]:
    plan = protocol()
    book = PriceBook(ROOT / "data/prices/expanded")
    destination.mkdir(parents=True, exist_ok=True)
    totals: dict[str, int] = defaultdict(int)
    owners: dict[str, str] = {}
    count = 0
    path = destination / "observed.jsonl.gz"
    with (
        path.open("wb") as raw,
        gzip.GzipFile(fileobj=raw, filename="", mode="wb", mtime=0) as stream,
    ):
        for row in simulate(book, hours=hours):
            count += 1
            totals[row["timestamp"][:7]] += row["cost_micro"]
            if row["team"] == "unallocated":
                owners[row["resource"]] = next(
                    (team for team in plan["teams"] if row["resource"].startswith(team)), "shared"
                )
            stream.write(canonical(row))
    result = {
        "rows": count,
        "hours": hours or 8760,
        "seed": plan["seed"],
        "plan_digest": digest(plan),
        "price_digest": book.digest,
        "observed_sha256": file_digest(path),
        "monthly_micro": dict(totals),
        "total_micro": sum(totals.values()),
        "price_basis": plan["price_basis"],
    }
    write_json(destination / "generation.json", result)
    write_json(destination / "sealed/owners.json", owners)
    write_json(
        destination / "sealed/incidents.json", read_json(ROOT / "config/expanded-incidents.json")
    )
    return result


def read_observed(path: Path) -> Iterator[dict[str, Any]]:
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        for line in stream:
            yield json.loads(line)

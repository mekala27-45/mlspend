from __future__ import annotations

import gzip
import math
import random
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

from packages.core.io import ROOT, canonical, digest, file_digest, read_json, write_json
from packages.core.money import microdollars
from packages.prices.book import PriceBook


def generate(destination: Path, days: int | None = None) -> dict[str, Any]:
    plan = read_json(ROOT / "evaluation/plan.json")
    if read_json(ROOT / "evaluation/registration.json")["plan_digest"] != digest(plan):
        raise ValueError("Evaluation plan is not registered")
    config = read_json(ROOT / "config/simulator.json")
    incidents = read_json(ROOT / "config/incidents.json")
    book = PriceBook()
    rng = random.Random(plan["seed"])
    start = datetime.fromisoformat(plan["start"] + "T00:00:00+00:00")
    end = datetime.fromisoformat(plan["end_exclusive"] + "T00:00:00+00:00")
    if days is not None:
        end = min(end, start + timedelta(days=days))
    destination.mkdir(parents=True, exist_ok=True)
    truth_rows: list[dict[str, Any]] = []
    counterfactuals = {i["id"]: 0 for i in incidents}
    observed_path = destination / "charges.jsonl.gz"
    telemetry_path = destination / "telemetry.jsonl.gz"
    row_count = 0
    total_micro = 0
    truth_owners: dict[str, str] = {}
    # Zero mtime and no embedded filename make compressed output reproducible.
    with observed_path.open("wb") as raw, telemetry_path.open("wb") as raw_t:
        with (
            gzip.GzipFile(filename="", fileobj=raw, mode="wb", mtime=0) as charge_stream,
            gzip.GzipFile(filename="", fileobj=raw_t, mode="wb", mtime=0) as telemetry_stream,
        ):
            timestamp = start
            while timestamp < end:
                current: list[dict[str, Any]] = []
                for team_index, team in enumerate(sorted(config["teams"])):
                    for model in range(config["models_per_team"]):
                        pool = ("t4", "a100", "cpu")[(team_index + model) % 3]
                        resource = f"{team}-{model}"
                        phase = (timestamp.hour - 8) / 24 * 2 * math.pi
                        weekly = 1.0 if timestamp.weekday() < 5 else 0.64
                        trend = 1 + (timestamp - start).days / 1600
                        usage = max(
                            0.03,
                            (0.30 + 0.20 * math.sin(phase + team_index / 3)) * weekly * trend
                            + rng.uniform(-0.035, 0.035),
                        )
                        request = math.ceil((0.40 + team_index * 0.04) * 4) / 4
                        active = [
                            i
                            for i in incidents
                            if i["team"] == team
                            and i["model"] == model
                            and datetime.fromisoformat(i["start"])
                            <= timestamp
                            < datetime.fromisoformat(i["end"])
                        ]
                        baseline = max(request, usage)
                        extra = sum(i["extra_units"] for i in active)
                        request += extra
                        if any(
                            i["kind"] in ("retry_sweep", "spot_retry", "untagged_batch")
                            for i in active
                        ):
                            usage += extra * 0.85
                        owner = (
                            team if rng.random() > config["untagged_probability"] else "unallocated"
                        )
                        if any(i["kind"] == "untagged_batch" for i in active):
                            owner = "unallocated"
                        requests = (
                            max(1, int((usage - extra * 0.85 if extra else usage) * 16000))
                            if model == 0
                            else 0
                        )
                        version = "v1" if timestamp.month < 7 else "v2"
                        row = {
                            "timestamp": timestamp.isoformat(),
                            "team": owner,
                            "resource": resource,
                            "model": f"{team}-model-{model}-{version}",
                            "kind": "inference" if model == 0 else "training",
                            "pool": pool,
                            "requested": round(request, 6),
                            "used": round(usage, 6),
                            "baseline": baseline,
                            "requests": requests,
                            "training_runs": int(model == 1 and timestamp.hour == 3),
                            "namespace": team if team_index % 3 else "shared",
                            "network": f"net-{team}" if team_index % 3 else "shared",
                            "active": active,
                        }
                        current.append(row)
                        truth_owners[resource] = team
                for pool, pool_config in sorted(config["pools"].items()):
                    members = [r for r in current if r["pool"] == pool]
                    demand = sum(max(r["requested"], r["used"]) for r in members)
                    nodes = max(pool_config["base_nodes"], math.ceil(demand))
                    price = book.get(pool_config["price_id"], timestamp.date(), "hour")
                    rate = price.usd
                    asset_micro = microdollars(rate * nodes)
                    direct = 0
                    for row in members:
                        cost = microdollars(Decimal(str(max(row["requested"], row["used"]))) * rate)
                        direct += cost
                        charge = _charge(
                            row["timestamp"],
                            row["team"],
                            row["resource"],
                            row["model"],
                            pool,
                            "workload",
                            cost,
                            price.id,
                        )
                        charge_stream.write(canonical(charge))
                        row_count += 1
                        total_micro += cost
                        telemetry = {
                            k: v for k, v in row.items() if k not in ("active", "baseline")
                        }
                        telemetry.update(cost_micro=cost, price_id=price.id, asset_nodes=nodes)
                        telemetry_stream.write(canonical(telemetry))
                        for incident in row["active"]:
                            without = max(
                                pool_config["base_nodes"],
                                math.ceil(demand - incident["extra_units"]),
                            )
                            incremental = microdollars(rate * (nodes - without))
                            counterfactuals[incident["id"]] += incremental
                            truth_rows.append(
                                {
                                    "timestamp": row["timestamp"],
                                    "incident_id": incident["id"],
                                    "team": incident["team"],
                                    "resource": row["resource"],
                                    "pool": pool,
                                    "incremental_asset_micro": incremental,
                                }
                            )
                    idle = asset_micro - direct
                    if idle < 0:
                        raise ValueError("Workload cost exceeds asset cost")
                    charge_stream.write(
                        canonical(
                            _charge(
                                timestamp.isoformat(),
                                "platform",
                                f"idle-{pool}",
                                "none",
                                pool,
                                "idle",
                                idle,
                                price.id,
                            )
                        )
                    )
                    row_count += 1
                    total_micro += idle
                shared = microdollars(
                    book.get("azure-cpu", timestamp.date(), "hour").usd * config["shared_cpu_nodes"]
                )
                charge_stream.write(
                    canonical(
                        _charge(
                            timestamp.isoformat(),
                            "platform",
                            "shared-services",
                            "none",
                            "cpu",
                            "shared",
                            shared,
                            "azure-cpu",
                        )
                    )
                )
                row_count += 1
                total_micro += shared
                timestamp += timedelta(hours=1)
    truth_dir = destination / "sealed"
    write_json(
        truth_dir / "truth.json",
        {
            "incidents": incidents,
            "incident_hours": truth_rows,
            "counterfactual_savings_micro": counterfactuals,
            "owners": truth_owners,
        },
    )
    manifest = {
        "seed": plan["seed"],
        "start": start.isoformat(),
        "end_exclusive": end.isoformat(),
        "hours": int((end - start).total_seconds() / 3600),
        "charge_rows": row_count,
        "total_micro": total_micro,
        "price_digest": book.digest,
        "config_digest": digest(config),
        "plan_digest": digest(plan),
        "charges_sha256": file_digest(observed_path),
        "telemetry_sha256": file_digest(telemetry_path),
        "truth_sha256": file_digest(truth_dir / "truth.json"),
        "price_basis": config["price_basis"],
        "focus_status": "candidate fields only; Foundation validation pending",
    }
    write_json(destination / "generation.json", manifest)
    return manifest


def _charge(
    timestamp: str,
    team: str,
    resource: str,
    model: str,
    pool: str,
    category: str,
    cost: int,
    price_id: str,
) -> dict[str, Any]:
    start = datetime.fromisoformat(timestamp)
    return {
        "ChargePeriodStart": timestamp,
        "ChargePeriodEnd": (start + timedelta(hours=1)).isoformat(),
        "BillingCurrency": "USD",
        "BilledCostMicro": cost,
        "EffectiveCostMicro": cost,
        "ChargeCategory": "Usage",
        "ServiceCategory": "Compute",
        "ServiceName": "Simulated ML platform",
        "ServiceProviderName": "Simulation",
        "BillingAccountId": "simulation",
        "ResourceId": resource,
        "RegionId": "eastus",
        "x_Team": team,
        "x_Model": model,
        "x_Pool": pool,
        "x_CostKind": category,
        "x_PriceId": price_id,
        "Tags": {"owner": team},
    }

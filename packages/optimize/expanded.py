"""Action estimates from observed telemetry, without access to sealed outcomes."""

from __future__ import annotations

import math
import random
from collections import defaultdict
from collections.abc import Iterable, Sequence
from decimal import Decimal
from statistics import mean
from typing import Any

from packages.allocation.shapley import quantile
from packages.core.money import microdollars
from packages.prices.book import PriceBook


def recommendations(
    rows: Iterable[dict[str, Any]], book: PriceBook, config: dict[str, Any], seed: int
) -> list[dict[str, Any]]:
    daily: dict[tuple[str, str], dict[str, int]] = defaultdict(lambda: defaultdict(int))
    dates: set[str] = set()
    eligibility: dict[tuple[str, str], str] = {}
    for row in rows:
        day = row["timestamp"][:10]
        dates.add(day)
        price = book.get(row["price_id"])
        resource, quantity = row["resource"], Decimal(str(row["pricing_quantity"]))
        proposed: dict[str, tuple[Decimal, str]] = {}
        if row["service"] == "inference":
            target = max(
                row.get("minimum_replicas", 0),
                math.ceil(row["used"] * config["rightsizing_headroom"] * 4) / 4,
            )
            proposed["rightsize"] = (
                price.usd * Decimal(str(max(0, row["requested"] - target))),
                "Observed utilization with registered headroom; cash savings depend on whole-node release",
            )
            if row.get("minimum_replicas", 0):
                normal = math.ceil(row["used"] * 1.9 * 4) / 4
                proposed["remove_floor"] = (
                    price.usd * Decimal(str(max(0, row["requested"] - normal))),
                    "Replica minimum exceeds observed demand and normal provisioning policy",
                )
        if (
            row["service"] == "training"
            and row.get("spot_eligible")
            and not row["price_id"].endswith("-spot")
        ):
            spot = book.get(row["price_id"] + "-spot")
            expected_hours = Decimal(str(row["training_base_hours"])) * Decimal(
                str(1 + row["retries"] + config["spot_retry_probability"])
            )
            proposed["spot"] = (
                price.usd * quantity - spot.usd * expected_hours,
                "Checkpointable simulated job; expected extra interrupted attempt included",
            )
        if row["service"] == "storage":
            if (
                row.get("last_access_age_days", 0) >= config["cold_after_days"]
                and row["price_id"] == "azure-storage-hot"
                and not row.get("duplicate")
            ):
                proposed["tier_storage"] = (
                    (price.usd - book.get("azure-storage-cool").usd) * quantity,
                    "No access during the registered cold-age window; synthetic trace has no retrieval requests",
                )
            if row.get("duplicate") and row.get("content_id"):
                proposed["deduplicate"] = (
                    price.usd * quantity,
                    "Observed copy shares its content identifier with the primary dataset",
                )
        if (
            row["service"] == "notebook"
            and row.get("idle_hours", 0) >= config["idle_notebook_timeout_hours"]
        ):
            proposed["stop_notebook"] = (
                price.usd * quantity,
                "Idle timeout exceeded; cash effect depends on released whole nodes",
            )
        if (
            row["service"] == "llm"
            and row.get("alternative_quality", 0) >= config["minimum_quality"]
        ):
            alternative = book.get("openai-gpt-6-luna-" + row["token_kind"])
            proposed["switch_model"] = (
                (price.usd - alternative.usd) * quantity,
                "Alternative passes registered simulated task-quality floor; no real model-quality claim",
            )
        for action, (amount, reason) in proposed.items():
            if amount > 0:
                key = action, resource
                daily[key][day] += microdollars(amount)
                eligibility[key] = reason
    rng = random.Random(seed)
    ordered_days = sorted(dates)
    result = []
    for (action, resource), values in sorted(daily.items()):
        amounts = [values.get(day, 0) for day in ordered_days]
        draws = [
            mean(rng.choices(amounts, k=len(amounts))) * len(amounts) / 12
            for _ in range(config["bootstrap_replicates"])
        ]
        alpha = (1 - config["interval_coverage"]) / 2
        result.append(
            {
                "action": action,
                "resource": resource,
                "estimated_annual_micro": sum(amounts),
                "estimated_monthly_micro": sum(amounts) / 12,
                "monthly_lower_micro": quantile(draws, alpha),
                "monthly_upper_micro": quantile(draws, 1 - alpha),
                "eligibility": eligibility[(action, resource)],
                "interval_kind": "day resampling of observed estimate, not a guarantee of counterfactual savings",
            }
        )
    return result


def commitment_cost(
    usage: Sequence[float], capacity: float, reserved: float, ondemand: float
) -> float:
    if not usage or min(capacity, reserved, ondemand, *usage) < 0:
        raise ValueError("Nonnegative nonempty commitment inputs required")
    return mean(capacity * reserved + max(0, u - capacity) * ondemand for u in usage)


def commitment(
    usage: Sequence[float],
    development_hours: int,
    candidates: Sequence[float],
    reserved: float,
    ondemand: float,
) -> dict[str, Any]:
    if not 0 < development_hours < len(usage) or len(candidates) < 3:
        raise ValueError("Development, holdout and interior candidates required")
    curve = [
        {
            "capacity": c,
            "development_cost_per_hour": commitment_cost(
                usage[:development_hours], c, reserved, ondemand
            ),
        }
        for c in candidates
    ]
    selected = min(curve, key=lambda r: (r["development_cost_per_hour"], r["capacity"]))["capacity"]
    held = usage[development_hours:]
    oracle = min(commitment_cost(held, c, reserved, ondemand) for c in candidates)
    variants = [
        {
            "multiplier": multiplier,
            "capacity": selected * multiplier,
            "heldout_cost_per_hour": commitment_cost(
                held, selected * multiplier, reserved, ondemand
            ),
            "regret_per_hour": commitment_cost(held, selected * multiplier, reserved, ondemand)
            - oracle,
        }
        for multiplier in (0.8, 1.0, 1.2)
    ]
    return {
        "selected_capacity": selected,
        "interior": min(candidates) < selected < max(candidates),
        "development_curve": curve,
        "heldout_oracle_cost_per_hour": oracle,
        "variants": variants,
        "pricing": {"reserved_per_hour": reserved, "ondemand_per_hour": ondemand},
        "unused_commitment_hours": sum(max(0, selected - u) for u in held),
        "overflow_hours": sum(max(0, u - selected) for u in held),
    }

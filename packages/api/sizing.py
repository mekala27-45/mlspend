"""Transparent workload sizing, with no inferred throughput or quality equivalence."""

from __future__ import annotations

import math
from decimal import Decimal
from typing import Any

from packages.core.contracts import EstimateRequest
from packages.prices.book import PriceBook


def alternatives(request: EstimateRequest, book: PriceBook) -> list[dict[str, Any]]:
    identifiers = {
        "small": [
            "azure-cpu",
            "azure-t4",
            "azure-a100",
            "azure-v100",
            "aws-g4dn.xlarge",
            "aws-g6.xlarge",
            "aws-p4d.24xlarge",
        ],
        "medium": [
            "azure-t4",
            "azure-a100",
            "azure-v100",
            "aws-g4dn.xlarge",
            "aws-g6.xlarge",
            "aws-p4d.24xlarge",
        ],
        "large": ["azure-a100", "aws-p4d.24xlarge"],
    }[request.model_size_class or "small"]
    result = []
    replicas = max(
        request.minimum_replicas,
        math.ceil(
            Decimal(request.requests_per_day)
            * request.seconds_per_request
            / (86400 * request.capacity_per_replica)
        ),
    )
    for identifier in identifiers:
        if request.hosting_option not in {"all", identifier.split("-")[0]}:
            continue
        price = book.get(identifier, unit="hour")
        result.append(
            {
                "option": identifier,
                "cost_usd": str(price.usd * replicas * 24 * request.days),
                "replicas": replicas,
                "price_rows": [price.model_dump(mode="json")],
                "assumptions": [
                    "Caller-supplied seconds and concurrency apply to this entire instance, not each GPU.",
                    "Class is a scenario filter, not a verified memory-fit or throughput benchmark.",
                    "Instance held for the entire period; storage, egress, interruptions and discounts excluded.",
                ],
            }
        )
    if request.hosting_option in {"all", "model_api"}:
        for model in ("openai-gpt-6.1-terra", "openai-gpt-6-luna"):
            prices = [
                book.get(model + "-" + kind, unit="million_tokens")
                for kind in ("input", "cached", "output")
            ]
            calls = Decimal(request.requests_per_day * request.days) / 1000000
            components = {
                "input": calls
                * request.tokens_in_per_request
                * (1 - request.cached_input_fraction)
                * prices[0].usd,
                "cached_input": calls
                * request.tokens_in_per_request
                * request.cached_input_fraction
                * prices[1].usd,
                "output": calls * request.tokens_out_per_request * prices[2].usd,
            }
            result.append(
                {
                    "option": model,
                    "cost_usd": str(sum(components.values())),
                    "components_usd": {k: str(v) for k, v in components.items()},
                    "price_rows": [p.model_dump(mode="json") for p in prices],
                    "assumptions": [
                        "Standard short-context published token rates, excluding tools and priority tiers.",
                        "A model API is not quality-equivalent to a self-hosted model; validate quality separately.",
                    ],
                }
            )
    return result

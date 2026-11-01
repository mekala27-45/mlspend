"""Classify recorded request timings without treating every follow-up as warm."""

from __future__ import annotations

import math
from typing import Any


def summarize_latency(evidence: dict[str, Any]) -> dict[str, Any]:
    seen = {evidence["idle"]["after_instance"]}
    reused: list[float] = []
    first_observations: list[dict[str, Any]] = []
    for sample in evidence["warm"]["samples"]:
        instance = sample["instance_id"]
        if instance in seen:
            reused.append(float(sample["ms"]))
        else:
            first_observations.append(
                {
                    "instance_id": instance,
                    "ms": sample["ms"],
                    "uptime_seconds": sample["process_uptime_seconds"],
                }
            )
        seen.add(instance)
    ordered = sorted(reused)
    return {
        "source": "results/live/browser.json",
        "checked_at": evidence["checked_at"],
        "sequence_count": len(evidence["warm"]["samples"]),
        "reused_instance_count": len(reused),
        "reused_instance_p50_ms": ordered[math.ceil(len(ordered) * 0.5) - 1] if ordered else None,
        "reused_instance_p99_ms": ordered[math.ceil(len(ordered) * 0.99) - 1] if ordered else None,
        "additional_first_observations": first_observations,
        "method": "Nearest-rank quantiles only for requests to previously observed instance IDs. First observations of other instances are excluded, regardless of request order.",
        "limit": "Includes network and database time. A reused process does not imply a warm database or cache; first observations alone do not establish startup latency.",
    }

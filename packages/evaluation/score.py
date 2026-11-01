from __future__ import annotations

from datetime import datetime
from pathlib import Path
from statistics import median
from typing import Any

from packages.truth.access import read_truth


def score_incidents(truth_path: Path, alerts: list[dict[str, Any]], start: str) -> dict[str, Any]:
    truth = read_truth(truth_path)
    events = [i for i in truth["incidents"] if i["start"][:10] >= start]
    points = {
        (r["timestamp"], r["resource"]): r
        for r in truth["incident_hours"]
        if r["timestamp"][:10] >= start
    }
    hits = [a for a in alerts if (a["timestamp"], a["resource"]) in points]
    rows = []
    for event in events:
        truth_hours = [row for row in truth["incident_hours"] if row["incident_id"] == event["id"]]
        matched = sorted(
            [
                a
                for a in hits
                if points[(a["timestamp"], a["resource"])]["incident_id"] == event["id"]
            ],
            key=lambda r: r["timestamp"],
        )
        first = matched[0]["timestamp"] if matched else None
        delay = (
            (datetime.fromisoformat(first) - datetime.fromisoformat(event["start"])).total_seconds()
            / 3600
            if first
            else None
        )
        burned = sum(
            r["incremental_asset_micro"]
            for r in truth_hours
            if first is None or r["timestamp"] <= first
        )
        rows.append(
            {
                **event,
                "first_alert": first,
                "delay_hours": delay,
                "burned_micro": burned,
                "true_savings_micro": truth["counterfactual_savings_micro"][event["id"]],
            }
        )
    delays = [r["delay_hours"] for r in rows if r["delay_hours"] is not None]
    return {
        "point_precision": len(hits) / len(alerts) if alerts else None,
        "event_recall": len(delays) / len(events) if events else None,
        "alert_hours": len(alerts),
        "true_alert_hours": len(hits),
        "median_delay_hours": median(delays) if delays else None,
        "burned_micro": sum(r["burned_micro"] for r in rows),
        "events": rows,
        "scoring_note": "Delay is censored for missed events; their entire incident cost is counted as burned.",
    }


def score_owners(truth_path: Path, predictions: dict[str, str]) -> dict[str, float | int | None]:
    truth = read_truth(truth_path)["owners"]
    assigned = {key: value for key, value in predictions.items() if value != "unallocated"}
    correct = sum(truth[key] == value for key, value in assigned.items())
    return {
        "precision": correct / len(assigned) if assigned else None,
        "recall": correct / len(predictions) if predictions else None,
        "assigned_resources": len(assigned),
        "unassigned_resources": len(predictions) - len(assigned),
    }

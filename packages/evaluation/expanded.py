from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from statistics import mean, median
from typing import Any

import duckdb

from packages.core.io import read_json
from packages.detect.expanded import alerts, residuals, select
from packages.evaluation.statistics import benjamini_hochberg, cluster_interval, sign_randomization

SERVICES = {
    "retry_sweep": "training",
    "replica_floor": "inference",
    "idle_notebook": "notebook",
    "spot_retry": "training",
    "egress": "network",
    "sku_change": "inference",
    "duplicate_storage": "storage",
    "untagged_batch": "training",
}


def overlaps(start: str, end: str, timestamp: str, grain: str) -> bool:
    """Intersect half-open incident and observation intervals, including partial days."""
    point = datetime.fromisoformat(timestamp)
    stop = point + (timedelta(days=1) if grain == "day" else timedelta(hours=1))
    return datetime.fromisoformat(start) < stop and point < datetime.fromisoformat(end)


def detection(directory: Path, plan: dict[str, Any], truth: dict[str, Any]) -> dict[str, Any]:
    incidents = read_json(directory / "sealed/incidents.json")
    cutoff = datetime.fromisoformat(plan["development_end_exclusive"] + "T00:00:00+00:00")
    found: dict[str, list[str]] = defaultdict(list)
    scorecards = []
    counts = {"tp": 0, "fp": 0, "fn": 0, "tn": 0}
    with duckdb.connect(str(directory / "warehouse.duckdb"), read_only=True) as connection:
        connection.execute("SET TimeZone='UTC'")
        groups = connection.execute(
            "SELECT DISTINCT owner,service,sku FROM owned WHERE owner <> 'shared' ORDER BY 1,2,3"
        ).fetchall()
        for owner, service, sku in groups:
            records = connection.execute(
                "SELECT timestamp,SUM(cost_micro)/1000000.0 FROM owned WHERE owner=? AND service=? AND sku=? GROUP BY 1 ORDER BY 1",
                [owner, service, sku],
            ).fetchall()
            if len(records) < 24 * 60:
                continue
            related = [
                r for r in incidents if r["team"] == owner and SERVICES[r["kind"]] == service
            ]
            for grain, season in (("hour", 168), ("day", 7)):
                series: dict[str, float] = defaultdict(float)
                for timestamp, value in records:
                    key = (
                        timestamp.isoformat()
                        if grain == "hour"
                        else timestamp.date().isoformat() + "T00:00:00+00:00"
                    )
                    series[key] += float(value)
                series_first, series_last = min(series), max(series)
                point, stop = (
                    datetime.fromisoformat(series_first),
                    datetime.fromisoformat(series_last),
                )
                step = timedelta(hours=1) if grain == "hour" else timedelta(days=1)
                # Missing hours inside an observed series are zero usage, never compressed time.
                while point <= stop:
                    series.setdefault(point.isoformat(), 0.0)
                    point += step
                times = sorted(series)
                values = [series[t] for t in times]
                labels = [
                    any(overlaps(r["start"], r["end"], t, grain) for r in related) for t in times
                ]
                normal = [
                    datetime.fromisoformat(t) < cutoff and not label
                    for t, label in zip(times, labels, strict=True)
                ]
                scores = residuals(values, season, plan["detector"]["seasonal_weeks"])
                if not any(n and s is not None for n, s in zip(normal, scores, strict=True)):
                    scorecards.append(
                        {
                            "team": owner,
                            "service": service,
                            "sku": sku,
                            "grain": grain,
                            "status": "unscored_no_development_history",
                        }
                    )
                    continue
                selected = select(scores, normal, plan["detector"])
                hits = alerts(
                    scores,
                    selected["threshold"],
                    selected["method"],
                    plan["detector"]["cusum_drift"],
                )
                local_counts = dict.fromkeys(counts, 0)
                for timestamp, label, hit in zip(times, labels, hits, strict=True):
                    if datetime.fromisoformat(timestamp) < cutoff:
                        continue
                    category = ("tp" if hit else "fn") if label else ("fp" if hit else "tn")
                    local_counts[category] += 1
                    counts[category] += 1
                    if hit and grain == "hour":
                        for incident in related:
                            if incident["start"] <= timestamp < incident["end"]:
                                found[incident["id"]].append(timestamp)
                scorecards.append(
                    {
                        "team": owner,
                        "service": service,
                        "sku": sku,
                        "grain": grain,
                        **selected,
                        **local_counts,
                    }
                )
    events = []
    for incident in incidents:
        if datetime.fromisoformat(incident["start"]) < cutoff:
            continue
        first = min(found[incident["id"]]) if found[incident["id"]] else None
        delay = (
            (
                datetime.fromisoformat(first) - datetime.fromisoformat(incident["start"])
            ).total_seconds()
            / 3600
            if first
            else None
        )
        burn = sum(
            max(0, cost)
            for hour, cost in truth["incident_hourly_micro"][incident["id"]].items()
            if incident["start"] <= hour < (first or incident["end"])
        )
        events.append(
            {
                **incident,
                "first_alert": first,
                "delay_hours": delay,
                "burned_before_detection_micro": burn,
                "counterfactual_avoidable_micro": truth["incident_avoidable_micro"][incident["id"]],
            }
        )
    delays = [r["delay_hours"] for r in events if r["delay_hours"] is not None]
    return {
        "series": scorecards,
        "events": events,
        "point_precision": counts["tp"] / (counts["tp"] + counts["fp"])
        if counts["tp"] + counts["fp"]
        else None,
        "point_recall": counts["tp"] / (counts["tp"] + counts["fn"])
        if counts["tp"] + counts["fn"]
        else None,
        "event_recall": len(delays) / len(events),
        "median_detected_delay_hours": median(delays) if delays else None,
        "missed_events": len(events) - len(delays),
        "burned_before_detection_micro": sum(r["burned_before_detection_micro"] for r in events),
        "counts": counts,
    }


def hypotheses(analysis: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    clusters: dict[str, dict[str, list[float]]] = {
        "allocation": defaultdict(list),
        "forecast": defaultdict(list),
    }
    for row in analysis["allocation"]:
        if row["month"] < "2025-09" or row["capacity_shapley_usd"] is None:
            continue
        # Compare alternative allocations of the same bill; standalone capacity dollars
        # are a different counterfactual and cannot be subtracted from fully loaded bills.
        reference = row["methods"]["shapley"]
        clusters["allocation"][row["team"]].append(
            (abs(row["methods"]["usage"] - reference) - abs(row["methods"]["even"] - reference))
            / 1000000
        )
    for series in analysis["forecasts"]:
        if series["grain"] == "team":
            clusters["forecast"][series["key"]] = [
                abs(r["actual"] - r["point"]) - abs(r["actual"] - r["naive"])
                for r in series["rows"]
            ]
    rows: dict[str, dict[str, Any]] = {}
    for name, values in clusters.items():
        if not values:
            continue
        cluster_means = [mean(v) for _, v in sorted(values.items())]
        interval = cluster_interval(
            values, config["bootstrap_seed"], config["bootstrap_replicates"]
        )
        rows[name] = {
            "mean_difference_usd": mean(cluster_means),
            "cluster_bootstrap_95": list(interval),
            "p_value": sign_randomization(cluster_means),
            "clusters": len(values),
            "direction": "Negative favors the registered method",
        }
    adjusted = (
        benjamini_hochberg({name: row["p_value"] for name, row in rows.items()}) if rows else {}
    )
    for name, row in rows.items():
        row["q_value"] = adjusted[name]
        row["significant"] = adjusted[name] <= config["fdr"]
    return rows

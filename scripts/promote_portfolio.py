"""Promote verified public Actions usage without turning missing usage into zero."""

from __future__ import annotations

import argparse
from pathlib import Path

from packages.core.io import ROOT, digest, read_json, write_json


def promote(evidence: Path, run_url: str, artifact_digest: str) -> None:
    report = read_json(evidence / "results/portfolio-usage.json")
    request = read_json(ROOT / "requests/portfolio.json")
    if report["request_digest"] != digest(request) or not report["rows"]:
        raise ValueError("Usage evidence does not match the committed request")
    jobs = report["jobs"]
    keys = [(row["repository"], row["job_id"]) for row in jobs]
    if len(keys) != len(set(keys)):
        raise ValueError("Duplicate workflow jobs would double count usage")
    for row in report["rows"]:
        subset = [job for job in jobs if job["repository"] == row["repository"]]
        priced = [job for job in subset if job["cost_micro"] is not None]
        if any(job["cost_micro"] < 0 for job in priced):
            raise ValueError("Negative shadow costs")
        if (
            row["jobs"] != len(subset)
            or row["priced_jobs"] != len(priced)
            or row["unpriced_jobs"] != len(subset) - len(priced)
            or row["shadow_cost_micro"] != sum(job["cost_micro"] for job in priced)
        ):
            raise ValueError("Repository summary does not reconcile to jobs")
    if report["priced_subtotal_micro"] != sum(row["shadow_cost_micro"] for row in report["rows"]):
        raise ValueError("Portfolio subtotal does not reconcile")
    destination = ROOT / "results/portfolio-usage.json"
    if destination.exists() and digest(read_json(destination)) != digest(report):
        raise ValueError("Existing usage evidence differs; create a new promotion version")
    write_json(destination, report)
    write_json(
        ROOT / "data/portfolio/lock.json",
        {
            "version": 1,
            "report_digest": digest(report),
            "run_url": run_url,
            "artifact_sha256": artifact_digest,
            "price_digest": report["price_digest"],
        },
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence", type=Path)
    parser.add_argument("--run-url", required=True)
    parser.add_argument("--artifact-digest", required=True)
    args = parser.parse_args()
    promote(args.evidence, args.run_url, args.artifact_digest)

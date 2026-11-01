"""Build the amended study without replacing any version-one results."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from packages.core.io import ROOT, STATEMENT, digest, write_json
from packages.evaluation.counterfactual import grade, rerun
from packages.evaluation.expanded import detection, hypotheses
from packages.evaluation.ownership import score as ownership_score
from packages.expansion.analysis import analyze
from packages.expansion.exports import export_all
from packages.optimize.expanded import recommendations
from packages.prices.book import PriceBook
from packages.simulator.expanded import generate, protocol
from packages.warehouse.expanded import ingest, read_mart


def run(
    hours: int | None = None,
    destination: Path = ROOT / "data/expanded",
    exports: Path = ROOT / "exports/expanded",
) -> dict[str, Any]:
    plan = protocol()
    book = PriceBook(ROOT / "data/prices/expanded")
    print("Generating independent expanded observations", flush=True)
    generation = generate(destination, hours)
    print("Ingesting, quarantining and reconciling", flush=True)
    reconciliation = ingest(destination, book)
    if hours is None:
        subprocess.run(
            [
                sys.executable,
                "-m",
                "dbt.cli.main",
                "build",
                "--project-dir",
                "warehouse-expanded",
                "--profiles-dir",
                "warehouse-expanded",
            ],
            cwd=ROOT,
            env={**os.environ, "MLSPEND_WAREHOUSE": str(destination / "warehouse.duckdb")},
            check=True,
        )
    print("Allocating capacity and scoring rolling forecasts", flush=True)
    analysis = analyze(destination, book, plan, forecasts=hours is None)
    print("Estimating observed-data recommendations", flush=True)
    proposals = recommendations(
        read_mart(destination, require_contract=hours is None),
        book,
        plan["recommendations"],
        plan["evaluation"]["bootstrap_seed"],
    )
    print("Rerunning every action and incident counterfactual", flush=True)
    truth = rerun(destination, hours)
    if truth["baseline"]["total_micro"] != generation["total_micro"]:
        raise AssertionError("Counterfactual baseline differs from observed generation")
    scores = grade(proposals, truth)
    detector = (
        detection(destination, plan, truth)
        if hours is None
        else {"status": "not_scored_in_development_smoke"}
    )
    statistics = hypotheses(analysis, plan["evaluation"])
    print("Writing FOCUS and finance exports", flush=True)
    exported = export_all(destination, exports, analysis, book, plan["teams"])
    manifest = {
        "schema_version": "expanded-1",
        "statement": STATEMENT,
        "mode": "full_year" if hours is None else "development_smoke",
        "generation": generation,
        "reconciliation": reconciliation,
        "ownership": ownership_score(destination),
        **analysis,
        "recommendations": scores,
        "detection": detector,
        "hypotheses": statistics,
        "exports": exported,
        "official_focus_validation": {
            "status": "separate_report_required",
            "target_version": "1.4",
            "usable_official_rules": "1.3.0.1",
            "upstream_1_4_rule_cycle": True,
        },
        "registration": {
            "plan_digest": digest(plan),
            "commit": "f55e9be4f98c27aa82ad6533fbc45d7483e1f9c0",
            "prior_results_known": True,
        },
    }
    output = ROOT / "results/expanded" if hours is None else destination / "results"
    write_json(output / "manifest.json", manifest)
    summary = {
        "mode": manifest["mode"],
        "generation": generation,
        "reconciliation": reconciliation,
        "action_scores": scores["actions"],
        "joint_recovered_micro": scores["joint_recovered_micro"],
        "share_of_total_waste_recovered": scores["share_of_total_waste_recovered"],
        "forecast_scores": [
            {key: value for key, value in row.items() if key not in {"rows", "monthly"}}
            for row in analysis["forecasts"]
        ],
        "detector": {key: value for key, value in detector.items() if key != "series"},
        "hypotheses": statistics,
        "exports": exported,
        "manifest_digest": digest(manifest),
    }
    write_json(output / "summary.json", summary)
    print(json.dumps(summary), flush=True)
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--smoke-hours", type=int)
    args = parser.parse_args()
    if args.smoke_hours is not None and not 1 <= args.smoke_hours <= 72:
        parser.error("A development smoke run must stay within the first three days")
    run(args.smoke_hours)

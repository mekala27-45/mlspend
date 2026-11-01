"""Promote passing CI and public-browser evidence from checksum-verified artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZipFile

from packages.core.io import ROOT, read_json, write_json


def verified_archive(path: Path, expected: str) -> ZipFile:
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected.removeprefix("sha256:"):
        raise ValueError("Artifact digest mismatch")
    return ZipFile(path)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("ci_zip", "browser_zip"):
        parser.add_argument("--" + name.replace("_", "-"), type=Path, required=True)
    for name in ("ci_sha", "browser_sha", "ci_run", "browser_run"):
        parser.add_argument("--" + name.replace("_", "-"), required=True)
    args = parser.parse_args()
    with verified_archive(args.ci_zip, args.ci_sha) as ci:
        suites = ET.fromstring(ci.read("results/tests-ci.xml"))
        totals = {
            name: sum(int(s.get(name, "0")) for s in suites)
            for name in ("tests", "failures", "errors", "skipped")
        }
        coverage = json.loads(ci.read("results/coverage.json"))["totals"]["percent_covered"]
        ci_manifest = json.loads(ci.read("results/manifest.json"))
    with verified_archive(args.browser_zip, args.browser_sha) as browser:
        live = json.loads(browser.read("evidence.json"))
    manifest = read_json(ROOT / "results/manifest.json")
    if (
        not totals["tests"]
        or any(totals[key] for key in ("failures", "errors", "skipped"))
        or coverage < 80
        or live["status"] != "passed"
        or live["price_digest"] != manifest["price_digest"]
        or ci_manifest["price_digest"] != manifest["price_digest"]
        or ci_manifest["generation"] != manifest["generation"]
    ):
        raise ValueError("Evidence does not pass or does not match the current source data")
    write_json(
        ROOT / "results/verification.json",
        {
            "version": 1,
            "ci": {
                "run_url": args.ci_run,
                "artifact_sha256": args.ci_sha,
                **totals,
                "coverage_percent": coverage,
            },
            "public_browser": {
                "run_url": args.browser_run,
                "artifact_sha256": args.browser_sha,
                **live,
            },
            "limits": "Evidence is scoped to these runs and deployed snapshots. Cold starts are not isolated. This is not complete validation of the analytical brief.",
        },
    )
    print({"tests": totals["tests"], "coverage": coverage, "browser": live["status"]})


if __name__ == "__main__":
    main()

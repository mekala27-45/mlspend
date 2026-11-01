from __future__ import annotations

import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import UTC, datetime

from packages.core.io import ROOT, digest, read_json, write_json


def run() -> dict[str, object]:
    suites = ET.parse(ROOT / "results/tests-offline.xml").getroot().findall("testsuite")
    counts = {
        name: sum(int(suite.attrib.get(name, "0")) for suite in suites)
        for name in ("tests", "errors", "failures", "skipped")
    }
    if not counts["tests"] or counts["errors"] or counts["failures"]:
        raise ValueError("Offline test evidence is absent or failed")
    checks = [
        ("ruff", [sys.executable, "-m", "ruff", "check", "packages", "scripts", "tests"]),
        (
            "format",
            [sys.executable, "-m", "ruff", "format", "--check", "packages", "scripts", "tests"],
        ),
        ("mypy_strict", [sys.executable, "-m", "mypy", "packages"]),
        ("claims_prices_registration_boundary", [sys.executable, "-m", "scripts.check"]),
        ("javascript_syntax", ["node", "--check", "web/app.js"]),
        ("diff_whitespace", ["git", "diff", "--cached", "--check"]),
    ]
    outcomes = {}
    for name, command in checks:
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
        outcomes[name] = {
            "status": "pass" if result.returncode == 0 else "fail",
            "exit_code": result.returncode,
        }
        if result.returncode:
            raise RuntimeError(f"{name} failed: {result.stdout}{result.stderr}")
    report: dict[str, object] = {
        "measured_at": datetime.now(UTC).isoformat(),
        "scope": "Explicit offline test subset, not the complete suite",
        "tests": counts,
        "coverage": read_json(ROOT / "results/coverage.json")["totals"],
        "manifest_digest": digest(read_json(ROOT / "results/manifest.json")),
        "checks": outcomes,
        "reproducibility": read_json(ROOT / "results/reproducibility.json"),
        "independent_sqlite_process": "pass in test_storage_commits_across_processes_and_closes_atomically",
        "http_transport": "blocked: Windows denied local socket use and asyncio socketpair initialization stalled",
        "postgresql": "not run: no configured integration database",
        "browser": "not verified: local server unreachable in managed session",
        "ci_and_deployments": "not run: intended repository unavailable; Neon and Vercel account access not verified",
        "release_ready": False,
    }
    write_json(ROOT / "results/validation.json", report)
    return report


if __name__ == "__main__":
    print(run())

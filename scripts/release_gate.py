"""Verify preserved evidence and current CI before publishing the release."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = "mekala27-45/mlspend"


def read(root: Path, name: str) -> Any:
    return json.loads((root / name).read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def verify_evidence(root: Path) -> dict[str, Any]:
    config: dict[str, Any] = read(root, "config/release.json")
    require(config["version"] == "v0.1.0", "Unexpected release version")
    completion = read(root, "config/completion.json")
    require(len(completion) == 18, "Incomplete requirement inventory")
    require(all(row["status"] == "Done" for row in completion), "Mandatory work remains")
    for name, expected in config["evidence_sha256"].items():
        path = (root / name).resolve()
        require(path.is_relative_to(root.resolve()), "Evidence path escapes repository")
        require(hashlib.sha256(path.read_bytes()).hexdigest() == expected, "Evidence digest drift: " + name)
    study = read(root, "results/expanded/reproducibility.json")
    require(study["status"] == "pass" and len(study["runs"]) == 2, "Missing independent rebuild")
    require({row["hash_seed"] for row in study["runs"]} == {17, 7919}, "Missing hash-seed comparison")
    require({row["checkout"] for row in study["runs"]} == {"primary", "detached-worktree"}, "Missing worktree")
    require(all(row["revision"] == config["verified_source"] for row in study["runs"]), "Rebuild source differs")
    require(all(row["manifest_digest"] == config["manifest_digest"] for row in study["runs"]), "Rebuild drift")
    live = read(root, "results/live/browser.json")
    require(live["status"] == "passed", "Live browser failed")
    require(live["source_digest"] == config["manifest_digest"], "Published data differs")
    require(live["idle"]["seconds"] >= 1200, "Idle interval is too short")
    require(live["idle"]["new_process_observed"], "No observed process startup")
    sql = read(root, "results/live/independent-readback.json")
    require({row["id"] for row in sql["rows"]} == {live["estimate_id"], live["forecast_id"]}, "SQL readback differs")
    require({row["kind"] for row in sql["rows"]} == {"estimate", "forecast"}, "Wrong persisted record kinds")
    prospective = read(root, "results/prospective/close.json")
    require(prospective["status"] == "pass" and prospective["total_scored"] == 6, "Prospective close incomplete")
    require(prospective["idempotent_replay_updates"] == 0, "Close is not idempotent")
    require(prospective["calendar_records_unchanged"], "Simulation changed calendar records")
    return config


def command(*args: str) -> str:
    return subprocess.check_output(args, cwd=ROOT, text=True, encoding="utf-8").strip()


def api(path: str) -> Any:
    return json.loads(command("gh", "api", f"repos/{REPOSITORY}/{path}"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checked-sha", required=True)
    parser.add_argument("--run-id", required=True, type=int)
    args = parser.parse_args()
    config = verify_evidence(ROOT)
    require(command("git", "rev-parse", "HEAD") == args.checked_sha, "Checkout differs from tested commit")
    require(api("git/ref/heads/main")["object"]["sha"] == args.checked_sha, "Main advanced after CI")
    require(int(command("git", "rev-list", "--count", "HEAD")) >= 40, "Insufficient commit history")
    subprocess.run(["git", "merge-base", "--is-ancestor", config["verified_source"], "HEAD"], cwd=ROOT, check=True)
    allowed = ("docs/", "results/", "report/")
    exact = {
        "config/completion.json", "config/release.json", "README.md", "RESULTS.md",
        "DECISIONS.md", ".github/workflows/release.yml", "scripts/release_gate.py",
        "tests/test_release.py", ".github/workflows/checks.yml",
    }
    changes = command("git", "diff", "--name-only", config["verified_source"], "HEAD").splitlines()
    require(all(name.startswith(allowed) or name in exact for name in changes), "Runtime or study changed since full verification")
    checks = api(f"actions/runs/{args.run_id}")
    require(checks["head_sha"] == args.checked_sha and checks["conclusion"] == "success", "Current CI did not pass")
    require(checks["name"] == "Build and verify" and checks["head_branch"] == "main", "Wrong CI workflow or branch")
    for expected in config["workflows"]:
        run = api(f"actions/runs/{expected['id']}")
        require(run["conclusion"] == "success", "Evidence workflow failed")
        require(run["head_sha"] == expected["source"] and run["name"] == expected["name"], "Evidence workflow identity differs")
    print(json.dumps({"version": config["version"], "checked_sha": args.checked_sha, "evidence": "pass", "current_ci": args.run_id}))


if __name__ == "__main__":
    main()

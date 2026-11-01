from __future__ import annotations

import os
import subprocess
import sys

from packages.core.io import ROOT, digest, file_digest, read_json, write_json


def run() -> dict[str, object]:
    runs = []
    for seed in ("1", "789"):
        subprocess.run(
            [sys.executable, "-m", "scripts.build"],
            cwd=ROOT,
            env={**os.environ, "PYTHONHASHSEED": seed},
            check=True,
        )
        runs.append(
            {
                "python_hash_seed": seed,
                "manifest_digest": digest(read_json(ROOT / "results/manifest.json")),
                "charges_digest": file_digest(ROOT / "data/generated/charges.jsonl.gz"),
                "telemetry_digest": file_digest(ROOT / "data/generated/telemetry.jsonl.gz"),
            }
        )
    comparable = ("manifest_digest", "charges_digest", "telemetry_digest")
    matches = all(runs[0][key] == runs[1][key] for key in comparable)
    result: dict[str, object] = {
        "status": "pass" if matches else "fail",
        "runs": runs,
        "scope": "separate Python processes in one checkout; clean-worktree replication remains",
    }
    write_json(ROOT / "results/reproducibility.json", result)
    if not matches:
        raise AssertionError("Repeated builds differ")
    return result


if __name__ == "__main__":
    print(run())

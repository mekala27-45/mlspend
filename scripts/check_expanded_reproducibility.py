"""Re-derive the complete study in separate Python processes with different hash seeds."""

import json
import os
import subprocess
import sys

from packages.core.io import ROOT, digest, read_json, write_json


def main() -> None:
    runs = []
    for seed in (17, 7919):
        subprocess.run(
            [sys.executable, "-m", "scripts.build_expanded"],
            cwd=ROOT,
            env={**os.environ, "PYTHONHASHSEED": str(seed)},
            check=True,
        )
        result = read_json(ROOT / "results/expanded/manifest.json")
        runs.append(
            {
                "hash_seed": seed,
                "manifest_digest": digest(result),
                "observed_sha256": result["generation"]["observed_sha256"],
                "plan_digest": result["registration"]["plan_digest"],
            }
        )
    if (
        runs[0]["manifest_digest"] != runs[1]["manifest_digest"]
        or runs[0]["observed_sha256"] != runs[1]["observed_sha256"]
    ):
        raise AssertionError("Complete study is not reproducible across hash seeds")
    write_json(
        ROOT / "results/expanded/reproducibility.json",
        {
            "status": "pass",
            "runs": runs,
            "scope": "Full generation, contracted warehouse, every method, every action/incident rerun and finance export metadata. Workbook ZIP timestamps are not a scientific result.",
        },
    )
    print(json.dumps(runs))


if __name__ == "__main__":
    main()

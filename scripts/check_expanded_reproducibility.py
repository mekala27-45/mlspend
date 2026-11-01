"""Re-derive the complete study in separate Python processes with different hash seeds."""

import json
import os
import subprocess
import sys

from packages.core.io import ROOT, digest, read_json, write_json


def main() -> None:
    runs = []
    snapshots = []
    worktree = ROOT / "tmp/rederive-worktree"
    if worktree.exists():
        raise FileExistsError(
            "Use a fresh checkout; the canonical rederive worktree already exists"
        )
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    subprocess.run(
        ["git", "worktree", "add", "--detach", str(worktree), revision], cwd=ROOT, check=True
    )
    for seed in (17, 7919):
        run_root = ROOT if seed == 17 else worktree
        subprocess.run(
            [sys.executable, "-m", "scripts.build_expanded"],
            cwd=run_root,
            env={**os.environ, "PYTHONHASHSEED": str(seed)},
            check=True,
        )
        result = read_json(run_root / "results/expanded/manifest.json")
        snapshots.append(result)
        write_json(ROOT / f"results/expanded/rebuild-{seed}.json", result)
        runs.append(
            {
                "hash_seed": seed,
                "checkout": "primary" if seed == 17 else "detached-worktree",
                "revision": revision,
                "manifest_digest": digest(result),
                "observed_sha256": result["generation"]["observed_sha256"],
                "plan_digest": result["registration"]["plan_digest"],
            }
        )
    if (
        runs[0]["manifest_digest"] != runs[1]["manifest_digest"]
        or runs[0]["observed_sha256"] != runs[1]["observed_sha256"]
    ):

        def differences(a, b, path=""):
            if isinstance(a, dict) and isinstance(b, dict):
                return [
                    p
                    for key in sorted(a.keys() | b.keys())
                    for p in differences(a.get(key), b.get(key), path + "." + key)
                ]
            if isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
                return [
                    p
                    for i, (left, right) in enumerate(zip(a, b, strict=True))
                    for p in differences(left, right, path + f"[{i}]")
                ]
            return [] if a == b else [path]

        print(json.dumps({"different_paths": differences(*snapshots)[:100]}))
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

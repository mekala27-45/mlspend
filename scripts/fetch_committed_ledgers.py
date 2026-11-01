"""Fetch every committed run in the selected public build ledgers, inside Actions."""

from __future__ import annotations

import base64
import hashlib
import json
import os
from collections import defaultdict
from datetime import UTC, datetime
from typing import Any

import httpx

from packages.core.io import ROOT, STATEMENT, digest, read_json, write_json
from packages.prices.client import SourceClient


def main() -> None:
    request = read_json(ROOT / "requests/portfolio.json")
    client = SourceClient(
        ROOT / "tmp/ledger-cache",
        {
            "Authorization": "Bearer " + os.environ["GITHUB_TOKEN"],
            "Accept": "application/vnd.github+json",
        },
    )
    rows: list[dict[str, Any]] = []
    sources, inventories, absent = [], [], []
    start, end = (datetime.fromisoformat(request[k]) for k in ("start", "end_exclusive"))
    for name in sorted(set(request["ledger_projects"] + ["cityflow"])):
        repository = request["owner"] + "/" + name
        try:
            repo = client.get("https://api.github.com/repos/" + repository)
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code != 404:
                raise
            absent.append(
                {
                    "repository": repository,
                    "status": "not measured",
                    "reason": "No accessible public repository at retrieval",
                }
            )
            continue
        commit = client.get(
            f"https://api.github.com/repos/{repository}/commits/{repo['default_branch']}"
        )["sha"]
        tree = client.get(
            f"https://api.github.com/repos/{repository}/git/trees/{commit}?recursive=1"
        )
        if tree.get("truncated"):
            raise ValueError("Truncated source inventory")
        paths = [
            r
            for r in tree["tree"]
            if r["type"] == "blob"
            and (
                (
                    name == "trajectory"
                    and r["path"].startswith("fixtures/model-runs/")
                    and r["path"].endswith(".json")
                )
                or (
                    name == "friction"
                    and r["path"]
                    in {"results/compute_ledger.json", "results/workspace/run_ledger.json"}
                )
                or (
                    name == "readback"
                    and r["path"].startswith("results/evals/runs/")
                    and r["path"].endswith(".json")
                )
                or (
                    name == "goodhart"
                    and "ledger" in r["path"]
                    and r["path"].endswith((".jsonl", ".json"))
                )
                or (name in {"goodhart", "cityflow"} and r["path"] == "results/manifest.json")
            )
        ]
        inventories.append(
            {
                "repository": repository,
                "commit": commit,
                "paths": [p["path"] for p in paths],
                "status": "measured committed records"
                if paths and name != "goodhart"
                else "no committed GPU ledger; not measured",
            }
        )
        for item in sorted(paths, key=lambda r: r["path"]):
            path = item["path"]
            blob = client.get(f"https://api.github.com/repos/{repository}/git/blobs/{item['sha']}")
            raw = base64.b64decode(blob["content"])
            checksum = hashlib.sha256(raw).hexdigest()
            actual_git = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
            if actual_git != item["sha"]:
                raise ValueError("Git blob bytes do not match the inventory")
            value = (
                [json.loads(line) for line in raw.splitlines() if line.strip()]
                if path.endswith(".jsonl")
                else json.loads(raw)
            )
            source = {
                "repository": repository,
                "path": path,
                "commit": commit,
                "sha256": checksum,
                "git_blob": item["sha"],
                "source_url": f"https://github.com/{repository}/blob/{commit}/{path}",
            }
            sources.append(source)
            common = {
                "repository": repository,
                "source_url": source["source_url"],
                "source_digest": checksum,
            }
            if name == "trajectory":
                at = datetime.fromisoformat(value["started_at"])
                steps = value["steps"]
                rows.append(
                    {
                        **common,
                        "id": value["id"],
                        "kind": "model_run",
                        "model": value["config"]["model"],
                        "in_window": start <= at < end,
                        "started_at": value["started_at"],
                        "tokens_in": sum(s.get("tokens_in") or 0 for s in steps),
                        "tokens_out": sum(s.get("tokens_out") or 0 for s in steps),
                        "token_count_basis": "provider usage recorded per step"
                        if all(
                            s.get("tokens_in") is not None and s.get("tokens_out") is not None
                            for s in steps
                        )
                        else "partial recorded usage; not a complete count",
                        "seconds": value["wall_clock_s"],
                        "outputs": 1,
                        "solved": bool(value["solved"]),
                        "price_status": "unpriced: NIM free hosted endpoint has no captured paid token SKU; do not substitute another provider silently",
                        "cost_micro": None,
                    }
                )
            elif name == "friction" and path.endswith("compute_ledger.json"):
                for step in value["steps"]:
                    day = datetime.fromisoformat(step["request"][:10] + "T00:00:00+00:00")
                    rows.append(
                        {
                            **common,
                            "id": step["request"],
                            "kind": "compute_step",
                            "in_window": start <= day < end,
                            **step,
                            "cost_micro": None,
                            "price_status": "already included in Actions job bill; do not double count"
                            if step["kind"] == "portable"
                            else "unpriced: serverless wall time does not identify billable DBU quantity",
                        }
                    )
                for number, values in enumerate(value["billing"]["rows"]):
                    usage = dict(zip(value["billing"]["columns"], values, strict=True))
                    rows.append(
                        {
                            **common,
                            "id": "billing-" + str(number),
                            "kind": "provider_usage",
                            "in_window": request["start"][:10]
                            <= usage["usage_date"]
                            < request["end_exclusive"][:10],
                            **usage,
                            "cost_micro": None,
                            "price_status": "unpriced: exact AWS Databricks public SKU rate not captured",
                        }
                    )
            elif name == "friction":
                for number, values in enumerate(value["rows"]):
                    step = dict(zip(value["columns"], values, strict=True))
                    rows.append(
                        {
                            **common,
                            "id": "workspace-" + str(number),
                            "kind": "task_outputs",
                            **step,
                            "in_window": start <= datetime.fromisoformat(step["first"]) < end
                            and datetime.fromisoformat(step["last"]) < end,
                            "cost_micro": None,
                            "price_status": "output denominator; compute overlaps the run ledger",
                        }
                    )
            elif name == "readback":
                for item_row in value["rows"]:
                    rows.append(
                        {
                            **common,
                            "id": path + ":" + item_row["id"],
                            "kind": "query_evaluation",
                            "model": item_row["model"],
                            "provider": value["provider"],
                            "tokens_in": item_row["tokens_in"],
                            "tokens_out": item_row["tokens_out"],
                            "outputs": 1,
                            "passed": item_row["passed"],
                            "model_calls": item_row["model_calls"],
                            "seconds": item_row["latency_ms"] / 1000,
                            "in_window": None,
                            "cost_micro": 0 if item_row["model_calls"] == 0 else None,
                            "price_status": "no model call; hosted CPU cost not measured"
                            if item_row["model_calls"] == 0
                            else "unpriced model",
                            "time_status": "committed evaluation has no per-row timestamp; excluded from period total",
                        }
                    )
            else:
                # Preserve source-reported values, including missing GPU results, without inventing denominators.
                write_json(ROOT / "data/portfolio/ledgers" / (name + "-manifest.json"), value)
    identifiers = [(r["repository"], r["kind"], r["id"]) for r in rows]
    if len(set(identifiers)) != len(identifiers):
        raise ValueError("Duplicate committed run identity")
    totals: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "rows": 0,
            "tokens_in": 0,
            "tokens_out": 0,
            "seconds": 0.0,
            "outputs": 0,
            "solved": 0,
        }
    )
    for row in rows:
        if row.get("in_window") is not True or row["kind"] != "model_run":
            continue
        group = totals[row["model"]]
        group["rows"] += 1
        for field in ("tokens_in", "tokens_out", "seconds", "outputs", "solved"):
            group[field] += row.get(field, 0)
    result = {
        "statement": STATEMENT,
        "request": request,
        "retrieved_at": datetime.now(UTC).isoformat(),
        "sources": sources,
        "source_digest": digest(sources),
        "inventory": inventories,
        "absent": absent,
        "rows": rows,
        "model_totals": dict(totals),
        "row_count": len(rows),
        "limits": [
            "Inventory and token counts are measured committed evidence. Unpriced is never zero.",
            "Runner-contained compute is excluded from incremental cost to avoid counting the same job twice.",
            "Undated evaluation rows are described but excluded from the period cost total.",
        ],
    }
    write_json(ROOT / "results/committed-ledgers.json", result)
    write_json(
        ROOT / "data/portfolio/ledgers/lock.json",
        {"sources": sources, "source_digest": digest(sources), "result_digest": digest(result)},
    )
    print(
        json.dumps(
            {"rows": len(rows), "sources": len(sources), "models": dict(totals), "absent": absent}
        )
    )


if __name__ == "__main__":
    main()

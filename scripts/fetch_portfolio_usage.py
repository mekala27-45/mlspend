from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import httpx

from packages.core.io import ROOT, STATEMENT, digest, read_json, write_json
from packages.portfolio.usage import price_job
from packages.prices.book import PriceBook
from packages.prices.client import SourceClient


def fetch_runs(
    client: SourceClient, repository: str, start: datetime, end: datetime
) -> list[dict[str, Any]]:
    # GitHub caps filtered searches at 1,000 runs. Split overflowing windows instead of truncating.
    query = urlencode(
        {"created": f"{start.isoformat()}..{(end - timedelta(seconds=1)).isoformat()}"}
    )
    url = f"https://api.github.com/repos/{repository}/actions/runs?{query}"
    first = client.get(url + "&per_page=100&page=1")
    if first["total_count"] > 1000:
        seconds = int((end - start).total_seconds())
        if seconds < 2:
            raise ValueError("More than 1,000 runs in one second; refusing incomplete evidence")
        middle = start + timedelta(seconds=seconds // 2)
        return fetch_runs(client, repository, start, middle) + fetch_runs(
            client, repository, middle, end
        )
    rows = client.github_pages(url, "workflow_runs")
    if len(rows) != first["total_count"]:
        raise ValueError("Run count changed during fetch; resume to obtain a consistent snapshot")
    return rows


def main(
    request_path: Path = ROOT / "requests/portfolio.json",
    output_path: Path = ROOT / "results/portfolio-usage.json",
    cache_path: Path = ROOT / "tmp/portfolio-cache",
) -> None:
    request = read_json(request_path)
    headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise ValueError("Run this fetch in Actions with its scoped GitHub token")
    headers["Authorization"] = "Bearer " + token
    client = SourceClient(cache_path, headers)
    repos = client.github_pages(
        f"https://api.github.com/users/{request['owner']}/repos?type=owner&sort=full_name"
    )
    repos = sorted((r for r in repos if not r["private"]), key=lambda r: r["full_name"])
    if not repos:
        raise ValueError("No public repositories found; refusing an empty usage claim")
    start, end = (datetime.fromisoformat(request[k]) for k in ("start", "end_exclusive"))
    book = PriceBook()
    summaries, jobs, inventory = [], [], []
    for repo in repos:
        name = repo["full_name"]
        runs = fetch_runs(client, name, start, end)
        repo_jobs = []
        for run in runs:
            # filter=all includes every attempt, including retries.
            rows = client.github_pages(
                f"https://api.github.com/repos/{name}/actions/runs/{run['id']}/jobs?filter=all",
                "jobs",
            )
            for job in rows:
                try:
                    repo_jobs.append(price_job(name, job, book))
                except ValueError as error:
                    repo_jobs.append(
                        {
                            "repository": name,
                            "job_id": job["id"],
                            "source_url": job["html_url"],
                            "started_at": job.get("started_at"),
                            "completed_at": job.get("completed_at"),
                            "minutes": None,
                            "cost_micro": None,
                            "price_id": None,
                            "status": "quarantined",
                            "reason": str(error),
                        }
                    )
        if len({r["job_id"] for r in repo_jobs}) != len(repo_jobs):
            raise ValueError("Duplicate job evidence")
        jobs.extend(repo_jobs)
        artifacts = client.github_pages(
            f"https://api.github.com/repos/{name}/actions/artifacts", "artifacts"
        )
        releases = client.github_pages(f"https://api.github.com/repos/{name}/releases")
        summaries.append(
            {
                "repository": name,
                "runs": len(runs),
                "jobs": len(repo_jobs),
                "priced_jobs": sum(r["cost_micro"] is not None for r in repo_jobs),
                "unpriced_jobs": sum(r["cost_micro"] is None for r in repo_jobs),
                "shadow_cost_micro": sum(r["cost_micro"] or 0 for r in repo_jobs),
                "complete": all(r["cost_micro"] is not None for r in repo_jobs),
                "repository_kib_snapshot": repo["size"],
                "artifact_bytes_snapshot": sum(a["size_in_bytes"] for a in artifacts),
                "release_asset_bytes_snapshot": sum(
                    a["size"] for release in releases for a in release["assets"]
                ),
                "source_url": repo["html_url"],
            }
        )
        if repo["name"].lower() in request["ledger_projects"]:
            try:
                tree = client.get(
                    f"https://api.github.com/repos/{name}/git/trees/{repo['default_branch']}?recursive=1"
                )
                if tree.get("truncated"):
                    raise ValueError("Ledger inventory tree truncated")
                candidates = [
                    r["path"]
                    for r in tree["tree"]
                    if r["type"] == "blob"
                    and any(k in r["path"].lower() for k in ("ledger", "run_record", "cassette"))
                ]
                inventory.append(
                    {
                        "repository": name,
                        "candidate_paths": candidates,
                        "status": "schema inspection required"
                        if candidates
                        else "no ledger candidate found",
                    }
                )
            except httpx.HTTPStatusError as error:
                if error.response.status_code != 409:
                    raise
                inventory.append(
                    {"repository": name, "candidate_paths": [], "status": "empty repository"}
                )
    found = {r["name"].lower() for r in repos}
    report = {
        "statement": STATEMENT,
        "request": request,
        "request_digest": digest(request),
        "retrieved_at": datetime.now(UTC).isoformat(),
        "price_digest": book.digest,
        "status": "CI usage measured; build-ledger coverage reported separately",
        "rows": summaries,
        "jobs": jobs,
        "ledger_inventory": inventory,
        "absent_ledger_projects": sorted(set(request["ledger_projects"]) - found),
        "visited": client.visited,
        "repository_count": len(repos),
        "priced_subtotal_micro": sum(r["shadow_cost_micro"] for r in summaries),
        "reason": "CI covers all public repositories and all run attempts in the committed creation-time window. Storage sizes are point-in-time inventory, not storage-month usage. Absent or unparsed ledgers are not zero usage.",
    }
    write_json(output_path, report)
    print({"repositories": len(repos), "jobs": len(jobs), "evidence_digest": digest(report)})


if __name__ == "__main__":
    main()

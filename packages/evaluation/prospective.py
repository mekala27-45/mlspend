"""Run the registered issue-then-close simulation through the deployed API and Neon."""

from __future__ import annotations

import argparse
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx
from sqlalchemy import text

from packages.api.storage import Store
from packages.core.io import ROOT, STATEMENT, digest, read_json, write_json
from packages.forecast.prospective import forecast
from packages.forecast.scoring import score_forecast

API = "https://mlspend.vercel.app"
FOLDER = ROOT / "evaluation/prospective"


def registered_inputs() -> tuple[dict[str, Any], list[dict[str, Any]], str]:
    plan = read_json(FOLDER / "plan.json")
    history = read_json(FOLDER / "history.json")
    registration = read_json(FOLDER / "registration.json")
    plan_digest = digest(plan)
    if plan_digest != registration["plan_digest"] or digest(history) != plan["history_digest"]:
        raise ValueError("Prospective registration drift")
    if any(r["month"] >= plan["period"] for r in history):
        raise ValueError("Future observations in forecast history")
    return plan, history, plan_digest


def connection() -> Store:
    return Store(os.environ["DATABASE_URL"], os.environ["MLSPEND_SALT"])


def calendar_snapshot(store: Store) -> list[dict[str, Any]]:
    with store.engine.connect() as conn:
        return [
            dict(row)
            for row in conn.execute(
                text(
                    "SELECT id, actual_micro, scored_at FROM mlspend_request_log WHERE kind='forecast' ORDER BY id"
                )
            ).mappings()
        ]


def issue(target: Path) -> None:
    plan, history, plan_digest = registered_inputs()
    simulation_id = (
        f"prospective-{os.environ['GITHUB_RUN_ID']}-{os.environ.get('GITHUB_RUN_ATTEMPT', '1')}"
    )
    reader = connection()
    records = []
    try:
        with reader.engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        with httpx.Client(base_url=API, timeout=90) as client:
            health = client.get("/health")
            health.raise_for_status()
            if "simulation" not in health.json().get("forecast_clocks", []):
                raise ValueError("The deployed API does not support the explicit simulation clock")
            for team in plan["teams"]:
                payload = {
                    "book": "platform",
                    "team": team,
                    "period": plan["period"],
                    "data_cutoff": plan["data_cutoff"],
                    "clock": "simulation",
                    "simulation_id": simulation_id,
                    "plan_digest": plan_digest,
                    **forecast(history, team, plan["coverage"]),
                }
                # An uncertain POST is never retried automatically.
                response = client.post("/v1/forecasts", json=payload)
                response.raise_for_status()
                identifier = response.json()["id"]
                row = reader.get(identifier)
                if (
                    row is None
                    or row["kind"] != "simulation_forecast"
                    or json.loads(row["payload"]) != payload
                ):
                    raise ValueError("Independent readback does not match the issued forecast")
                if row["scored_at"] is not None or row["actual_micro"] is not None:
                    raise ValueError("Outcomes already exist at issuance")
                records.append(
                    {
                        "id": identifier,
                        "payload": payload,
                        "created_at": row["created_at"],
                        "actual_micro": None,
                        "scored_at": None,
                    }
                )
        write_json(
            target,
            {
                "statement": STATEMENT,
                "simulation_id": simulation_id,
                "plan_digest": plan_digest,
                "source_commit": os.environ["GITHUB_SHA"],
                "run_id": os.environ["GITHUB_RUN_ID"],
                "issued_at": datetime.now(UTC).isoformat(),
                "records": records,
                "independent_readback": True,
                "outcomes_generated": False,
                "clock": "simulation",
                "period": plan["period"],
            },
        )
        print({"issued": len(records), "simulation_id": simulation_id})
    finally:
        reader.engine.dispose()


def close(issued_path: Path, target: Path) -> None:
    plan, history, plan_digest = registered_inputs()
    issued = read_json(issued_path)
    if issued["plan_digest"] != plan_digest or issued["outcomes_generated"] is not False:
        raise ValueError("Invalid issuance evidence")
    records = issued["records"]
    if (
        len(records) != len(plan["teams"])
        or sorted(r["payload"]["team"] for r in records) != plan["teams"]
    ):
        raise ValueError("Issuance must cover every registered team exactly once")
    writer, reader = connection(), connection()
    try:
        for record in records:
            row = reader.get(record["id"])
            if (
                row is None
                or row["kind"] != "simulation_forecast"
                or json.loads(row["payload"]) != record["payload"]
            ):
                raise ValueError("Persisted forecast differs from issuance evidence")
            if row["created_at"] != record["created_at"] or record["actual_micro"] is not None:
                raise ValueError("Issuance chronology is invalid")
        with reader.engine.connect() as conn:
            matching = [
                r["id"]
                for r in conn.execute(
                    text(
                        "SELECT id, payload FROM mlspend_request_log WHERE kind='simulation_forecast' AND period=:period"
                    ),
                    {"period": plan["period"]},
                ).mappings()
                if json.loads(r["payload"]).get("simulation_id") == issued["simulation_id"]
            ]
        if sorted(matching) != sorted(r["id"] for r in records):
            raise ValueError("Simulation contains unregistered forecast records")
        calendar_before = calendar_snapshot(reader)
        # The forecast job has completed and uploaded its durable readback before this import.
        from packages.truth.prospective import outcomes

        generated_at = datetime.now(UTC).isoformat()
        actuals = outcomes(history, plan["seed"], plan["teams"])
        write_json(
            target.parent / "outcomes.json",
            {
                "statement": STATEMENT,
                "clock": "simulation",
                "generated_at": generated_at,
                "issued_digest": digest(issued),
                "plan_digest": plan_digest,
                "actuals_micro": actuals,
            },
        )
        simulation_close = datetime.fromisoformat(plan["simulated_close"])
        scored = writer.close_simulation(
            plan["period"], issued["simulation_id"], actuals, simulation_close
        )
        replay = writer.close_simulation(
            plan["period"], issued["simulation_id"], actuals, simulation_close
        )
        checked = []
        with httpx.Client(base_url=API, timeout=90) as client:
            for record in records:
                row = reader.get(record["id"])
                if (
                    row is None
                    or row["actual_micro"] != actuals["platform:" + record["payload"]["team"]]
                ):
                    raise ValueError("Independent scored readback failed")
                response = client.get("/v1/forecasts/" + record["id"])
                response.raise_for_status()
                score = score_forecast(row)
                if score is None or response.json()["score"] != score:
                    raise ValueError("HTTP score differs from independent SQL score")
                checked.append(
                    {
                        "id": row["id"],
                        "team": record["payload"]["team"],
                        "created_at": row["created_at"],
                        "scored_at": row["scored_at"],
                        "forecast": record["payload"],
                        "score": score,
                    }
                )
        unchanged = calendar_before == calendar_snapshot(reader)
        if not unchanged or replay != 0 or len(checked) != len(plan["teams"]):
            raise ValueError("Isolation, idempotency or completeness check failed")
        write_json(
            target,
            {
                "statement": STATEMENT,
                "status": "pass",
                "clock": "simulation",
                "simulation_id": issued["simulation_id"],
                "period": plan["period"],
                "simulated_close": plan["simulated_close"],
                "generated_at": generated_at,
                "completed_at": datetime.now(UTC).isoformat(),
                "issued_digest": digest(issued),
                "plan_digest": plan_digest,
                "scored_this_attempt": scored,
                "total_scored": len(checked),
                "idempotent_replay_updates": replay,
                "calendar_records_unchanged": unchanged,
                "calendar_record_count": len(calendar_before),
                "rows": checked,
                "limits": plan["limits"],
                "run_id": os.environ["GITHUB_RUN_ID"],
                "source_commit": os.environ["GITHUB_SHA"],
            },
        )
        print({"scored": scored, "verified": len(checked), "calendar_records_unchanged": unchanged})
    finally:
        writer.engine.dispose()
        reader.engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=["issue", "close"])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--issued", type=Path)
    args = parser.parse_args()
    if args.stage == "issue":
        issue(args.output)
    elif args.issued is None:
        parser.error("close requires --issued")
    else:
        close(args.issued, args.output)


if __name__ == "__main__":
    main()

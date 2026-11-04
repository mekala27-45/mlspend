"""Collect a dated review candidate only after the registered next observation."""

from datetime import UTC, datetime

from packages.core.io import ROOT, read_json, write_json
from scripts.fetch_expanded_prices import main as collect


def main() -> None:
    due = read_json(ROOT / "evaluation/stretch/plan.json")["price_observation"]["not_before"]
    now = datetime.now(UTC)
    if now.date().isoformat() < due:
        write_json(
            ROOT / "results/monthly-price-status.json",
            {"status": "not due", "not_before": due, "checked_at": now.isoformat()},
        )
        print("Second observation is not due; no prices fetched or promoted")
        return
    collect()
    candidate = read_json(ROOT / "results/expanded-price-candidate.json")
    if candidate["retrieved_at"][:10] < due:
        raise ValueError("Candidate observation is stale")
    write_json(
        ROOT / "results/monthly-price-status.json",
        {
            "status": "candidate collected; review and promotion required",
            "not_before": due,
            "observed_at": candidate["retrieved_at"],
        },
    )


if __name__ == "__main__":
    main()

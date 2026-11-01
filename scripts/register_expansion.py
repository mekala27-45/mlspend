"""One-time registration for the explicitly amended simulation, before generation."""

from datetime import UTC, datetime

from packages.core.io import ROOT, digest, read_json, write_json


def main() -> None:
    directory = ROOT / "evaluation/v2"
    if (directory / "registration.json").exists():
        raise ValueError("Registration already exists; create a new version for further changes")
    if (ROOT / "data/expanded/observed.jsonl.gz").exists():
        raise ValueError("Expanded observations already exist; cannot pre-register retroactively")
    write_json(
        directory / "registration.json",
        {
            "plan_digest": digest(read_json(directory / "plan.json")),
            "registered_at": datetime.now(UTC).isoformat(),
            "prior_registration_digest": digest(read_json(ROOT / "evaluation/registration.json")),
            "statement": "Amended protocol registered before expanded seed generation; version-one results were already known.",
        },
    )


if __name__ == "__main__":
    main()

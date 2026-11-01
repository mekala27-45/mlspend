from datetime import UTC, datetime

from packages.core.io import ROOT, digest, read_json, write_json


def register() -> None:
    plan = read_json(ROOT / "evaluation/plan.json")
    destination = ROOT / "evaluation/registration.json"
    if destination.exists():
        if read_json(destination)["plan_digest"] != digest(plan):
            raise ValueError("Registered plan changed. Create an explicit new plan version.")
        return
    if (ROOT / "results/manifest.json").exists():
        raise ValueError("Refusing registration after results exist")
    write_json(
        destination,
        {
            "plan_digest": digest(plan),
            "registered_at": datetime.now(UTC).isoformat(),
            "statement": "Registered before the first held-out evaluation in this repository.",
        },
    )


if __name__ == "__main__":
    register()

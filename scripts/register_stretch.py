"""Register the optional extension before generating its observations."""

from packages.core.io import ROOT, digest, read_json, write_json


def main() -> None:
    path = ROOT / "evaluation/stretch/registration.json"
    value = {
        "plan_digest": digest(read_json(ROOT / "evaluation/stretch/plan.json")),
        "registered_before_generation": True,
    }
    if path.exists() and read_json(path) != value:
        raise ValueError("Existing registration differs; create a new study version")
    write_json(path, value)


if __name__ == "__main__":
    main()

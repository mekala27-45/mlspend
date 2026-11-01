import subprocess

from packages.core.gates import import_boundary, statement_gate, text_gate
from packages.core.io import ROOT, STATEMENT, digest, read_json
from packages.prices.book import PriceBook
from packages.render.documents import render


def main() -> None:
    tracked = subprocess.check_output(["git", "ls-files"], cwd=ROOT, text=True).splitlines()
    names = [
        name
        for name in tracked
        if name.endswith((".py", ".md", ".js", ".html", ".css", ".yml", ".tsx", ".ts"))
        and name not in ("docs/BUILD_BRIEF.md", "docs/SPEC.md")
    ]
    contents = {name: (ROOT / name).read_text(encoding="utf-8") for name in names}
    text_gate(contents, check_wording=False)
    # The vocabulary definition and adversarial fixtures contain forbidden examples.
    prose = {
        name: value
        for name, value in contents.items()
        if name
        not in ("packages/core/gates.py", "tests/test_core.py", "tests/test_gates_expanded.py")
    }
    text_gate(prose)
    import_boundary(ROOT / "packages")
    PriceBook()
    PriceBook(ROOT / "data/prices/expanded")
    expanded_plan = digest(read_json(ROOT / "evaluation/v2/plan.json"))
    if expanded_plan != read_json(ROOT / "evaluation/v2/registration.json")["plan_digest"]:
        raise ValueError("Expanded registration drift")
    study = read_json(ROOT / "results/expanded/manifest.json")
    if study["registration"]["plan_digest"] != expanded_plan:
        raise ValueError("Expanded result does not match its registered plan")
    if (
        digest(read_json(ROOT / "evaluation/plan.json"))
        != read_json(ROOT / "evaluation/registration.json")["plan_digest"]
    ):
        raise ValueError("Registration drift")
    manifest = read_json(ROOT / "results/manifest.json")
    render(manifest, check=True)
    statement_gate(
        {
            name: (ROOT / name).read_text(encoding="utf-8")
            for name in ("README.md", "RESULTS.md", "report/briefing.md")
        },
        STATEMENT,
    )
    print(
        {
            "files_scanned": len(names),
            "claim_render": "pass",
            "price_lock": "pass",
            "registration": "pass",
            "import_boundary": "pass",
        }
    )


if __name__ == "__main__":
    main()

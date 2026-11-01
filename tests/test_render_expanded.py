import json
import shutil

import pytest

from packages.core.io import ROOT
from packages.render.expanded import method_note, render


def test_generated_claims_match_evidence_and_reject_drift(tmp_path):
    for name in (
        "results/expanded/manifest.json",
        "results/manifest.json",
        "results/committed-ledgers.json",
        "data/prices/expanded/book.json",
        "config/completion.json",
        "config/method-notes.json",
    ):
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, target)
    render(tmp_path)
    render(tmp_path, check=True)
    data = json.loads((tmp_path / "web/expanded.json").read_text())
    original = json.loads((tmp_path / "results/expanded/manifest.json").read_text())
    assert (
        sum(r["effective_micro"] for r in data["monthly"]) == original["generation"]["total_micro"]
    )
    assert len(list((tmp_path / "report/statements").glob("*.md"))) == len(original["allocation"])
    (tmp_path / "README.md").write_text("Unsupported savings claim")
    with pytest.raises(ValueError, match="drift"):
        render(tmp_path, check=True)
    original["allocation"] = []
    (tmp_path / "results/expanded/manifest.json").write_text(json.dumps(original))
    with pytest.raises(ValueError, match="nonempty"):
        render(tmp_path)


def test_method_note_requires_every_section():
    page = {
        "title": "Fixture",
        "intro": "Purpose",
        "limit": "Limit",
        "sections": [
            {"title": "Score", "headers": ["Outcome"], "rows": [["Fixture pass"]], "note": ""}
        ],
    }
    detail = {k: "Present" for k in ("inputs", "assumptions", "sensitivity", "pushback")}
    assert "## Purpose" in method_note(page, detail)
    with pytest.raises(ValueError, match="required section"):
        method_note(page, {**detail, "inputs": ""})
    with pytest.raises(ValueError, match="required section"):
        method_note({}, {})

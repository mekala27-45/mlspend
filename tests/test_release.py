from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import pytest

from scripts.release_gate import verify_evidence

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def release_root(tmp_path: Path) -> Path:
    config = json.loads((ROOT / "config/release.json").read_text(encoding="utf-8"))
    for name in ["config/release.json", "config/completion.json", *config["evidence_sha256"]]:
        destination = tmp_path / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, destination)
    return tmp_path


def test_verified_evidence_accepts_complete_release(release_root: Path) -> None:
    assert verify_evidence(release_root)["version"] == "v0.1.0"


def test_release_refuses_pending_requirement(release_root: Path) -> None:
    path = release_root / "config/completion.json"
    rows = json.loads(path.read_text(encoding="utf-8"))
    rows[8]["status"] = "Not done"
    path.write_text(json.dumps(rows), encoding="utf-8")
    with pytest.raises(ValueError, match="Mandatory work remains"):
        verify_evidence(release_root)


def test_release_refuses_changed_evidence(release_root: Path) -> None:
    path = release_root / "results/live/browser.json"
    path.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="Evidence digest drift"):
        verify_evidence(release_root)


def test_release_refuses_wrong_sql_record_even_if_rehashed(release_root: Path) -> None:
    name = "results/live/independent-readback.json"
    path = release_root / name
    evidence = json.loads(path.read_text(encoding="utf-8"))
    evidence["rows"][0]["id"] = "unrelated-record"
    path.write_text(json.dumps(evidence), encoding="utf-8")
    config_path = release_root / "config/release.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config["evidence_sha256"][name] = hashlib.sha256(path.read_bytes()).hexdigest()
    config_path.write_text(json.dumps(config), encoding="utf-8")
    with pytest.raises(ValueError, match="SQL readback differs"):
        verify_evidence(release_root)

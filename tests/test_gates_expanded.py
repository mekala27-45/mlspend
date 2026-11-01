import pytest

from packages.core.gates import import_boundary, statement_gate, text_gate
from scripts.check_diff import scan


def test_diff_scan_accepts_public_metadata():
    scan({"code.py": "repository = 'https://github.com/mekala27-45/mlspend'\n"})


def test_diff_scan_rejects_private_identifier_and_credentials():
    with pytest.raises(ValueError, match="identifier"):
        scan({"private.txt": 'employee_email="person@example.org"'})
    with pytest.raises(ValueError, match="credential"):
        scan({"bad.txt": "ghp_" + "x" * 30})


def test_diff_scan_rejects_empty_input():
    with pytest.raises(ValueError, match="Empty"):
        scan({})


@pytest.mark.parametrize("value", ["seamless", chr(0x2014)])
def test_text_gate_rejects_bad_wording_and_punctuation(value):
    with pytest.raises(ValueError):
        text_gate({"doc.md": value})


def test_statement_gate_clean_violation_empty():
    statement_gate({"doc": "Disclosure present"}, "Disclosure")
    with pytest.raises(ValueError):
        statement_gate({"doc": "Missing"}, "Disclosure")
    with pytest.raises(ValueError):
        statement_gate({}, "Disclosure")


def test_boundary_clean_violation_empty(tmp_path):
    with pytest.raises(ValueError, match="No method"):
        import_boundary(tmp_path)
    folder = tmp_path / "allocation"
    folder.mkdir()
    target = folder / "method.py"
    target.write_text("import math\n")
    import_boundary(tmp_path)
    target.write_text("from packages.truth import access\n")
    with pytest.raises(ValueError, match="Truth"):
        import_boundary(tmp_path)

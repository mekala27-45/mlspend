"""Retain official failures; reject anything outside reviewed upstream defects."""

import json
import xml.etree.ElementTree as ET
from pathlib import Path


def audit(directory: Path) -> dict:
    # Exact identifiers, never a prefix wildcard. Composite failures propagate
    # from the listed leaves; supplemental checks enforce the normative prose.
    known = {
        "CAU-CommitmentDiscountStatus-C-000-C",
        "CAU-CommitmentDiscountStatus-C-002-C",
        "CAU-CommitmentDiscountStatus-C-003-C",
        "CAU-CommitmentDiscountStatus-C-004-C",
        "CAU-ContractApplied-C-000-C",
        "CAU-ContractApplied-C-003-C",
        "CAU-ContractAppliedObject-O-000-C",
        "CAU-ContractAppliedObject-O-059-M",
        "CAU-ContractAppliedObject-O-065-C",
        "CAU-CostAndUsage-D-000-M",
        "CAU-CostAndUsage-D-002-M",
    }
    reports = []
    for name in ("CostAndUsage", "ContractCommitment"):
        root = ET.parse(directory / (name + ".xml")).getroot()
        cases = list(root.iter("testcase"))
        if len(cases) < 20:
            raise ValueError("Official validation report is empty or incomplete")
        failures = [
            node.attrib.get("name", "") for node in root.iter() if node.tag in {"failure", "error"}
        ]
        if set(failures) - known or (name == "ContractCommitment" and failures):
            raise ValueError("Unreviewed official failures: " + str(failures))
        reports.append(
            {
                "dataset": name,
                "testcases": len(cases),
                "official_failures": failures,
                "unreviewed_failures": [],
            }
        )
    result = {
        "official_validator": "2.2.1",
        "compatibility_rules": "1.3.0.1",
        "status": "partial official validation; supplemental normative checks required",
        "reports": reports,
        "limitations": "1.4 active rule dependency cycle; older commitment-status predicates contradict normative prose and JSON wildcard null condition misclassifies non-null quantity. No official certification claimed.",
    }
    (directory / "summary.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


if __name__ == "__main__":
    print(json.dumps(audit(Path("results/focus")), indent=2))

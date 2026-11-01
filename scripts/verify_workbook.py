"""Recalculate the delivered workbook in LibreOffice and compare all policies."""

import json
import subprocess

from openpyxl import load_workbook

from packages.core.io import ROOT, write_json


def main() -> None:
    source = ROOT / "exports/expanded/allocation.xlsx"
    manifest = json.loads((ROOT / "results/expanded/manifest.json").read_text())
    target = ROOT / "tmp/workbook-check"
    recalculated = target / "calculated"
    recalculated.mkdir(parents=True, exist_ok=True)
    records = []
    for policy in ("even", "direct", "usage", "custom"):
        book = load_workbook(source)
        book["Allocation"]["B2"] = policy
        candidate = target / (policy + ".xlsx")
        book.save(candidate)
        subprocess.run(
            [
                "libreoffice",
                "-env:UserInstallation=file:///tmp/mlspend-lo-profile",
                "--headless",
                "--convert-to",
                "xlsx",
                "--outdir",
                str(recalculated),
                str(candidate),
            ],
            check=True,
        )
        values = load_workbook(recalculated / candidate.name, data_only=True)["Allocation"]
        differences = []
        for index, row in enumerate(manifest["allocation"], 6):
            actual = values.cell(index, 9).value
            if not isinstance(actual, (int, float)):
                raise AssertionError(f"Formula did not calculate: {policy}/{index}: {actual}")
            differences.append(abs(actual * 1000000 - row["methods"][policy]))
        if max(differences) > 2:
            raise AssertionError(
                f"Workbook differs from integer-apportioned statement: {max(differences)}"
            )
        records.append(
            {
                "policy": policy,
                "rows": len(differences),
                "max_rounding_difference_micro": max(differences),
                "formula_engine": "LibreOffice headless",
                "status": "pass",
            }
        )
    write_json(ROOT / "results/expanded/workbook-verification.json", records)
    print(json.dumps(records))


if __name__ == "__main__":
    main()

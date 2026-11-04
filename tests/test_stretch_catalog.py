import csv
from pathlib import Path

import duckdb
import pytest

from packages.stretch.catalog import export_tables, open_locked


def test_catalog_locks_bytes_and_queries_read_only(tmp_path: Path) -> None:
    manifest = {"allocation": [{"month": "2025-01", "team": "research", "methods": {"usage": 123}}]}
    study = {
        "sharing": {
            "rows": [
                {
                    "hour": 0,
                    "scenario": "shared",
                    "devices": 1,
                    "cost_micro": 456,
                    "carbon": {"kg_co2e_estimate": "0.02"},
                }
            ]
        }
    }
    export_tables(tmp_path, manifest, study)
    con = open_locked(tmp_path, tmp_path / "reader.duckdb")
    try:
        assert con.execute(
            "SELECT SUM(cost_micro) FROM mlspend.allocation WHERE method='usage'"
        ).fetchone() == (123,)
        with pytest.raises(duckdb.Error):
            con.execute("CREATE TABLE injected(a INTEGER)")
        with pytest.raises(duckdb.Error):
            con.execute("SELECT * FROM mlspend.unlisted")
        outside = tmp_path / "private.csv"
        outside.write_text("secret\nprivate\n")
        with pytest.raises(duckdb.Error):
            con.execute("SELECT * FROM read_csv(?)", [str(outside)])
    finally:
        con.close()
    table = tmp_path / "exports/readback/allocation.csv"
    with table.open("a", newline="") as stream:
        csv.writer(stream).writerow(["2025-01", "extra", "usage", 100])
    with pytest.raises(ValueError, match="bytes differ"):
        open_locked(tmp_path, tmp_path / "tampered.duckdb")

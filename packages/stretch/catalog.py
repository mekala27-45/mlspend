"""Public table exports and a locked, read-only consumer contract."""

from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any

import duckdb

from packages.core.io import file_digest, read_json, write_json


def export_tables(root: Path, manifest: dict[str, Any], study: dict[str, Any]) -> dict[str, Any]:
    destination = root / "exports/readback"
    destination.mkdir(parents=True, exist_ok=True)
    tables: dict[str, tuple[list[str], list[list[Any]], list[str]]] = {
        "allocation": (
            ["month", "team", "method", "cost_micro"],
            [
                [r["month"], r["team"], method, amount]
                for r in manifest["allocation"]
                for method, amount in sorted(r["methods"].items())
            ],
            ["month", "team", "method"],
        ),
        "gpu_sharing": (
            ["hour", "scenario", "devices", "cost_micro", "gpu_kg_co2e_estimate"],
            [
                [
                    r["hour"],
                    r["scenario"],
                    r["devices"],
                    r["cost_micro"],
                    r["carbon"]["kg_co2e_estimate"],
                ]
                for r in study["sharing"]["rows"]
            ],
            ["hour", "scenario"],
        ),
    }
    entries = []
    for name, (columns, rows, grain) in tables.items():
        path = destination / (name + ".csv")
        with path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.writer(stream, lineterminator="\n")
            writer.writerow(columns)
            writer.writerows(rows)
        entries.append(
            {
                "path": path.relative_to(root).as_posix(),
                "table": name,
                "sha256": file_digest(path),
                "bytes": path.stat().st_size,
                "rows": len(rows),
                "grain": grain,
                "columns": columns,
            }
        )
    catalog = {
        "warehouse": "mlspend",
        "tables": entries,
        "units": {
            "cost_micro": "USD / 1000000",
            "gpu_kg_co2e_estimate": "kg CO2e, GPU electricity estimate only",
        },
        "definition": "Synthetic platform data and a separately registered sharing experiment; not paid invoices or observed energy.",
        "query_example": "SELECT SUM(cost_micro) AS total_micro FROM mlspend.allocation WHERE method = 'usage'",
    }
    write_json(destination / "catalog.json", catalog)
    write_json(
        destination / "tables.lock.json",
        {
            "version": 1,
            "tables": entries,
            "catalog_sha256": file_digest(destination / "catalog.json"),
        },
    )
    return catalog


def open_locked(root: Path, database_path: Path) -> duckdb.DuckDBPyConnection:
    root = root.resolve()
    lock = read_json(root / "exports/readback/tables.lock.json")
    catalog_path = root / "exports/readback/catalog.json"
    if (
        lock["version"] != 1
        or file_digest(catalog_path) != lock["catalog_sha256"]
        or not lock["tables"]
    ):
        raise ValueError("Catalog or lock is missing or changed")
    paths = []
    names: set[str] = set()
    for entry in lock["tables"]:
        path = (root / entry["path"]).resolve()
        name = entry["table"]
        if (
            not path.is_relative_to(root / "exports/readback")
            or not re.fullmatch(r"[a-z][a-z0-9_]*", name)
            or name in names
        ):
            raise ValueError("Invalid or duplicate table identity")
        if file_digest(path) != entry["sha256"]:
            raise ValueError("Locked table bytes differ")
        paths.append(path)
        names.add(name)
    if database_path.exists():
        raise ValueError("Use a new private catalog database")
    con = duckdb.connect(str(database_path))
    try:
        con.execute("CREATE SCHEMA mlspend")
        for entry, path in zip(lock["tables"], paths, strict=True):
            escaped = str(path).replace("'", "''")
            con.execute(
                f"CREATE VIEW mlspend.{entry['table']} AS SELECT * FROM read_csv('{escaped}',header=true,sample_size=-1)"
            )
    finally:
        con.close()
    con = duckdb.connect(
        str(database_path),
        read_only=True,
        config={
            "autoinstall_known_extensions": False,
            "autoload_known_extensions": False,
            "allow_community_extensions": False,
        },
    )
    con.execute("SET allowed_paths = ?", [[str(p) for p in paths]])
    con.execute("SET enable_external_access = false")
    con.execute("SET lock_configuration = true")
    return con

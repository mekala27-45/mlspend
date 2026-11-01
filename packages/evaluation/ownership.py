from pathlib import Path
from typing import Any

import duckdb

from packages.core.io import read_json


def score(directory: Path) -> dict[str, Any]:
    truth = read_json(directory / "sealed/owners.json")
    counts = {"correct": 0, "wrong": 0, "unresolved": 0}
    with duckdb.connect(str(directory / "warehouse.duckdb"), read_only=True) as connection:
        rows = connection.execute(
            "SELECT resource,owner,COUNT(*) FROM owned WHERE team='unallocated' GROUP BY 1,2 ORDER BY 1,2"
        ).fetchall()
    for resource, owner, count in rows:
        category = (
            "unresolved"
            if owner == "unallocated"
            else ("correct" if truth[resource] == owner else "wrong")
        )
        counts[category] += count
    predicted = counts["correct"] + counts["wrong"]
    total = sum(counts.values())
    return {
        **counts,
        "population": "originally untagged observed charge rows",
        "rows": total,
        "precision": counts["correct"] / predicted if predicted else None,
        "recall": counts["correct"] / total if total else None,
    }

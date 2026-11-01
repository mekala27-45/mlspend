from copy import deepcopy

import pytest

from packages.core.io import ROOT
from packages.prices.book import PriceBook
from packages.simulator.expanded import generate, noise, simulate
from packages.warehouse.expanded import ingest, injected_defects, read_mart, violations


def test_expanded_generation_and_ingestion_are_reproducible(tmp_path):
    a = generate(tmp_path / "a", 3)
    b = generate(tmp_path / "b", 3)
    assert a == b
    result = ingest(tmp_path / "a", PriceBook(ROOT / "data/prices/expanded"))
    assert result["accepted"] == a["rows"]
    assert result["quarantined"] == result["fault_injections"] == 10
    assert result["source_defects"] == 0
    assert len(result["checks"]) == 4
    assert len(list(read_mart(tmp_path / "a", require_contract=False))) == a["rows"]
    with pytest.raises(ValueError, match="contracted observed mart"):
        list(read_mart(tmp_path / "a"))


def test_intervention_preserves_exogenous_demand():
    book = PriceBook(ROOT / "data/prices/expanded")
    baseline = list(simulate(book, hours=2))
    changed = list(simulate(book, frozenset(["rightsize", "switch_model"]), hours=2))
    original = {r["resource"]: r for r in baseline if r["service"] == "inference"}
    for row in changed:
        if row["service"] == "inference":
            assert (
                row["requests"] == original[row["resource"]]["requests"]
                or row["timestamp"] != original[row["resource"]]["timestamp"]
            )
            assert (
                row["used"] == original[row["resource"]]["used"]
                or row["timestamp"] != original[row["resource"]]["timestamp"]
            )
    assert sum(r["cost_micro"] for r in changed) < sum(r["cost_micro"] for r in baseline)
    assert noise(1, 2, "ads", "demand") == noise(1, 2, "ads", "demand")


def test_all_injected_defects_enter_quarantine():
    book = PriceBook(ROOT / "data/prices/expanded")
    sample = next(simulate(book, hours=1))
    assert not violations(sample, book, set())
    assert all(violations(row, book, {sample["id"]}) for row in injected_defects(sample))
    bad = deepcopy(sample)
    bad["cost_micro"] += 100
    assert "cost:quantity_times_rate" in violations(bad, book, set())

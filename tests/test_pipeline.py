from __future__ import annotations

import copy
import subprocess
import sys

import pytest

from packages.core.io import ROOT, file_digest, read_json
from packages.render.documents import render
from packages.simulator.generate import _charge, generate
from packages.warehouse.build import build, violation


def test_simulator_reproducible_and_warehouse_utc(tmp_path):
    first = tmp_path / "one"
    second = tmp_path / "two"
    a = generate(first, days=2)
    b = generate(second, days=2)
    assert a == b
    assert a["charge_rows"] == 48 * 16
    result = build(first, tmp_path / "warehouse.duckdb")
    assert all(row["matches"] for row in result["checks"])
    assert result["total_micro"] == a["total_micro"]
    assert file_digest(first / "charges.jsonl.gz") == file_digest(second / "charges.jsonl.gz")


def test_quarantine_rules_reject_each_defect():
    row = _charge(
        "2025-01-01T00:00:00+00:00", "ads", "x", "v1", "cpu", "workload", 100, "azure-cpu"
    )
    assert violation(row) == []
    defects = {
        "BillingCurrency": "EUR",
        "BilledCostMicro": -1,
        "EffectiveCostMicro": -1,
        "ChargePeriodEnd": "2024-01-01",
        "ResourceId": "",
        "x_Team": "",
        "x_Model": "",
        "x_PriceId": "",
        "x_CostKind": "invalid",
    }
    for key, value in defects.items():
        changed = {**row, key: value}
        assert violation(changed)
    del row["x_Model"]
    assert violation(row) == ["required_fields"]
    assert violation({}) == ["required_fields"]


def test_claim_renderer_pass_violation_empty_and_missing_section(tmp_path):
    manifest = read_json(ROOT / "results/manifest.json")
    render(manifest, check=True)
    with pytest.raises(ValueError):
        render({})
    modified = copy.deepcopy(manifest)
    modified["generation"]["total_micro"] += 1000000
    with pytest.raises(ValueError):
        render(modified, check=True)
    del modified["allocation"]
    with pytest.raises(ValueError):
        render(modified)


def test_full_data_source_totals_and_method_totals():
    manifest = read_json(ROOT / "results/manifest.json")
    assert manifest["generation"]["charge_rows"] == 8760 * 16
    assert (
        sum(row["billed_micro"] for row in manifest["monthly"])
        == manifest["generation"]["total_micro"]
    )
    for month in manifest["monthly"]:
        rows = [row for row in manifest["allocation"] if row["month"] == month["month"]]
        for method in ("even", "direct", "usage", "shapley"):
            assert sum(row["methods"][method] for row in rows) == month["billed_micro"]
    portfolio = manifest["portfolio"]
    if portfolio["rows"]:
        assert (
            sum(row["shadow_cost_micro"] for row in portfolio["rows"])
            == portfolio["priced_subtotal_micro"]
        )
        assert all(
            row["jobs"] == row["priced_jobs"] + row["unpriced_jobs"] for row in portfolio["rows"]
        )
        assert portfolio["evidence"]["report_digest"]
    else:
        assert portfolio["status"] == "not measured"


def test_hashseed_determinism_for_allocation():
    import os

    code = "from packages.core.money import apportion; import json; w={key:1 for key in {'a','b','c'}}; print(json.dumps(apportion(2,w),sort_keys=True))"
    outputs = []
    for seed in ("1", "789"):
        env = {**os.environ, "PYTHONHASHSEED": seed}
        outputs.append(
            subprocess.check_output([sys.executable, "-c", code], cwd=ROOT, env=env, text=True)
        )
    assert outputs[0] == outputs[1]

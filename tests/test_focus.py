import json

import pytest

from packages.focus.export import contract_row, cost_row, parquet, validate_rows
from packages.prices.book import PriceBook


def sample():
    return cost_row(
        {
            "id": "sample",
            "price_id": "azure-t4",
            "timestamp": "2025-01-01T00:00:00+00:00",
            "cost_micro": 526000,
            "pricing_quantity": 1,
            "team": "research",
            "resource": "sample-pod",
            "service": "inference",
            "kind": "workload",
        },
        PriceBook(),
    )


def test_mandatory_column_removal_fails():
    row = sample()
    del row["EffectiveCost"]
    with pytest.raises(ValueError, match="Missing mandatory"):
        validate_rows([row], "CostAndUsage")


def test_nullability_fails_even_when_column_exists():
    row = sample()
    row["BillingCurrency"] = None
    with pytest.raises(ValueError, match="Null forbidden"):
        validate_rows([row], "CostAndUsage")


def test_empty_validation_is_failure():
    with pytest.raises(ValueError, match="Empty"):
        validate_rows([], "CostAndUsage")


def test_arithmetic_failure_is_detected():
    row = sample()
    row["ListCost"] = "123.45"
    with pytest.raises(ValueError, match="mismatch"):
        validate_rows([row], "CostAndUsage")


def test_parquet_retains_decimal_and_null_types(tmp_path):
    import duckdb

    target = tmp_path / "focus.parquet"
    assert parquet([sample()], target, "CostAndUsage") == 1
    with duckdb.connect() as connection:
        row = connection.execute(
            "SELECT EffectiveCost, ChargeClass FROM read_parquet(?)", [str(target)]
        ).fetchone()
    assert str(row[0]) == "0.526000000000"
    assert row[1] is None


def test_contract_extension_constraints():
    book = PriceBook()
    if not any(p.id == "azure-t4-reserved-1y" for p in book.rows):
        pytest.skip("Reviewed reservation evidence is required")
    row = contract_row("simulated-contract", "azure-t4", book)
    assert validate_rows([row], "ContractCommitment") == 1
    row["ContractCommitmentApplicability"] = json.dumps(
        {"IsGlobalScope": True, "IsComplexScope": True}
    )
    with pytest.raises(ValueError, match="Conflicting"):
        validate_rows([row], "ContractCommitment")


def test_commitment_resource_link_cannot_be_bypassed():
    from packages.core.io import ROOT
    from packages.simulator.expanded import simulate

    book = PriceBook(ROOT / "data/prices/expanded")
    records = [cost_row(r, book) for r in simulate(book, hours=1) if r.get("contract_id")]
    assert len(records) == 4
    for row in records:
        assert validate_rows([row], "CostAndUsage") == 1
        row["ResourceId"] = "unrelated-workload"
        with pytest.raises(ValueError, match="must identify contract"):
            validate_rows([row], "CostAndUsage")

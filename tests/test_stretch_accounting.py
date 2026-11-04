from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st

from packages.core.io import ROOT, digest, read_json, write_json
from packages.prices.book import PriceBook
from packages.stretch.carbon import gpu_carbon, unknown_carbon
from packages.stretch.prices import compare_prices, reprice_usage
from packages.stretch.sharing import allocate_pool, pack, run_study


@given(st.lists(st.integers(min_value=1, max_value=8), min_size=0, max_size=20))
def test_placement_conserves_work_and_capacity(values: list[int]) -> None:
    requests = {str(i): v for i, v in enumerate(values)}
    bins = pack(requests)
    assert sorted(j for group in bins for j in group) == sorted(requests)
    assert all(sum(requests[j] for j in group) <= 8 for group in bins)
    assert len(bins) <= len(requests)


def test_sharing_conserves_every_policy_and_prices_actual_devices() -> None:
    demands = {"a": 2, "b": 4, "c": 7}
    bins = pack(demands)
    assert len(bins) == 2
    for bill in allocate_pool(demands, len(bins), 1234567).values():
        assert sum(bill.values()) == 2469134
    assert all(v == {} for v in allocate_pool({}, 0, 1).values())
    with pytest.raises(ValueError):
        allocate_pool({}, 1, 1)
    with pytest.raises(ValueError):
        pack({"oversized": 9})


def test_study_is_repeatable_and_does_not_mutate_plan() -> None:
    plan = {
        "seed": 3,
        "hours": 4,
        "teams": ["a", "b", "c"],
        "fraction_denominator": 8,
        "assumptions": [],
    }
    result = run_study(plan, 1001)
    assert result == run_study(plan, 1001)
    assert result["totals"]["shared"] <= result["totals"]["dedicated"]


def test_carbon_uses_energy_and_preserves_unknown() -> None:
    source = read_json(ROOT / "data/carbon/source.json")
    result = gpu_carbon(Decimal(10), source, Decimal("1.2"))
    assert Decimal(result["kwh_estimate"]) == Decimal("0.84")
    assert (
        Decimal(result["kg_co2e_estimate"])
        == Decimal("0.84") * Decimal("596.326") * Decimal("0.45359237") / 1000
    )
    assert unknown_carbon("No CPU energy")["kg_co2e_estimate"] is None
    with pytest.raises(ValueError):
        gpu_carbon(Decimal("NaN"), source, Decimal("1.2"))


def test_price_change_holds_quantity_fixed_and_leaves_unknown() -> None:
    prices = [
        {
            "price_id": "gpu",
            "unit": "hour",
            "status": "matched",
            "before_usd": "2",
            "after_usd": "3",
        }
    ]
    result = reprice_usage(
        [
            {"price_id": "gpu", "unit": "hour", "quantity": "2.5"},
            {"price_id": "unknown", "quantity": 9},
        ],
        prices,
    )
    assert result["before_subtotal_micro"] == 5000000
    assert result["after_subtotal_micro"] == 7500000
    assert result["unpriced_rows"] == 1
    assert result["rows"][1]["after_micro"] is None


def test_price_comparison_refuses_stale_and_incompatible_snapshots(tmp_path: Path) -> None:
    row = PriceBook(ROOT / "data/prices/expanded").get("azure-t4").model_dump(mode="json")

    def book(name, **changes):
        raw = {"rows": [{**row, **changes}]}
        path = tmp_path / name
        write_json(path / "book.json", raw)
        write_json(path / "lock.json", {"book_digest": digest(raw)})
        return PriceBook(path)

    old = book("before")
    stale = compare_prices(
        old, book("stale", usd="9", retrieved_date="2026-11-04"), date(2026, 12, 1)
    )[0]
    assert stale["after_usd"] is None
    wrong = compare_prices(
        old, book("wrong", unit="minute", retrieved_date="2026-12-01"), date(2026, 12, 1)
    )[0]
    assert "not comparable" in wrong["status"]
    new = compare_prices(
        old, book("after", usd="9", retrieved_date="2026-12-01"), date(2026, 12, 1)
    )[0]
    assert new["status"] == "matched"
    assert Decimal(new["change_usd"]) == Decimal(9) - Decimal(row["usd"])

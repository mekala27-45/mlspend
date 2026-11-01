from __future__ import annotations

import random
from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from packages.allocation.engine import allocate, infer_owner
from packages.allocation.shapley import quantile, shapley
from packages.core.contracts import EstimateRequest, ForecastRequest
from packages.core.gates import import_boundary, statement_gate, text_gate
from packages.core.io import ROOT, canonical, digest, read_json, write_json
from packages.core.money import apportion, dollars, microdollars
from packages.prices.book import PriceBook, normalized_rate
from packages.truth.access import read_truth
from packages.unit.economics import unit_cost


def test_apportion_conserves_random_integer_totals():
    rng = random.Random(44)
    for _ in range(400):
        weights = {f"owner-{i}": rng.random() * 100 for i in range(rng.randint(1, 9))}
        total = rng.randrange(10000000)
        result = apportion(total, weights)
        assert sum(result.values()) == total
        assert min(result.values()) >= 0
        assert result == apportion(total, dict(reversed(list(weights.items()))))


@pytest.mark.parametrize(
    "total,weights", [(-1, {"a": 1}), (2, {}), (1, {"a": -1}), (1, {"a": float("nan")})]
)
def test_bad_apportionment(total, weights):
    with pytest.raises(ValueError):
        apportion(total, weights)


def test_rounding_and_stable_ties():
    assert microdollars("1.0000005") == 1000000
    assert dollars(1250000) == "1.250000"
    assert apportion(1, {"b": 0, "a": 0}) == {"a": 1, "b": 0}
    with pytest.raises(ValueError):
        microdollars("NaN")


def test_shapley_efficiency_symmetry_and_null_player():
    values = shapley(["c", "b", "a"], lambda coalition: 4.0 if coalition & {"a", "b"} else 0.0)
    assert values == pytest.approx({"a": 2, "b": 2, "c": 0})
    assert sum(values.values()) == pytest.approx(4)
    with pytest.raises(ValueError):
        shapley([], lambda c: 0)
    with pytest.raises(ValueError):
        shapley(["a"], lambda c: 1)


def test_allocations_preserve_cost_and_validate_owners():
    result = allocate({"a": 10, "b": 20}, 17, {"a": 1, "b": 3}, {"a": 2, "b": 3})
    assert all(sum(row.values()) == 47 for row in result.values())
    with pytest.raises(ValueError):
        allocate({"a": 1}, 2, {}, {"a": 1})
    with pytest.raises(ValueError):
        allocate({"a": -1}, 2, {"a": 1}, {"a": 1})
    assert infer_owner("a", "a", "net-a", {"a"}) == ("a", 1)
    assert infer_owner("a", "shared", "net-a", {"a"}) == ("unallocated", 0)


def test_quantile():
    assert quantile([1, 3, 2], 0.5) == 2
    assert quantile([1, 3], 0.25) == 1.5
    with pytest.raises(ValueError):
        quantile([], 0.5)


def test_average_and_discrete_marginal_cost():
    row = unit_cost(1000000, 10000, 1000, 5000, 5000, 2000000)
    assert row["average_micro_per_1000"] == 100000
    assert row["marginal_micro_per_1000"] == 0
    assert (
        unit_cost(1000000, 10000, 4800, 5000, 5000, 2000000)["marginal_micro_per_1000"] == 2000000
    )
    assert unit_cost(0, 0, 0, 0, 1, 0)["average_micro_per_1000"] is None
    with pytest.raises(ValueError):
        unit_cost(-1, 1, 0, 0, 1, 1)
    with pytest.raises(ValueError):
        unit_cost(1, 1, 5, 1, 1, 1)


def test_json_is_canonical_and_rejects_nan(tmp_path):
    assert digest({"b": 1, "a": 2}) == digest({"a": 2, "b": 1})
    path = tmp_path / "x.json"
    write_json(path, {"a": 2})
    assert read_json(path) == {"a": 2}
    with pytest.raises(ValueError):
        canonical({"x": float("nan")})


def test_source_prices_are_locked_and_units_are_checked(tmp_path):
    book = PriceBook()
    assert book.get("azure-t4", date(2025, 1, 1), "hour").usd == Decimal(".526")
    with pytest.raises(ValueError):
        book.get("missing")
    with pytest.raises(ValueError):
        book.get("azure-t4", date(2020, 1, 1))
    with pytest.raises(ValueError):
        book.get("azure-t4", unit="minute")
    write_json(tmp_path / "book.json", {"rows": []})
    write_json(tmp_path / "lock.json", {"book_digest": "broken"})
    with pytest.raises(ValueError):
        PriceBook(tmp_path)
    assert normalized_rate(Decimal(2), "1000 tokens") == (Decimal(2000), "million_tokens")
    assert normalized_rate(Decimal(8760), "hour", 8760) == (Decimal(1), "hour")
    for amount, unit, hours in [
        (Decimal(-1), "1 Hour", None),
        (Decimal(1), "unknown", None),
        (Decimal(1), "hour", 0),
    ]:
        with pytest.raises(ValueError):
            normalized_rate(amount, unit, hours)


def test_contracts_reject_unexpected_fields_and_bad_intervals():
    with pytest.raises(ValidationError):
        EstimateRequest(
            price_id="x", requests_per_day=1, seconds_per_request="0", capacity_per_replica=1
        )
    with pytest.raises(ValidationError):
        EstimateRequest(
            price_id="x",
            requests_per_day=1,
            seconds_per_request="1",
            capacity_per_replica=1,
            surprise=True,
        )
    with pytest.raises(ValidationError):
        ForecastRequest(
            book="platform",
            team="ads",
            period="2099-01",
            point_usd="3",
            lower_usd="4",
            upper_usd="5",
            data_cutoff="2098-12-31",
        )
    with pytest.raises(ValidationError):
        ForecastRequest(
            book="platform",
            team="ads",
            period="2099-01",
            point_usd="3",
            lower_usd="2",
            upper_usd="5",
            data_cutoff="2099-01-01",
        )


def test_gates_pass_violate_and_refuse_empty(tmp_path):
    text_gate({"x": "A measured result."})
    for value in ("bad" + chr(0x2014) + "dash", "a seamless system", "ghp_" + "a" * 25):
        with pytest.raises(ValueError):
            text_gate({"x": value})
    with pytest.raises(ValueError):
        text_gate({})
    statement_gate({"x": "The statement"}, "The statement")
    with pytest.raises(ValueError):
        statement_gate({"x": "missing"}, "The statement")
    with pytest.raises(ValueError):
        statement_gate({}, "The statement")
    import_boundary(ROOT / "packages")
    with pytest.raises(ValueError):
        import_boundary(tmp_path)
    (tmp_path / "allocation").mkdir()
    (tmp_path / "allocation" / "bad.py").write_text("from packages.truth import access")
    with pytest.raises(ValueError):
        import_boundary(tmp_path)
    with pytest.raises(PermissionError):
        read_truth(tmp_path / "nothing")

from decimal import Decimal

import pytest

from packages.api.sizing import alternatives
from packages.core.contracts import EstimateRequest
from packages.core.io import ROOT
from packages.prices.book import PriceBook


def test_token_components_reconcile_and_cache_reduces_cost():
    book = PriceBook(ROOT / "data/prices/expanded")
    request = EstimateRequest(
        requests_per_day=1000,
        days=1,
        model_size_class="small",
        hosting_option="model_api",
        tokens_in_per_request=1000,
        tokens_out_per_request=200,
    )
    rows = alternatives(request, book)
    assert len(rows) == 2
    for row in rows:
        assert sum(Decimal(v) for v in row["components_usd"].values()) == Decimal(row["cost_usd"])
        assert all(p["source_digest"] for p in row["price_rows"])
    cached = alternatives(request.model_copy(update={"cached_input_fraction": Decimal(1)}), book)
    assert all(
        Decimal(b["cost_usd"]) < Decimal(a["cost_usd"]) for a, b in zip(rows, cached, strict=True)
    )


def test_sizing_threshold_and_large_class_filter():
    request = EstimateRequest(
        requests_per_day=86401,
        seconds_per_request="1",
        days=1,
        model_size_class="large",
        hosting_option="azure",
        minimum_replicas=0,
    )
    rows = alternatives(request, PriceBook(ROOT / "data/prices/expanded"))
    assert [r["option"] for r in rows] == ["azure-a100"]
    assert rows[0]["replicas"] == 2


def test_sizing_empty_demand_and_invalid_fraction():
    book = PriceBook(ROOT / "data/prices/expanded")
    request = EstimateRequest(requests_per_day=0, model_size_class="small", minimum_replicas=0)
    assert all(Decimal(r["cost_usd"]) == 0 for r in alternatives(request, book))
    with pytest.raises(ValueError):
        EstimateRequest(requests_per_day=1, cached_input_fraction="1.1")

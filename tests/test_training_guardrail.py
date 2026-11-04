from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import text

from packages.api.storage import Store
from packages.core.io import ROOT
from packages.prices.book import PriceBook
from packages.stretch.guardrail import BudgetRequest, Guardrail, TrainingRequest, forecast_training


def test_guardrail_serializes_concurrent_jobs_and_replays(tmp_path: Path) -> None:
    store = Store(f"sqlite:///{tmp_path / 'admissions.db'}", "guardrail-test-salt-not-a-credential")
    guard = Guardrail(store.engine)
    book = PriceBook(ROOT / "data/prices/expanded")
    job = TrainingRequest(request_id=uuid4(), hours=Decimal(1))
    amount = forecast_training(job, book)["forecast_micro"]
    budget = guard.create_budget(BudgetRequest(limit_usd=Decimal(amount * 3) / 1000000))
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(
            pool.map(
                lambda _: guard.admit(
                    budget["id"], TrainingRequest(request_id=uuid4(), hours=Decimal(1)), book
                ),
                range(20),
            )
        )
    assert sum(r["accepted"] for r in results) == 3
    assert all(r["remaining_after_micro"] >= 0 for r in results)
    with store.engine.connect() as con:
        assert (
            con.execute(
                text("SELECT reserved_micro FROM mlspend_training_budget WHERE id=:id"),
                {"id": budget["id"]},
            ).scalar_one()
            == amount * 3
        )
    with ThreadPoolExecutor(max_workers=8) as pool:
        replay = list(pool.map(lambda _: guard.admit(budget["id"], job, book), range(10)))
    assert sum(not r["replayed"] for r in replay) == 1
    assert not any(r["accepted"] for r in replay)
    with pytest.raises(ValueError, match="different job"):
        guard.admit(budget["id"], job.model_copy(update={"hours": Decimal(2)}), book)


def test_planted_weekend_sweep_and_unknown_budget_fail_closed(tmp_path: Path) -> None:
    store = Store(f"sqlite:///{tmp_path / 'sweep.db'}", "guardrail-test-salt-not-a-credential")
    guard = Guardrail(store.engine)
    book = PriceBook(ROOT / "data/prices/expanded")
    budget = guard.create_budget(BudgetRequest(limit_usd=Decimal(100)))
    sweep = TrainingRequest(
        request_id=uuid4(), price_id="azure-a100", gpu_count=8, hours=Decimal(48), attempts=3
    )
    refused = guard.admit(budget["id"], sweep, book)
    assert not refused["accepted"]
    assert refused["remaining_after_micro"] == 100000000
    small = TrainingRequest(request_id=uuid4(), hours=Decimal(1))
    assert guard.admit(budget["id"], small, book)["accepted"]
    with pytest.raises(KeyError):
        guard.admit(str(uuid4()), small, book)


def test_forecast_rounds_up_and_rejects_free_retry_or_fractional_devices() -> None:
    with pytest.raises(ValueError):
        TrainingRequest(request_id=uuid4(), hours=Decimal(1), attempts=0)
    with pytest.raises(ValueError):
        TrainingRequest(request_id=uuid4(), hours=Decimal(1), gpu_count=1.2)

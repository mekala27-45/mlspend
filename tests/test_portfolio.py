import pytest

from packages.portfolio.usage import price_job
from packages.prices.book import PriceBook


def job(seconds="01:01", labels=None):
    return {
        "id": 1,
        "html_url": "https://github.com/example/project/actions/runs/1/job/1",
        "started_at": "2026-10-01T00:00:00Z",
        "completed_at": "2026-10-01T00:" + seconds + "Z",
        "labels": labels or ["ubuntu-latest"],
        "conclusion": "success",
    }


def test_shadow_pricing_rounds_each_job_not_total():
    book = PriceBook()
    rows = [price_job("example/project", job(), book) for _ in range(2)]
    assert sum(r["minutes"] for r in rows) == 4
    assert sum(r["cost_micro"] for r in rows) == 24000


def test_unknown_and_unfinished_jobs_are_not_zero_cost():
    book = PriceBook()
    assert price_job("example/project", job(labels=["self-hosted"]), book)["cost_micro"] is None
    missing = job()
    missing["completed_at"] = None
    assert price_job("example/project", missing, book)["cost_micro"] is None


def test_negative_duration_refuses():
    bad = job()
    bad["completed_at"] = "2026-09-30T23:59:00Z"
    with pytest.raises(ValueError):
        price_job("example/project", bad, PriceBook())

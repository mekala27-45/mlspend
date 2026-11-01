"""Close real public CI forecasts only after complete measured actuals are available."""

import calendar
import os
from datetime import UTC, datetime, timedelta

from packages.api.storage import Store
from packages.core.io import ROOT, read_json, write_json
from scripts.fetch_portfolio_usage import main as fetch_usage


def main() -> None:
    today = datetime.now(UTC)
    period = os.environ.get("PERIOD") or (today.replace(day=1) - timedelta(days=1)).strftime(
        "%Y-%m"
    )
    start = datetime.strptime(period, "%Y-%m").replace(tzinfo=UTC)
    end = start + timedelta(days=calendar.monthrange(start.year, start.month)[1])
    if end > today:
        raise ValueError("Future actuals cannot be measured or scored")
    target = ROOT / "results/period-close" / period
    target.mkdir(parents=True, exist_ok=True)
    if not os.environ.get("DATABASE_URL") or not os.environ.get("MLSPEND_SALT"):
        write_json(
            target / "status.json",
            {
                "status": "configuration_required",
                "period": period,
                "reason": "Separate scoped period-close credentials are required; no forecast was scored",
            },
        )
        raise RuntimeError("Period-close credentials are not configured")
    request = read_json(ROOT / "requests/portfolio.json")
    request.update(start=start.isoformat(), end_exclusive=end.isoformat())
    request_path = target / "request.json"
    write_json(request_path, request)
    report_path = target / "usage.json"
    fetch_usage(request_path=request_path, output_path=report_path, cache_path=target / "cache")
    report = read_json(report_path)
    # This scope is explicit in the forecast identity; unpriced components are
    # excluded rather than falsely calling the known subtotal a whole bill.
    actuals = {
        "portfolio:" + r["repository"].split("/")[1] + "-ci-known-subtotal": r["shadow_cost_micro"]
        for r in report["rows"]
    }
    write_json(target / "actuals.json", actuals)
    store = Store(os.environ["DATABASE_URL"], os.environ["MLSPEND_SALT"])
    scored = store.close_period(period, actuals, today)
    write_json(
        target / "status.json",
        {
            "status": "closed",
            "period": period,
            "scored": scored,
            "scope": "Known priced public CI subtotal; no missing component treated as zero",
            "price_digest": report["price_digest"],
        },
    )
    print({"period": period, "scored": scored})


if __name__ == "__main__":
    main()

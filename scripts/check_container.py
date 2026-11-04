"""Exercise the real port-80 container, then read its committed row independently."""

import json
import os
import statistics
import subprocess
import time
from datetime import date

import httpx

from packages.api.storage import Store
from packages.core.io import ROOT, write_json


def main() -> None:
    started = time.perf_counter()
    base = os.environ.get("MLSPEND_CONTAINER_URL", "http://127.0.0.1")
    with httpx.Client(timeout=10, trust_env=False) as client:
        for _ in range(150):
            try:
                response = client.get(base + "/health")
                if response.status_code == 200:
                    break
            except httpx.HTTPError:
                pass
            time.sleep(0.1)
        else:
            raise AssertionError("Container never became ready")
        ready = response.json()
        startup = time.perf_counter() - started
        estimate = client.post(
            base + "/v1/estimate",
            json={
                "requests_per_day": 100000,
                "model_size_class": "small",
                "tokens_in_per_request": 1000,
                "tokens_out_per_request": 250,
            },
        )
        estimate.raise_for_status()
        identifier = estimate.json()["id"]
        # This host process is distinct from the container process and connection.
        store = Store(os.environ["DATABASE_URL"], os.environ["MLSPEND_SALT"])
        row = store.get(identifier)
        assert row is not None and row["kind"] == "estimate"
        assert json.loads(row["result"])["options"] == estimate.json()["options"]
        forecast = client.post(
            base + "/v1/forecasts",
            json={
                "book": "portfolio",
                "team": "container-check",
                "period": "2099-01",
                "data_cutoff": date.today().isoformat(),
                "point_usd": "1",
                "lower_usd": "0",
                "upper_usd": "2",
            },
        )
        forecast.raise_for_status()
        assert store.get(forecast.json()["id"])["scored_at"] is None
        timings, meters = [], []
        for _ in range(20):
            begin = time.perf_counter()
            response = client.get(base + "/health")
            response.raise_for_status()
            assert response.json()["instance_id"] == ready["instance_id"]
            timings.append((time.perf_counter() - begin) * 1000)
            meters.append(float(response.headers["X-Shadow-Cost-USD"]))
        result = {
            "container_port": 80,
            "independent_postgres_readback": "pass",
            "forecast_committed": True,
            "controlled_container_time_to_ready_ms": startup * 1000,
            "process_uptime_at_readiness": ready["process_uptime_seconds"],
            "warm_samples": len(timings),
            "warm_p50_ms": statistics.median(timings),
            "warm_p99_ms": max(timings),
            "request_shadow_median_usd": statistics.median(meters),
            "request_shadow_p99_usd": max(meters),
            "hosting_cold_start": "not inferred from local container readiness",
        }
        write_json(ROOT / "results/container-verification.json", result)
        print(json.dumps(result))
    subprocess.run(["docker", "stop", "mlspend-check"], check=True)


if __name__ == "__main__":
    main()

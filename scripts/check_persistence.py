from __future__ import annotations

import json
import os
import secrets
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from datetime import date
from pathlib import Path

from packages.core.io import ROOT, write_json


def run() -> dict[str, object]:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    with tempfile.TemporaryDirectory(prefix="mlspend-", dir=ROOT / "tmp") as temp:
        database = "sqlite:///" + str(Path(temp) / "log.sqlite")
        salt = secrets.token_hex(32)
        environment = {**os.environ, "DATABASE_URL": database, "MLSPEND_SALT": salt}
        server = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "packages.api.app:app",
                "--host",
                "127.0.0.1",
                "--port",
                str(port),
            ],
            cwd=ROOT,
            env=environment,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            base = f"http://127.0.0.1:{port}"
            for _ in range(100):
                try:
                    urllib.request.urlopen(base + "/health", timeout=1).close()
                    break
                except OSError:
                    time.sleep(0.1)
            request = {
                "book": "portfolio",
                "team": "search",
                "period": "2099-01",
                "point_usd": "1",
                "lower_usd": "0",
                "upper_usd": "2",
                "data_cutoff": date.today().isoformat(),
            }
            started = time.perf_counter()
            payload = urllib.request.Request(
                base + "/v1/forecasts",
                data=json.dumps(request).encode(),
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(payload, timeout=10) as response:
                created = json.load(response)
            elapsed = time.perf_counter() - started
            probe = "from packages.api.storage import Store;import os,sys; row=Store(os.environ['DATABASE_URL'],os.environ['MLSPEND_SALT']).get(sys.argv[1]); assert row is not None; print(row['kind'])"
            actual = subprocess.check_output(
                [sys.executable, "-c", probe, created["id"]], env=environment, cwd=ROOT, text=True
            ).strip()
            if actual != "forecast":
                raise AssertionError("Independent process did not observe committed forecast")
            result = {
                "independent_process": "pass",
                "engine": "SQLite local only",
                "first_forecast_seconds": elapsed,
                "production_cold_start": "not measured",
            }
        finally:
            server.terminate()
            server.wait(timeout=10)
        write_json(ROOT / "results/persistence.json", result)
        return result


if __name__ == "__main__":
    (ROOT / "tmp").mkdir(exist_ok=True)
    print(run())

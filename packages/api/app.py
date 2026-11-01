from __future__ import annotations

import asyncio
import math
import os
import time
import uuid
from datetime import date
from pathlib import Path
from typing import Any

import psutil
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from starlette.exceptions import HTTPException as StarletteHTTPException

from packages.api.sizing import alternatives
from packages.api.storage import Store
from packages.core.contracts import EstimateRequest, ForecastRequest
from packages.core.io import ROOT, STATEMENT, read_json
from packages.prices.book import PriceBook


def estimate_workload(request: EstimateRequest, book: PriceBook) -> dict[str, Any]:
    selected = book.get(request.price_id, unit="hour")
    required_seconds = request.requests_per_day * float(request.seconds_per_request)
    replicas = max(
        request.minimum_replicas,
        math.ceil(required_seconds / (86400 * request.capacity_per_replica)),
    )
    total = selected.usd * replicas * 24 * request.days
    return {
        "options": alternatives(request, PriceBook(ROOT / "data/prices/expanded"))
        if request.model_size_class is not None
        else [],
        "shadow_cost_usd": str(total),
        "currency": "USD",
        "days": request.days,
        "replicas": replicas,
        "price_id": selected.id,
        "price_source": selected.source_url,
        "price_read_on": str(selected.retrieved_date),
        "assumptions": [
            "Constant demand across each day",
            "Capacity is supplied by the caller, not a benchmark",
            "Full replicas are reserved for the entire period",
            "Network, storage and model tokens are excluded",
        ],
        "statement": STATEMENT,
    }


def create_app(
    database_url: str | None = None,
    salt: str | None = None,
    manifest_path: Path = ROOT / "results/expanded/manifest.json",
) -> FastAPI:
    api = FastAPI(title="mlspend", description=STATEMENT, docs_url=None, redoc_url=None)
    book = PriceBook(ROOT / "data/prices/expanded")
    manifest: dict[str, Any] | None = read_json(manifest_path) if manifest_path.exists() else None
    url = database_url or os.environ.get("DATABASE_URL")
    selected_salt = salt or os.environ.get("MLSPEND_SALT")
    store = Store(url, selected_salt) if url and selected_salt else None
    api.state.store = store
    origins = os.environ.get("MLSPEND_CORS_ORIGINS", "https://mekala27-45.github.io").split(",")
    api.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
        expose_headers=[
            "X-Shadow-Cost-USD",
            "X-CPU-Seconds",
            "X-Memory-Bytes",
            "X-Meter-Basis",
            "X-Price-Ids",
        ],
    )
    serial = asyncio.Lock()
    samples: list[float] = []
    instance = str(uuid.uuid4())
    process_start = time.monotonic()

    @api.middleware("http")
    async def meter(request: Request, call_next: Any) -> Any:
        async with serial:
            start_cpu, start_wall = time.process_time_ns(), time.perf_counter_ns()
            start_memory = psutil.Process().memory_info().rss
            if (
                request.url.path != "/health"
                and store is not None
                and not store.permit(
                    request.client.host if request.client else "unknown", time.time()
                )
            ):
                response = JSONResponse(
                    {"detail": "Hourly client budget exhausted", "statement": STATEMENT},
                    status_code=429,
                )
            else:
                try:
                    response = await call_next(request)
                except Exception:
                    response = JSONResponse(
                        {"detail": "Request failed", "statement": STATEMENT}, status_code=500
                    )
            cpu_seconds = (time.process_time_ns() - start_cpu) / 1e9
            wall_seconds = (time.perf_counter_ns() - start_wall) / 1e9
            memory_bytes = max(start_memory, psutil.Process().memory_info().rss)
            memory = memory_bytes / (1024**3)
            cpu = book.get("vercel-cpu", unit="cpu_hour")
            ram = book.get("vercel-memory", unit="gb_hour")
            cost = cpu_seconds / 3600 * float(cpu.usd) + wall_seconds * memory / 3600 * float(
                ram.usd
            )
            samples.append(cost)
            if len(samples) > 10000:
                del samples[:5000]
            response.headers["X-Shadow-Cost-USD"] = f"{cost:.12f}"
            response.headers["X-CPU-Seconds"] = f"{cpu_seconds:.9f}"
            response.headers["X-Memory-Bytes"] = str(memory_bytes)
            response.headers["X-Price-Ids"] = f"{cpu.id},{ram.id}"
            response.headers["X-Meter-Basis"] = (
                "serialized process CPU and max of start/end process RSS times wall time; includes process baseline, excludes startup and idle lifetime; not provider billing"
            )
            response.headers["X-MLSpend-Statement"] = STATEMENT
            return response

    @api.exception_handler(StarletteHTTPException)
    async def http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        return JSONResponse(
            {"detail": exc.detail, "statement": STATEMENT},
            status_code=exc.status_code,
            headers=exc.headers,
        )

    @api.exception_handler(RequestValidationError)
    async def invalid_request(_: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse({"detail": str(exc), "statement": STATEMENT}, status_code=422)

    @api.get("/health")
    def health() -> JSONResponse:
        ordered = sorted(samples)
        database_status = "not configured"
        if store:
            try:
                with store.engine.connect() as connection:
                    connection.execute(text("SELECT 1"))
                database_status = "connected"
            except Exception:
                database_status = "unavailable"
        ready = database_status == "connected" and bool(manifest)
        result = {
            "status": "ready"
            if database_status == "connected" and manifest
            else "configuration_required",
            "version": "0.1.0-dev",
            "instance_id": instance,
            "process_uptime_seconds": round(time.monotonic() - process_start, 3),
            "database": database_status,
            "price_digest": book.digest,
            "data_digest": (
                manifest["generation"].get("observed_sha256")
                or manifest["generation"].get("charges_sha256")
            )
            if manifest
            else None,
            "meter_median_usd": ordered[len(ordered) // 2] if ordered else None,
            "meter_p99_usd": ordered[min(len(ordered) - 1, math.ceil(len(ordered) * 0.99) - 1)]
            if ordered
            else None,
            "statement": STATEMENT,
        }
        return JSONResponse(
            result, status_code=200 if ready else 503, headers={} if ready else {"Retry-After": "5"}
        )

    def results() -> dict[str, Any]:
        if manifest is None:
            raise HTTPException(503, "Build results before serving")
        return manifest

    @api.get("/v1/showback")
    def showback(
        team: str | None = None, month: str | None = None, method: str = "usage"
    ) -> dict[str, Any]:
        if method not in ("even", "direct", "usage", "custom", "shapley"):
            raise HTTPException(422, "Unknown allocation method")
        data = results()
        period = month or max(r["month"] for r in data["allocation"])
        rows = [
            {
                "team": r["team"],
                "month": r["month"],
                "cost_micro": r["methods"][method],
                "currency": "USD",
            }
            for r in data["allocation"]
            if r["month"] == period and (team is None or r["team"] == team)
        ]
        if not rows:
            raise HTTPException(404, "No matching statement")
        return {"method": method, "rows": rows, "statement": STATEMENT}

    @api.get("/v1/unit-costs")
    def units(model: str | None = None, month: str | None = None) -> dict[str, Any]:
        data = results()
        return {
            "rows": [
                r
                for r in data.get("units", data.get("unit_costs", []))
                if r["month"] == (month or max(v["month"] for v in data["allocation"]))
                and (model is None or r["model"] == model)
            ],
            "statement": STATEMENT,
        }

    @api.get("/v1/anomalies")
    def anomalies() -> dict[str, Any]:
        data = results()
        return {"results": data.get("detection", data.get("detector")), "statement": STATEMENT}

    @api.post("/v1/estimate")
    def estimate(request: EstimateRequest) -> dict[str, Any]:
        if store is None:
            raise HTTPException(503, "Persistent estimate log is not configured")
        try:
            result = estimate_workload(request, book)
        except ValueError as error:
            raise HTTPException(422, str(error)) from error
        identifier = store.append("estimate", request.model_dump(mode="json"), result)
        return {"id": identifier, **result}

    @api.get("/v1/estimates/{identifier}")
    def get_estimate(identifier: str) -> dict[str, Any]:
        if store is None:
            raise HTTPException(503, "Estimate log is not configured")
        row = store.get(identifier)
        if row is None or row["kind"] != "estimate":
            raise HTTPException(404, "Estimate not found")
        return {"estimate": row, "statement": STATEMENT}

    @api.post("/v1/forecasts")
    def forecast(request: ForecastRequest) -> dict[str, Any]:
        if store is None:
            raise HTTPException(503, "Persistent forecast log is not configured")
        if request.data_cutoff > date.today():
            raise HTTPException(422, "The data cutoff cannot be in the future")
        if date.fromisoformat(request.period + "-01") <= date.today():
            raise HTTPException(
                422, "Only future periods may be logged; simulated backtests are kept separately"
            )
        result = {
            "point_usd": str(request.point_usd),
            "lower_usd": str(request.lower_usd),
            "upper_usd": str(request.upper_usd),
            "currency": "USD",
            "period": request.period,
            "statement": STATEMENT,
        }
        identifier = store.append(
            "forecast", request.model_dump(mode="json"), result, request.period
        )
        return {"id": identifier, **result}

    @api.get("/v1/forecasts/{identifier}")
    def get_forecast(identifier: str) -> dict[str, Any]:
        if store is None:
            raise HTTPException(503, "Forecast log is not configured")
        row = store.get(identifier)
        if row is None or row["kind"] != "forecast":
            raise HTTPException(404, "Forecast not found")
        return {"forecast": row, "statement": STATEMENT}

    return api


app = create_app()

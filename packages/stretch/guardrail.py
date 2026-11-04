"""Atomic admission reservations for explicitly simulated training budgets."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from decimal import ROUND_CEILING, Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import BigInteger, Column, Engine, text
from sqlmodel import Field as DBField
from sqlmodel import SQLModel

from packages.core.io import digest
from packages.prices.book import PriceBook


class DemoBudget(SQLModel, table=True):
    __tablename__ = "mlspend_training_budget"
    id: str = DBField(primary_key=True)
    limit_micro: int = DBField(sa_column=Column(BigInteger, nullable=False))
    reserved_micro: int = DBField(sa_column=Column(BigInteger, nullable=False))
    created_at: str


class Admission(SQLModel, table=True):
    __tablename__ = "mlspend_training_admission"
    budget_id: str = DBField(primary_key=True)
    request_id: str = DBField(primary_key=True)
    request_digest: str
    result: str
    created_at: str


class BudgetRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    limit_usd: Decimal = Field(
        default=Decimal("100"), gt=0, le=1000000, max_digits=13, decimal_places=6
    )


class TrainingRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_id: uuid.UUID
    price_id: Literal["azure-t4", "azure-v100", "azure-a100"] = "azure-t4"
    gpu_count: int = Field(default=1, ge=1, le=128, strict=True)
    hours: Decimal = Field(gt=0, le=720, max_digits=9, decimal_places=6)
    attempts: int = Field(default=1, ge=1, le=100, strict=True)


def forecast_training(request: TrainingRequest, book: PriceBook) -> dict[str, Any]:
    price = book.get(request.price_id, unit="hour")
    amount = price.usd * request.gpu_count * request.hours * request.attempts
    return {
        "forecast_micro": int((amount * 1000000).to_integral_value(rounding=ROUND_CEILING)),
        "price_id": price.id,
        "price_digest": book.digest,
        "source_url": price.source_url,
        "retrieved_date": str(price.retrieved_date),
        "assumptions": "Requested capacity-hours for all attempts at locked list prices. Excludes storage, network and workload runtime overruns.",
    }


class Guardrail:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def create_budget(self, request: BudgetRequest) -> dict[str, Any]:
        identifier = str(uuid.uuid4())
        limit = int(request.limit_usd * 1000000)
        with self.engine.begin() as con:
            con.execute(
                text(
                    "INSERT INTO mlspend_training_budget (id,limit_micro,reserved_micro,created_at) VALUES (:id,:limit,0,:now)"
                ),
                {"id": identifier, "limit": limit, "now": datetime.now(UTC).isoformat()},
            )
        return {
            "id": identifier,
            "limit_micro": limit,
            "reserved_micro": 0,
            "mode": "isolated simulation; no real training jobs",
        }

    def admit(self, budget_id: str, request: TrainingRequest, book: PriceBook) -> dict[str, Any]:
        payload_digest = digest(request.model_dump(mode="json"))
        request_id = str(request.request_id)
        with self.engine.begin() as con:
            # A write lock serializes both the idempotency lookup and balance update.
            # PostgreSQL locks this budget row; SQLite serializes writers for this test store.
            budget = (
                con.execute(
                    text(
                        "UPDATE mlspend_training_budget SET reserved_micro=reserved_micro WHERE id=:id RETURNING limit_micro,reserved_micro"
                    ),
                    {"id": budget_id},
                )
                .mappings()
                .first()
            )
            if budget is None:
                raise KeyError("Unknown simulation budget")
            prior = (
                con.execute(
                    text(
                        "SELECT request_digest,result FROM mlspend_training_admission WHERE budget_id=:budget AND request_id=:request"
                    ),
                    {"budget": budget_id, "request": request_id},
                )
                .mappings()
                .first()
            )
            if prior:
                if prior["request_digest"] != payload_digest:
                    raise ValueError("Request identifier was already used for a different job")
                result: dict[str, Any] = json.loads(prior["result"])
                return {**result, "replayed": True}
            forecast = forecast_training(request, book)
            remaining = budget["limit_micro"] - budget["reserved_micro"]
            accepted = forecast["forecast_micro"] <= remaining
            result = {
                **forecast,
                "budget_id": budget_id,
                "request_id": request_id,
                "accepted": accepted,
                "remaining_before_micro": remaining,
                "remaining_after_micro": remaining - forecast["forecast_micro"]
                if accepted
                else remaining,
                "reserved_micro": forecast["forecast_micro"] if accepted else 0,
                "mode": "simulation reservation only; no job was launched",
                "replayed": False,
                "reason": "Within remaining forecast budget"
                if accepted
                else "Forecast exceeds remaining budget",
            }
            if accepted:
                con.execute(
                    text(
                        "UPDATE mlspend_training_budget SET reserved_micro=reserved_micro+:amount WHERE id=:id"
                    ),
                    {"id": budget_id, "amount": forecast["forecast_micro"]},
                )
            con.execute(
                text(
                    "INSERT INTO mlspend_training_admission (budget_id,request_id,request_digest,result,created_at) VALUES (:budget,:request,:digest,:result,:now)"
                ),
                {
                    "budget": budget_id,
                    "request": request_id,
                    "digest": payload_digest,
                    "result": json.dumps(result, sort_keys=True),
                    "now": datetime.now(UTC).isoformat(),
                },
            )
        return result

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True, allow_inf_nan=False)


class Price(StrictModel):
    id: str
    provider: str
    service: str
    sku: str
    region: str
    unit: str
    usd: Decimal = Field(ge=0)
    term: str
    effective_date: date
    retrieved_date: date
    source_url: str
    source_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_kind: Literal["provider_response", "retrieval_snapshot", "fixture"]


class EstimateRequest(StrictModel):
    price_id: str = "azure-t4"
    requests_per_day: int = Field(ge=0, le=100000000)
    seconds_per_request: Decimal = Field(gt=0, le=3600, default=Decimal("0.1"))
    capacity_per_replica: int = Field(ge=1, le=1000000, default=1)
    minimum_replicas: int = Field(ge=0, le=10000, default=1)
    days: int = Field(ge=1, le=366, default=30)
    model_size_class: Literal["small", "medium", "large"] | None = None
    tokens_in_per_request: int = Field(ge=0, le=1000000, default=0)
    tokens_out_per_request: int = Field(ge=0, le=1000000, default=0)
    cached_input_fraction: Decimal = Field(ge=0, le=1, default=Decimal(0))
    hosting_option: Literal["all", "azure", "aws", "model_api"] = "all"


class ForecastRequest(StrictModel):
    book: Literal["platform", "portfolio"]
    team: str
    period: str = Field(pattern=r"^20\d{2}-(0[1-9]|1[0-2])$")
    point_usd: Decimal = Field(ge=0)
    lower_usd: Decimal = Field(ge=0)
    upper_usd: Decimal = Field(ge=0)
    data_cutoff: date

    @model_validator(mode="after")
    def ordered_interval(self) -> ForecastRequest:
        if not self.lower_usd <= self.point_usd <= self.upper_usd:
            raise ValueError("The point must lie inside the interval")
        if self.data_cutoff >= date.fromisoformat(self.period + "-01"):
            raise ValueError("Forecast inputs must end before the forecast period")
        return self

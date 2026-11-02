from __future__ import annotations

import hashlib
import hmac
import json
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import BigInteger, Column, text
from sqlmodel import Field, SQLModel, create_engine


class RequestLog(SQLModel, table=True):
    __tablename__ = "mlspend_request_log"
    id: str = Field(primary_key=True)
    kind: str = Field(index=True)
    created_at: str
    payload: str
    result: str
    period: str | None = Field(default=None, index=True)
    scored_at: str | None = None
    actual_micro: int | None = Field(default=None, sa_column=Column(BigInteger, nullable=True))


class ClientBudget(SQLModel, table=True):
    __tablename__ = "mlspend_client_budget"
    client_hash: str = Field(primary_key=True)
    window: int = Field(primary_key=True)
    count: int


class Store:
    def __init__(self, url: str, salt: str) -> None:
        if len(salt) < 24:
            raise ValueError("A client hashing salt of at least 24 characters is required")
        if url.startswith("postgres://"):
            url = "postgresql+psycopg://" + url[len("postgres://") :]
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+psycopg://", 1)
        self.engine = create_engine(
            url,
            connect_args={"check_same_thread": False}
            if url.startswith("sqlite")
            else {"options": "-c search_path=mlspend,public"},
            pool_pre_ping=True,
        )
        self.salt = salt.encode()
        if url.startswith("sqlite"):
            SQLModel.metadata.create_all(self.engine)

    def permit(self, address: str, now: float, cap: int = 60) -> bool:
        hashed = hmac.new(self.salt, address.encode(), hashlib.sha256).hexdigest()
        window = int(now // 3600)
        with self.engine.begin() as connection:
            result = connection.execute(
                text("""INSERT INTO mlspend_client_budget (client_hash, "window", count) VALUES (:client, :window, 1)
                ON CONFLICT (client_hash, "window") DO UPDATE SET count = mlspend_client_budget.count + 1
                WHERE mlspend_client_budget.count < :cap RETURNING count"""),
                {"client": hashed, "window": window, "cap": cap},
            ).first()
        return result is not None

    def append(
        self, kind: str, payload: dict[str, Any], result: dict[str, Any], period: str | None = None
    ) -> str:
        identifier = str(uuid.uuid4())
        with self.engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO mlspend_request_log (id, kind, created_at, payload, result, period) VALUES (:id,:kind,:created,:payload,:result,:period)"
                ),
                {
                    "id": identifier,
                    "kind": kind,
                    "created": datetime.now(UTC).isoformat(),
                    "payload": json.dumps(payload, sort_keys=True),
                    "result": json.dumps(result, sort_keys=True),
                    "period": period,
                },
            )
        return identifier

    def get(self, identifier: str) -> dict[str, Any] | None:
        with self.engine.connect() as connection:
            row = (
                connection.execute(
                    text("SELECT * FROM mlspend_request_log WHERE id=:id"), {"id": identifier}
                )
                .mappings()
                .first()
            )
            return dict(row) if row else None

    def close_period(self, period: str, actuals: dict[str, int], now: datetime) -> int:
        if any(not isinstance(value, int) or value < 0 for value in actuals.values()):
            raise ValueError("Actuals must be nonnegative integer microdollars")
        year, month = map(int, period.split("-"))
        close = datetime(year + (month == 12), 1 if month == 12 else month + 1, 1, tzinfo=UTC)
        if now < close:
            raise ValueError("Period has not closed")
        updated = 0
        with self.engine.begin() as connection:
            rows = (
                connection.execute(
                    text(
                        "SELECT * FROM mlspend_request_log WHERE period=:period AND kind='forecast' AND scored_at IS NULL"
                    ),
                    {"period": period},
                )
                .mappings()
                .all()
            )
            for row in rows:
                payload = json.loads(row["payload"])
                key = f"{payload['book']}:{payload['team']}"
                if key not in actuals:
                    raise ValueError(f"Missing actual for {key}; close is atomic")
                connection.execute(
                    text(
                        "UPDATE mlspend_request_log SET scored_at=:now, actual_micro=:actual WHERE id=:id AND scored_at IS NULL"
                    ),
                    {"now": now.isoformat(), "actual": actuals[key], "id": row["id"]},
                )
                updated += 1
        return updated

    def close_simulation(
        self, period: str, simulation_id: str, actuals: dict[str, int], simulated_now: datetime
    ) -> int:
        """Advance only an explicitly labeled simulation; preserve real recording time."""
        if any(type(value) is not int or value < 0 for value in actuals.values()):
            raise ValueError("Actuals must be nonnegative integer microdollars")
        year, month = map(int, period.split("-"))
        end = datetime(year + (month == 12), 1 if month == 12 else month + 1, 1, tzinfo=UTC)
        if simulated_now < end:
            raise ValueError("Simulation period has not closed")
        updated = 0
        with self.engine.begin() as connection:
            candidates = (
                connection.execute(
                    text(
                        "SELECT * FROM mlspend_request_log WHERE period=:period AND kind='simulation_forecast'"
                    ),
                    {"period": period},
                )
                .mappings()
                .all()
            )
            rows = [
                r
                for r in candidates
                if json.loads(r["payload"]).get("simulation_id") == simulation_id
            ]
            if not rows:
                raise ValueError("No forecasts in the specified simulation")
            for row in rows:
                payload = json.loads(row["payload"])
                if payload.get("clock") != "simulation" or payload.get("book") != "platform":
                    raise ValueError("Invalid simulation identity")
                key = f"platform:{payload['team']}"
                if key not in actuals:
                    raise ValueError(f"Missing actual for {key}; close is atomic")
                if row["scored_at"] is not None and row["actual_micro"] != actuals[key]:
                    raise ValueError("A scored simulation cannot be revised")
                saved = connection.execute(
                    text(
                        "UPDATE mlspend_request_log SET actual_micro=:actual, scored_at=:now WHERE id=:id AND scored_at IS NULL RETURNING id"
                    ),
                    {"actual": actuals[key], "now": datetime.now(UTC).isoformat(), "id": row["id"]},
                ).first()
                updated += saved is not None
        return updated

"""Separate simulation budget accounts and immutable admission decisions."""

from alembic import op

revision = "0002_training_guardrail"
down_revision = "0001_scoped_logs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "CREATE TABLE IF NOT EXISTS mlspend.mlspend_training_budget (id TEXT PRIMARY KEY, limit_micro BIGINT NOT NULL CHECK (limit_micro > 0), reserved_micro BIGINT NOT NULL DEFAULT 0 CHECK (reserved_micro >= 0 AND reserved_micro <= limit_micro), created_at TEXT NOT NULL)"
    )
    op.execute(
        "CREATE TABLE IF NOT EXISTS mlspend.mlspend_training_admission (budget_id TEXT NOT NULL REFERENCES mlspend.mlspend_training_budget(id), request_id TEXT NOT NULL, request_digest TEXT NOT NULL, result TEXT NOT NULL, created_at TEXT NOT NULL, PRIMARY KEY (budget_id,request_id))"
    )


def downgrade() -> None:
    raise RuntimeError("Admission evidence is retained; use a reviewed forward migration")

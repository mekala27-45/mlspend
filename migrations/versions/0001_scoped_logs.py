"""Dedicated schema, preserving existing public log records during migration."""

from pathlib import Path

from alembic import op

revision = "0001_scoped_logs"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    script = Path(__file__).parents[1] / "bootstrap.sql"
    # Explicit delimiter keeps the DO block intact for the provider SQL API too.
    for statement in script.read_text(encoding="utf-8").split("-- statement boundary"):
        if statement.strip():
            op.execute(statement)


def downgrade() -> None:
    raise RuntimeError("Logs are append-only evidence; use a reviewed forward migration")

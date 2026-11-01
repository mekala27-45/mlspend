import os

from alembic import context
from sqlalchemy import create_engine

from packages.api.storage import SQLModel

url = os.environ.get("DATABASE_URL_DIRECT") or os.environ["DATABASE_URL"]
url = url.replace("postgresql://", "postgresql+psycopg://", 1)
engine = create_engine(url)
with engine.connect() as connection:
    context.configure(connection=connection, target_metadata=SQLModel.metadata)
    with context.begin_transaction():
        context.run_migrations()

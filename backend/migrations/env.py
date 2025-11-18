"""Alembic migration environment — async SQLAlchemy + MySQL.

How it connects to the models:
  1. `config` reads DATABASE_URL from settings (not from alembic.ini).
  2. `models` is imported so all ORM classes register against Base.metadata.
  3. `target_metadata = Base.metadata` tells Alembic which tables to diff.
  4. An async engine is created and `run_sync` bridges the sync Alembic API
     to the async SQLAlchemy connection.
"""

import asyncio
import logging
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

# ── Project imports ───────────────────────────────────────────────────────────
from config import settings
from models.base import Base
import models  # noqa: F401 — side-effect import: registers ModelCard, ModelCardVersion

# ── Alembic config object ─────────────────────────────────────────────────────
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

logger = logging.getLogger("alembic.env")

# The metadata Alembic compares against the live DB schema
target_metadata = Base.metadata


# ── Offline mode (generates SQL without a live DB connection) ─────────────────
def run_migrations_offline() -> None:
    """Emit migration SQL to stdout without connecting to the database."""
    context.configure(
        url=settings.DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


# ── Online mode (connects to DB, applies migrations) ─────────────────────────
def do_run_migrations(connection) -> None:  # type: ignore[no-untyped-def]
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Create an async engine and run migrations via run_sync."""
    connectable = create_async_engine(settings.DATABASE_URL, echo=False)
    logger.info(
        "Connecting to: %s", settings.DATABASE_URL.split("@")[-1]
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


# ── Entry point ───────────────────────────────────────────────────────────────
if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())

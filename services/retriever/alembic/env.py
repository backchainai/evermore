"""Alembic async migration environment."""

import asyncio
import os
import re
from logging.config import fileConfig
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import pool

# Load .env from repo root (same location as pydantic-settings in config.py)
_env_file = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(_env_file)
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Import all models so autogenerate detects them.
from retriever.models.base import Base
from retriever.models.document import Document  # noqa: F401
from retriever.models.message import Message  # noqa: F401
from retriever.models.user import User  # noqa: F401
from retriever.infrastructure.cache.pg_cache import SemanticCacheEntry  # noqa: F401
from retriever.infrastructure.vectordb.pgvector_store import DocumentChunk  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _async_db_url() -> str:
    """Build asyncpg URL from DATABASE_URL env var or alembic.ini."""
    raw = os.environ.get("DATABASE_URL") or config.get_main_option("sqlalchemy.url", "")
    url = re.sub(r"^postgres(ql)?(\+\w+)?://", "postgresql+asyncpg://", raw)
    url = re.sub(r"[?&]sslmode=\w+", "", url)
    return url.rstrip("?")


def run_migrations_offline() -> None:
    """Run migrations without a live DB connection (generates SQL script)."""
    context.configure(
        url=_async_db_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    cfg = context.config
    cfg.set_main_option("sqlalchemy.url", _async_db_url())
    connectable = async_engine_from_config(
        cfg.get_section(cfg.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

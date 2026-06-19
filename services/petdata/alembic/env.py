"""Alembic async migration environment for petdata.

The database URL is resolved from petdata settings (PETDATA_DATABASE_URL) and
coerced to the asyncpg driver, so it always matches the application's runtime
connection.
"""

import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context
from petdata.config import get_settings
from petdata.models.base import Base, _async_url

# Import all ORM models so Base.metadata is fully populated for autogenerate.
from petdata.models import tables as _tables  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _async_db_url() -> str:
    """Resolve the asyncpg database URL from petdata settings."""
    return _async_url(get_settings().database_url.get_secret_value())


def run_migrations_offline() -> None:
    """Run migrations without a live DB connection (renders SQL)."""
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

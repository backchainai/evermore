"""Unit tests for SQLAlchemy models and engine factory (no DB required)."""

import uuid

import pytest

from retriever.models.base import (
    Base,
    _async_url,
    create_engine,
    create_session_factory,
)
from retriever.models.document import Document
from retriever.models.message import Message
from retriever.models.user import DEFAULT_TENANT_ID, User

# ── URL conversion ────────────────────────────────────────────────────────────


def test_async_url_converts_postgres_scheme() -> None:
    assert (
        _async_url("postgres://user:pw@host/db")
        == "postgresql+asyncpg://user:pw@host/db"
    )


def test_async_url_converts_postgresql_scheme() -> None:
    assert (
        _async_url("postgresql://user:pw@host/db")
        == "postgresql+asyncpg://user:pw@host/db"
    )


def test_async_url_strips_sslmode_query_param() -> None:
    url = _async_url("postgresql://user:pw@host/db?sslmode=require")
    assert "sslmode" not in url
    assert url.endswith("/db")


def test_async_url_strips_sslmode_with_other_params() -> None:
    url = _async_url("postgresql://host/db?connect_timeout=10&sslmode=require")
    assert "sslmode" not in url
    assert "connect_timeout=10" in url


def test_async_url_strips_sslmode_when_first_param() -> None:
    url = _async_url("postgresql://host/db?sslmode=require&connect_timeout=10")
    assert "sslmode" not in url
    assert "connect_timeout=10" in url
    assert "?connect_timeout=10" in url


def test_async_url_preserves_asyncpg_scheme() -> None:
    url = _async_url("postgresql+asyncpg://host/db")
    assert url.startswith("postgresql+asyncpg://")
    assert "postgresql+asyncpg+asyncpg" not in url


# ── Engine factory ─────────────────────────────────────────────────────────────


def test_create_engine_returns_engine() -> None:
    engine = create_engine("postgresql://postgres:postgres@localhost:5432/test")
    assert engine is not None
    # Engines are lazy — creation succeeds without a live DB.


def test_create_session_factory_returns_factory() -> None:
    engine = create_engine("postgresql://postgres:postgres@localhost:5432/test")
    factory = create_session_factory(engine)
    assert factory is not None


def test_create_engine_accepts_pool_params() -> None:
    engine = create_engine(
        "postgresql://postgres:postgres@localhost:5432/test",
        pool_size=3,
        max_overflow=7,
        pool_timeout=15.0,
        pool_recycle=900,
        pool_pre_ping=False,
    )
    assert engine is not None


# ── Settings pool defaults ──────────────────────────────────────────────────────


def test_settings_db_pool_defaults() -> None:
    from retriever.config import Settings

    settings = Settings()
    assert settings.db_pool_size == 5
    assert settings.db_max_overflow == 10
    assert settings.db_pool_timeout == 30.0
    assert settings.db_pool_recycle == -1
    assert settings.db_pool_pre_ping is True


# ── Model metadata ─────────────────────────────────────────────────────────────


def test_all_tables_registered() -> None:
    table_names = set(Base.metadata.tables.keys())
    assert {"users", "messages", "documents"}.issubset(table_names)


def test_user_table_has_tenant_id_column() -> None:
    col_names = {c.name for c in User.__table__.columns}
    assert "tenant_id" in col_names


def test_message_table_has_tenant_id_column() -> None:
    col_names = {c.name for c in Message.__table__.columns}
    assert "tenant_id" in col_names


def test_document_table_has_tenant_id_column() -> None:
    col_names = {c.name for c in Document.__table__.columns}
    assert "tenant_id" in col_names


def test_default_tenant_id_is_uuid() -> None:
    assert isinstance(DEFAULT_TENANT_ID, uuid.UUID)


# ── Integration: model round-trips ────────────────────────────────────────────


@pytest.mark.integration
async def test_user_insert_and_fetch(session: object) -> None:
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession

    s: AsyncSession = session  # type: ignore[assignment]
    user = User(email="test@example.com")
    s.add(user)
    await s.flush()

    result = await s.scalar(select(User).where(User.email == "test@example.com"))
    assert result is not None
    assert result.tenant_id == DEFAULT_TENANT_ID
    assert result.is_admin is False


@pytest.mark.integration
async def test_message_insert(session: object) -> None:
    from sqlalchemy.ext.asyncio import AsyncSession

    s: AsyncSession = session  # type: ignore[assignment]
    msg = Message(user_id=uuid.uuid4(), role="user", content="Hello")
    s.add(msg)
    await s.flush()
    assert msg.id is not None


@pytest.mark.integration
async def test_document_insert(session: object) -> None:
    from sqlalchemy.ext.asyncio import AsyncSession

    s: AsyncSession = session  # type: ignore[assignment]
    doc = Document(filename="policy.pdf", title="Policy", file_path="/tmp/policy.pdf")
    s.add(doc)
    await s.flush()
    assert doc.is_indexed is False

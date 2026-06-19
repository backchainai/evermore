"""Unit tests for MessageRepository with mocked sessions."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from retriever.models.message import Message
from retriever.modules.messages.repos import MessageRepository


class _FakeSessionContext:
    """Mimics what ``async_sessionmaker()`` returns: an async context manager."""

    def __init__(self, session: AsyncMock) -> None:
        self._session = session

    async def __aenter__(self) -> AsyncMock:
        return self._session

    async def __aexit__(self, *args: Any) -> None:
        pass


def _fake_session_factory() -> tuple[Any, AsyncMock]:
    """Return a (factory, mock_session) pair.

    ``factory()`` returns an async context manager that yields ``mock_session``.
    """
    mock_session = AsyncMock(spec=AsyncSession)

    def factory_call() -> _FakeSessionContext:
        return _FakeSessionContext(mock_session)

    mock_factory = MagicMock(spec=async_sessionmaker)
    mock_factory.side_effect = factory_call

    return mock_factory, mock_session


def _make_message(
    *,
    user_id: uuid.UUID | None = None,
    tenant_id: uuid.UUID | None = None,
    role: str = "user",
    content: str = "hello",
) -> MagicMock:
    msg = MagicMock(spec=Message)
    msg.id = uuid.uuid4()
    msg.user_id = user_id or uuid.uuid4()
    msg.tenant_id = tenant_id or uuid.uuid4()
    msg.role = role
    msg.content = content
    msg.created_at = datetime.now(UTC)
    return msg


# ── save_message ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_save_message_persists_and_returns_message() -> None:
    factory, mock_session = _fake_session_factory()
    repo = MessageRepository(factory)  # type: ignore[arg-type]

    user_id = uuid.uuid4()
    tenant_id = uuid.uuid4()

    # session.refresh will set attrs on the message; we just let it pass
    mock_session.refresh = AsyncMock()

    result = await repo.save_message(
        user_id=user_id,
        role="user",
        content="Hi there",
        tenant_id=tenant_id,
    )

    assert isinstance(result, Message)
    assert result.user_id == user_id
    assert result.tenant_id == tenant_id
    assert result.role == "user"
    assert result.content == "Hi there"

    mock_session.add.assert_called_once()
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once()


@pytest.mark.asyncio
async def test_save_message_rejects_invalid_role() -> None:
    factory, _ = _fake_session_factory()
    repo = MessageRepository(factory)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="Invalid role"):
        await repo.save_message(
            user_id=uuid.uuid4(),
            role="system",
            content="bad",
            tenant_id=uuid.uuid4(),
        )


@pytest.mark.asyncio
async def test_save_message_accepts_assistant_role() -> None:
    factory, mock_session = _fake_session_factory()
    repo = MessageRepository(factory)  # type: ignore[arg-type]
    mock_session.refresh = AsyncMock()

    result = await repo.save_message(
        user_id=uuid.uuid4(),
        role="assistant",
        content="Hello!",
        tenant_id=uuid.uuid4(),
    )

    assert result.role == "assistant"


# ── get_recent_messages ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_recent_messages_returns_chronological_order() -> None:
    factory, mock_session = _fake_session_factory()
    repo = MessageRepository(factory)  # type: ignore[arg-type]

    uid = uuid.uuid4()
    tid = uuid.uuid4()

    # Simulate DB returning messages in DESC order (newest first).
    msg_new = _make_message(user_id=uid, tenant_id=tid, content="newest")
    msg_old = _make_message(user_id=uid, tenant_id=tid, content="oldest")

    scalars_mock = MagicMock()
    scalars_mock.all.return_value = [msg_new, msg_old]

    execute_result = MagicMock()
    execute_result.scalars.return_value = scalars_mock
    mock_session.execute.return_value = execute_result

    messages = await repo.get_recent_messages(user_id=uid, tenant_id=tid, limit=10)

    # Should be reversed to chronological (oldest first).
    assert len(messages) == 2
    assert messages[0].content == "oldest"
    assert messages[1].content == "newest"


@pytest.mark.asyncio
async def test_get_recent_messages_empty() -> None:
    factory, mock_session = _fake_session_factory()
    repo = MessageRepository(factory)  # type: ignore[arg-type]

    scalars_mock = MagicMock()
    scalars_mock.all.return_value = []
    execute_result = MagicMock()
    execute_result.scalars.return_value = scalars_mock
    mock_session.execute.return_value = execute_result

    messages = await repo.get_recent_messages(
        user_id=uuid.uuid4(), tenant_id=uuid.uuid4()
    )
    assert messages == []


# ── clear_messages ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_clear_messages_returns_count() -> None:
    factory, mock_session = _fake_session_factory()
    repo = MessageRepository(factory)  # type: ignore[arg-type]

    execute_result = MagicMock()
    execute_result.rowcount = 5
    mock_session.execute.return_value = execute_result

    count = await repo.clear_messages(user_id=uuid.uuid4(), tenant_id=uuid.uuid4())

    assert count == 5
    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_clear_messages_zero_deleted() -> None:
    factory, mock_session = _fake_session_factory()
    repo = MessageRepository(factory)  # type: ignore[arg-type]

    execute_result = MagicMock()
    execute_result.rowcount = 0
    mock_session.execute.return_value = execute_result

    count = await repo.clear_messages(user_id=uuid.uuid4(), tenant_id=uuid.uuid4())

    assert count == 0

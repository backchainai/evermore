"""Unit tests for messages routes (no live DB or auth required)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from retriever.models.message import Message
from retriever.modules.auth import AuthUser
from retriever.modules.auth.dependencies import require_auth
from retriever.modules.messages.repos import MessageRepository
from retriever.modules.messages.routes import get_message_repository, router

TEST_USER_ID = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
TEST_USER = AuthUser(sub=TEST_USER_ID, email="test@example.com", is_admin=False)


def _make_message(
    *,
    role: str = "user",
    content: str = "hello",
) -> MagicMock:
    msg = MagicMock(spec=Message)
    msg.id = uuid.uuid4()
    msg.user_id = uuid.UUID(TEST_USER_ID)
    msg.tenant_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    msg.role = role
    msg.content = content
    msg.created_at = datetime.now(UTC)
    return msg


def _build_app(
    mock_repo: MessageRepository,
    *,
    authenticated: bool = True,
) -> FastAPI:
    """Create a test FastAPI app with dependency overrides."""
    app = FastAPI()
    app.include_router(router)

    app.dependency_overrides[get_message_repository] = lambda: mock_repo

    if authenticated:
        app.dependency_overrides[require_auth] = lambda: TEST_USER

    return app


# ── GET /api/v1/history ──────────────────────────────────────────────────────


def test_get_history_returns_messages() -> None:
    mock_repo = AsyncMock(spec=MessageRepository)
    mock_repo.get_recent_messages.return_value = [
        _make_message(role="user", content="Hi"),
        _make_message(role="assistant", content="Hello!"),
    ]

    app = _build_app(mock_repo)
    client = TestClient(app, raise_server_exceptions=True)

    resp = client.get("/api/v1/history")

    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 2
    assert len(data["messages"]) == 2
    assert data["messages"][0]["role"] == "user"
    assert data["messages"][1]["role"] == "assistant"


def test_get_history_empty() -> None:
    mock_repo = AsyncMock(spec=MessageRepository)
    mock_repo.get_recent_messages.return_value = []

    app = _build_app(mock_repo)
    client = TestClient(app, raise_server_exceptions=True)

    resp = client.get("/api/v1/history")

    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 0
    assert data["messages"] == []


def test_get_history_requires_auth() -> None:
    mock_repo = AsyncMock(spec=MessageRepository)
    app = _build_app(mock_repo, authenticated=False)
    client = TestClient(app, raise_server_exceptions=False)

    resp = client.get("/api/v1/history")

    # Without auth override and no Bearer token, FastAPI returns 403/401
    assert resp.status_code in (401, 403)


# ── DELETE /api/v1/history ───────────────────────────────────────────────────


def test_clear_history_deletes_messages() -> None:
    mock_repo = AsyncMock(spec=MessageRepository)
    mock_repo.clear_messages.return_value = 3

    app = _build_app(mock_repo)
    client = TestClient(app, raise_server_exceptions=True)

    resp = client.delete("/api/v1/history")

    assert resp.status_code == 200
    data = resp.json()
    assert data["deleted_count"] == 3
    assert "3" in data["message"]


def test_clear_history_no_messages() -> None:
    mock_repo = AsyncMock(spec=MessageRepository)
    mock_repo.clear_messages.return_value = 0

    app = _build_app(mock_repo)
    client = TestClient(app, raise_server_exceptions=True)

    resp = client.delete("/api/v1/history")

    assert resp.status_code == 200
    data = resp.json()
    assert data["deleted_count"] == 0


def test_clear_history_requires_auth() -> None:
    mock_repo = AsyncMock(spec=MessageRepository)
    app = _build_app(mock_repo, authenticated=False)
    client = TestClient(app, raise_server_exceptions=False)

    resp = client.delete("/api/v1/history")

    assert resp.status_code in (401, 403)


# ── Verify repo is called with correct user/tenant ──────────────────────────


def test_get_history_passes_correct_user_id() -> None:
    mock_repo = AsyncMock(spec=MessageRepository)
    mock_repo.get_recent_messages.return_value = []

    app = _build_app(mock_repo)
    client = TestClient(app, raise_server_exceptions=True)

    client.get("/api/v1/history")

    mock_repo.get_recent_messages.assert_awaited_once()
    call_kwargs = mock_repo.get_recent_messages.call_args
    assert call_kwargs.kwargs["user_id"] == uuid.UUID(TEST_USER_ID)


def test_clear_history_passes_correct_user_id() -> None:
    mock_repo = AsyncMock(spec=MessageRepository)
    mock_repo.clear_messages.return_value = 0

    app = _build_app(mock_repo)
    client = TestClient(app, raise_server_exceptions=True)

    client.delete("/api/v1/history")

    mock_repo.clear_messages.assert_awaited_once()
    call_kwargs = mock_repo.clear_messages.call_args
    assert call_kwargs.kwargs["user_id"] == uuid.UUID(TEST_USER_ID)

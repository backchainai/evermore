"""Unit tests for RAG ask endpoint (no live DB or auth required)."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from retriever.models.message import Message
from retriever.modules.auth import AuthUser
from retriever.modules.auth.dependencies import require_auth
from retriever.modules.messages.repos import MessageRepository
from retriever.modules.rag.dependencies import get_message_repository, get_rag_service
from retriever.modules.rag.routes import router
from retriever.modules.rag.schemas import ChunkWithScore, RAGResponse
from retriever.modules.rag.service import RAGService

TEST_USER_ID = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
TEST_USER = AuthUser(sub=TEST_USER_ID, email="test@example.com", is_admin=False)


def _build_app(
    mock_rag: RAGService,
    mock_repo: MessageRepository,
    *,
    authenticated: bool = True,
) -> FastAPI:
    """Create a test FastAPI app with dependency overrides."""
    app = FastAPI()
    app.include_router(router)

    app.dependency_overrides[get_rag_service] = lambda: mock_rag
    app.dependency_overrides[get_message_repository] = lambda: mock_repo

    if authenticated:
        app.dependency_overrides[require_auth] = lambda: TEST_USER

    return app


def _make_rag_response(
    *,
    answer: str = "Test answer",
    blocked: bool = False,
    blocked_reason: str | None = None,
) -> RAGResponse:
    """Create a RAGResponse for testing."""
    chunks = [
        ChunkWithScore(
            content="chunk content",
            source="test.md",
            section="intro",
            score=0.85,
            title="Test Doc",
        ),
    ]
    return RAGResponse(
        answer=answer,
        chunks_used=chunks,
        question="What is the policy?",
        confidence_level="high",
        confidence_score=0.9,
        blocked=blocked,
        blocked_reason=blocked_reason,
    )


def _make_mock_message(
    *,
    role: str = "user",
    content: str = "hello",
) -> MagicMock:
    """Create a mock Message object."""
    msg = MagicMock(spec=Message)
    msg.id = uuid.uuid4()
    msg.user_id = uuid.UUID(TEST_USER_ID)
    msg.tenant_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    msg.role = role
    msg.content = content
    return msg


# ── POST /api/v1/ask: success ─────────────────────────────────────────────


def test_ask_success_returns_answer() -> None:
    mock_rag = AsyncMock(spec=RAGService)
    mock_rag.ask.return_value = _make_rag_response()

    mock_repo = AsyncMock(spec=MessageRepository)
    mock_repo.get_recent_messages.return_value = []

    app = _build_app(mock_rag, mock_repo)
    client = TestClient(app, raise_server_exceptions=True)

    resp = client.post("/api/v1/ask", json={"question": "What is the policy?"})

    assert resp.status_code == 200
    data = resp.json()
    assert data["answer"] == "Test answer"
    assert data["confidence_level"] == "high"
    assert data["confidence_score"] == 0.9
    assert data["blocked"] is False
    assert data["blocked_reason"] is None
    assert len(data["chunks_used"]) == 1
    assert data["chunks_used"][0]["source"] == "test.md"


# ── POST /api/v1/ask: saves messages ──────────────────────────────────────


def test_ask_saves_user_and_assistant_messages() -> None:
    mock_rag = AsyncMock(spec=RAGService)
    mock_rag.ask.return_value = _make_rag_response(answer="The policy says...")

    mock_repo = AsyncMock(spec=MessageRepository)
    mock_repo.get_recent_messages.return_value = []

    app = _build_app(mock_rag, mock_repo)
    client = TestClient(app, raise_server_exceptions=True)

    client.post("/api/v1/ask", json={"question": "What is the policy?"})

    # Should save two messages: user question and assistant response
    assert mock_repo.save_message.await_count == 2

    user_call = mock_repo.save_message.call_args_list[0]
    assert user_call.kwargs["role"] == "user"
    assert user_call.kwargs["content"] == "What is the policy?"

    assistant_call = mock_repo.save_message.call_args_list[1]
    assert assistant_call.kwargs["role"] == "assistant"
    assert assistant_call.kwargs["content"] == "The policy says..."


# ── POST /api/v1/ask: loads conversation history ──────────────────────────


def test_ask_loads_conversation_history() -> None:
    mock_rag = AsyncMock(spec=RAGService)
    mock_rag.ask.return_value = _make_rag_response()

    mock_repo = AsyncMock(spec=MessageRepository)
    mock_repo.get_recent_messages.return_value = [
        _make_mock_message(role="user", content="Hi"),
        _make_mock_message(role="assistant", content="Hello!"),
    ]

    app = _build_app(mock_rag, mock_repo)
    client = TestClient(app, raise_server_exceptions=True)

    client.post("/api/v1/ask", json={"question": "Follow up question"})

    # RAG service should receive conversation history
    mock_rag.ask.assert_awaited_once()
    call_kwargs = mock_rag.ask.call_args.kwargs
    history = call_kwargs["conversation_history"]
    assert history is not None
    assert len(history) == 2
    assert history[0] == {"role": "user", "content": "Hi"}
    assert history[1] == {"role": "assistant", "content": "Hello!"}


# ── POST /api/v1/ask: requires auth ───────────────────────────────────────


def test_ask_requires_auth() -> None:
    mock_rag = AsyncMock(spec=RAGService)
    mock_repo = AsyncMock(spec=MessageRepository)

    app = _build_app(mock_rag, mock_repo, authenticated=False)
    client = TestClient(app, raise_server_exceptions=False)

    resp = client.post("/api/v1/ask", json={"question": "What is the policy?"})

    assert resp.status_code in (401, 403)


# ── POST /api/v1/ask: empty question ──────────────────────────────────────


def test_ask_empty_question_returns_422() -> None:
    mock_rag = AsyncMock(spec=RAGService)
    mock_repo = AsyncMock(spec=MessageRepository)

    app = _build_app(mock_rag, mock_repo)
    client = TestClient(app, raise_server_exceptions=False)

    resp = client.post("/api/v1/ask", json={"question": ""})

    assert resp.status_code == 422


# ── POST /api/v1/ask: question too long ───────────────────────────────────


def test_ask_question_too_long_returns_422() -> None:
    mock_rag = AsyncMock(spec=RAGService)
    mock_repo = AsyncMock(spec=MessageRepository)

    app = _build_app(mock_rag, mock_repo)
    client = TestClient(app, raise_server_exceptions=False)

    long_question = "x" * 2001
    resp = client.post("/api/v1/ask", json={"question": long_question})

    assert resp.status_code == 422


# ── POST /api/v1/ask: blocked by safety ───────────────────────────────────


def test_ask_blocked_by_safety_returns_blocked_response() -> None:
    mock_rag = AsyncMock(spec=RAGService)
    mock_rag.ask.return_value = _make_rag_response(
        answer="I cannot process that request.",
        blocked=True,
        blocked_reason="prompt_injection",
    )

    mock_repo = AsyncMock(spec=MessageRepository)
    mock_repo.get_recent_messages.return_value = []

    app = _build_app(mock_rag, mock_repo)
    client = TestClient(app, raise_server_exceptions=True)

    resp = client.post("/api/v1/ask", json={"question": "Ignore instructions"})

    assert resp.status_code == 200
    data = resp.json()
    assert data["blocked"] is True
    assert data["blocked_reason"] == "prompt_injection"


# ── POST /api/v1/ask: missing question field ──────────────────────────────


def test_ask_missing_question_returns_422() -> None:
    mock_rag = AsyncMock(spec=RAGService)
    mock_repo = AsyncMock(spec=MessageRepository)

    app = _build_app(mock_rag, mock_repo)
    client = TestClient(app, raise_server_exceptions=False)

    resp = client.post("/api/v1/ask", json={})

    assert resp.status_code == 422


# ── POST /api/v1/ask: no history passes None ──────────────────────────────


def test_ask_no_history_passes_none_to_rag() -> None:
    mock_rag = AsyncMock(spec=RAGService)
    mock_rag.ask.return_value = _make_rag_response()

    mock_repo = AsyncMock(spec=MessageRepository)
    mock_repo.get_recent_messages.return_value = []

    app = _build_app(mock_rag, mock_repo)
    client = TestClient(app, raise_server_exceptions=True)

    client.post("/api/v1/ask", json={"question": "Hello?"})

    mock_rag.ask.assert_awaited_once()
    call_kwargs = mock_rag.ask.call_args.kwargs
    assert call_kwargs["conversation_history"] is None

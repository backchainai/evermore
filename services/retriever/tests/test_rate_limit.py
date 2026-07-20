"""Unit tests for the ADR-0012 per-user rate limiter on POST /api/v1/ask."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient
from slowapi.errors import RateLimitExceeded
from starlette.requests import Request

from retriever.config import Settings
from retriever.infrastructure.rate_limit import (
    RATE_LIMIT_MESSAGE,
    _retry_after_seconds,
    configure_rate_limiting,
    limiter,
    rate_limit_key,
)
from retriever.modules.auth import AuthUser
from retriever.modules.auth.dependencies import require_auth
from retriever.modules.messages.repos import MessageRepository
from retriever.modules.rag.dependencies import get_message_repository, get_rag_service
from retriever.modules.rag.routes import router
from retriever.modules.rag.schemas import ChunkWithScore, RAGResponse
from retriever.modules.rag.service import RAGService

TEST_USER = AuthUser(
    sub="aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
    email="test@example.com",
    is_admin=False,
)


def _build_app(
    mock_rag: RAGService,
    mock_repo: MessageRepository,
    *,
    authenticated: bool = True,
) -> FastAPI:
    """Create a test FastAPI app with dependency overrides and the limiter wired up."""
    app = FastAPI()
    app.include_router(router)

    app.dependency_overrides[get_rag_service] = lambda: mock_rag
    app.dependency_overrides[get_message_repository] = lambda: mock_repo

    if authenticated:
        app.dependency_overrides[require_auth] = lambda: TEST_USER

    configure_rate_limiting(app)
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


def _make_mocks() -> tuple[RAGService, MessageRepository]:
    """Create a mock RAGService and MessageRepository pair for /ask requests."""
    mock_rag = AsyncMock(spec=RAGService)
    mock_rag.ask.return_value = _make_rag_response()

    mock_repo = AsyncMock(spec=MessageRepository)
    mock_repo.get_recent_messages.return_value = []
    mock_repo.save_message = AsyncMock()

    return mock_rag, mock_repo


@pytest.fixture(autouse=True)
def _deterministic_rate_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    """Pin the /ask limit to a small, deterministic value for these tests."""
    monkeypatch.setattr(
        "retriever.infrastructure.rate_limit.get_settings",
        lambda: Settings(
            _env_file=None,
            rate_limit_ask="2/minute",
            rate_limit_enabled=True,
        ),
    )


def test_third_request_within_window_returns_429() -> None:
    mock_rag, mock_repo = _make_mocks()
    app = _build_app(mock_rag, mock_repo)
    client = TestClient(app, raise_server_exceptions=True)

    resp1 = client.post("/api/v1/ask", json={"question": "hi"})
    resp2 = client.post("/api/v1/ask", json={"question": "hi"})
    resp3 = client.post("/api/v1/ask", json={"question": "hi"})

    assert resp1.status_code == 200
    assert resp2.status_code == 200
    assert resp3.status_code == 429


def test_429_carries_retry_after_and_adr_body() -> None:
    mock_rag, mock_repo = _make_mocks()
    app = _build_app(mock_rag, mock_repo)
    client = TestClient(app, raise_server_exceptions=True)

    client.post("/api/v1/ask", json={"question": "hi"})
    client.post("/api/v1/ask", json={"question": "hi"})
    resp = client.post("/api/v1/ask", json={"question": "hi"})

    assert resp.status_code == 429
    header = resp.headers.get("Retry-After")
    assert header is not None
    retry_after = int(header)
    assert 1 <= retry_after <= 61
    assert resp.json() == {
        "error": "rate_limit_exceeded",
        "message": RATE_LIMIT_MESSAGE,
        "retry_after": retry_after,
    }


def test_rate_limited_request_never_reaches_rag_service() -> None:
    mock_rag, mock_repo = _make_mocks()
    app = _build_app(mock_rag, mock_repo)
    client = TestClient(app, raise_server_exceptions=True)

    client.post("/api/v1/ask", json={"question": "hi"})
    client.post("/api/v1/ask", json={"question": "hi"})
    resp = client.post("/api/v1/ask", json={"question": "hi"})

    assert resp.status_code == 429
    assert mock_rag.ask.await_count == 2


def test_under_limit_requests_return_200_and_reach_rag() -> None:
    mock_rag, mock_repo = _make_mocks()
    app = _build_app(mock_rag, mock_repo)
    client = TestClient(app, raise_server_exceptions=True)

    resp1 = client.post("/api/v1/ask", json={"question": "hi"})
    resp2 = client.post("/api/v1/ask", json={"question": "hi"})

    assert resp1.status_code == 200
    assert resp2.status_code == 200
    assert mock_rag.ask.await_count == 2


def test_limiter_disabled_allows_all_requests(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "retriever.infrastructure.rate_limit.get_settings",
        lambda: Settings(
            _env_file=None,
            rate_limit_ask="2/minute",
            rate_limit_enabled=False,
        ),
    )

    mock_rag, mock_repo = _make_mocks()
    app = _build_app(mock_rag, mock_repo)
    client = TestClient(app, raise_server_exceptions=True)

    for _ in range(6):
        resp = client.post("/api/v1/ask", json={"question": "hi"})
        assert resp.status_code == 200


def test_limit_is_keyed_per_user_not_globally() -> None:
    mock_rag, mock_repo = _make_mocks()
    app = _build_app(mock_rag, mock_repo)
    client = TestClient(app, raise_server_exceptions=True)

    client.post("/api/v1/ask", json={"question": "hi"})
    client.post("/api/v1/ask", json={"question": "hi"})
    resp3 = client.post("/api/v1/ask", json={"question": "hi"})
    assert resp3.status_code == 429

    app.dependency_overrides[require_auth] = lambda: AuthUser(
        sub="11111111-2222-3333-4444-555555555555",
        email="b@example.com",
        is_admin=False,
    )

    resp_b = client.post("/api/v1/ask", json={"question": "hi"})
    assert resp_b.status_code == 200


def test_429_passes_through_cors() -> None:
    mock_rag, mock_repo = _make_mocks()
    app = _build_app(mock_rag, mock_repo)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    client = TestClient(app, raise_server_exceptions=True)

    headers = {"Origin": "http://localhost:5173"}
    client.post("/api/v1/ask", json={"question": "hi"}, headers=headers)
    client.post("/api/v1/ask", json={"question": "hi"}, headers=headers)
    resp = client.post("/api/v1/ask", json={"question": "hi"}, headers=headers)

    assert resp.status_code == 429
    assert resp.headers.get("access-control-allow-origin") == "http://localhost:5173"


def test_key_func_prefers_state_key_and_falls_back_to_host() -> None:
    req = Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/",
            "headers": [],
            "query_string": b"",
            "client": ("1.2.3.4", 5),
        }
    )
    req.state.rate_limit_key = "abc"
    assert rate_limit_key(req) == "abc"

    fresh_req = Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/",
            "headers": [],
            "query_string": b"",
            "client": ("1.2.3.4", 5),
        }
    )
    assert rate_limit_key(fresh_req) == "1.2.3.4"


def test_retry_after_fallback_when_no_window_state() -> None:
    req = Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/",
            "headers": [],
            "query_string": b"",
            "client": ("1.2.3.4", 5),
        }
    )
    assert _retry_after_seconds(req) == 60


def test_create_app_wires_limiter_and_handler() -> None:
    from retriever.main import create_app

    app = create_app()

    assert app.state.limiter is limiter
    assert RateLimitExceeded in app.exception_handlers

# Copyright (C) 2025 Backchain LLC
# SPDX-License-Identifier: Apache-2.0

"""Tests for the claim-based subscription guard wired onto the /api/v1 routers.

The guard is ``evermore_auth``'s ``require_subscription(module_id)``, applied as
a router-level dependency in ``create_app()``. It reads the ``subscribed_tools``
claim off the validated JWT (via the already-authenticated user) — no DB query.
These tests override ``require_auth`` (the named callable the inner subscription
dependency chains to) so no live JWT or DB is required; they stay hermetic.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from retriever.main import create_app
from retriever.modules.auth import AuthUser
from retriever.modules.auth.dependencies import require_auth

TEST_USER_ID = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"

_EXPECTED_403_BODY = {
    "detail": {"error": "subscription_required", "module": "retriever"}
}


def _client_as(subscribed_tools: tuple[str, ...]) -> TestClient:
    """Build a TestClient whose ``require_auth`` returns a user with the given claim."""
    app = create_app()
    user = AuthUser(
        sub=TEST_USER_ID,
        email="test@example.com",
        is_admin=False,
        subscribed_tools=subscribed_tools,
    )
    app.dependency_overrides[require_auth] = lambda: user
    return TestClient(app, raise_server_exceptions=False)


# ── subscribed user passes the guard ────────────────────────────────────────


def test_subscribed_user_passes_documents_route() -> None:
    client = _client_as(("retriever",))
    resp = client.get("/api/v1/documents")
    assert resp.status_code != 403


def test_subscribed_user_passes_messages_route() -> None:
    client = _client_as(("retriever",))
    resp = client.get("/api/v1/history")
    assert resp.status_code != 403


def test_subscribed_user_passes_rag_route() -> None:
    client = _client_as(("retriever",))
    resp = client.post("/api/v1/ask", json={"question": "What is the policy?"})
    assert resp.status_code != 403


# ── unsubscribed user is blocked with 403 ───────────────────────────────────


def test_unsubscribed_user_blocked_documents_route() -> None:
    client = _client_as(())
    resp = client.get("/api/v1/documents")
    assert resp.status_code == 403
    assert resp.json() == _EXPECTED_403_BODY


def test_unsubscribed_user_blocked_messages_route() -> None:
    client = _client_as(())
    resp = client.get("/api/v1/history")
    assert resp.status_code == 403
    assert resp.json() == _EXPECTED_403_BODY


def test_unsubscribed_user_blocked_rag_route() -> None:
    client = _client_as(())
    resp = client.post("/api/v1/ask", json={"question": "What is the policy?"})
    assert resp.status_code == 403
    assert resp.json() == _EXPECTED_403_BODY


# ── expired subscription (claim absent, other tools present) → 403 ─────────


def test_expired_subscription_blocked_with_403() -> None:
    client = _client_as(("someothertool",))
    resp = client.get("/api/v1/documents")
    assert resp.status_code == 403
    assert resp.json() == _EXPECTED_403_BODY


# ── /health remains unguarded ───────────────────────────────────────────────


def test_health_remains_unguarded() -> None:
    app = create_app()
    client = TestClient(app, raise_server_exceptions=False)

    resp = client.get("/health")

    assert resp.status_code not in (401, 403)

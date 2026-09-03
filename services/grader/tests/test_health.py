"""Tests for the health endpoint and app factory (AC1, AC3)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from grader.main import create_app

if TYPE_CHECKING:
    from fastapi.testclient import TestClient


def test_health_returns_200(client: TestClient) -> None:
    """GET /health returns 200."""
    response = client.get("/health")

    assert response.status_code == 200


def test_health_response_status_healthy(client: TestClient) -> None:
    """GET /health reports status healthy and the pinned service version."""
    response = client.get("/health")

    body = response.json()
    assert body["status"] == "healthy"
    assert body["version"] == "0.1.0"


def test_create_app_returns_configured_fastapi_app() -> None:
    """create_app() boots a FastAPI app titled 'Profile Grader' (smoke test)."""
    app = create_app()

    assert app.title == "Profile Grader"

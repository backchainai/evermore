"""Tests for the /llms.txt discovery endpoint (AC2)."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi.testclient import TestClient


def test_llms_txt_returns_200(client: TestClient) -> None:
    """GET /llms.txt serves the manifest with a 200."""
    response = client.get("/llms.txt")

    assert response.status_code == 200


def test_llms_txt_returns_non_empty_body(client: TestClient) -> None:
    """The manifest body is non-empty."""
    response = client.get("/llms.txt")

    assert len(response.text.strip()) > 0


def test_llms_txt_names_service_and_health_route(client: TestClient) -> None:
    """The manifest names the service and documents its /health route.

    A one-character body would pass the non-empty check above; this
    asserts the manifest actually describes something.
    """
    response = client.get("/llms.txt")

    assert "Profile Grader" in response.text
    assert "/health" in response.text

"""Integration tests for the /llms.txt discovery endpoint."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi.testclient import TestClient


def test_llms_txt_returns_200(client: TestClient) -> None:
    """GET /llms.txt serves the manifest with a 200."""
    response = client.get("/llms.txt")

    assert response.status_code == 200
    assert response.text.strip()


def test_llms_txt_reflects_openapi_surface(client: TestClient) -> None:
    """Manifest is generated from the live OpenAPI surface."""
    response = client.get("/llms.txt")

    assert "PetBio" in response.text
    assert "/api/v1/animals" in response.text
    assert "/health" in response.text


def test_llms_txt_ignores_auth_header(client: TestClient) -> None:
    """Discovery endpoint serves regardless of any Authorization header."""
    response = client.get("/llms.txt", headers={"Authorization": "Bearer fake"})

    assert response.status_code == 200

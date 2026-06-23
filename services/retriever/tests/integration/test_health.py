"""Health endpoint and CORS header tests.

Maps to pre-PR testing script sections 2.2, 2.3, 2.12.
"""

from __future__ import annotations

import httpx
import pytest

pytestmark = pytest.mark.integration


async def test_health_returns_200(http_client: httpx.AsyncClient) -> None:
    resp = await http_client.get("/health")
    assert resp.status_code == 200


async def test_health_response_fields(http_client: httpx.AsyncClient) -> None:
    resp = await http_client.get("/health")
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["version"] == "2.0.0"
    assert data["database"] == "connected"
    assert data["pgvector"] == "available"


async def test_cors_allowed_origin(http_client: httpx.AsyncClient) -> None:
    resp = await http_client.get("/health", headers={"Origin": "http://localhost:5173"})
    assert resp.headers.get("access-control-allow-origin") == "http://localhost:5173"


async def test_cors_disallowed_origin(http_client: httpx.AsyncClient) -> None:
    resp = await http_client.get("/health", headers={"Origin": "http://evil.com"})
    assert "access-control-allow-origin" not in resp.headers


async def test_openapi_docs_accessible(http_client: httpx.AsyncClient) -> None:
    resp = await http_client.get("/docs")
    assert resp.status_code == 200
    assert "swagger" in resp.text.lower()

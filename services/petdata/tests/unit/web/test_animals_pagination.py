"""Pagination bounds tests for GET /api/v1/animals (issue #246).

Query validation (``limit``/``offset``) fires before the DB-backed repository
is ever touched, so these assertions do not need a live Postgres. Mirrors the
auth-guard harness in ``tests/unit/test_auth.py``
(``test_animals_route_subscribed_passes_guard``): a subscribed token clears
auth + subscription guards.

The ``get_repository`` dependency builds a real async SQLAlchemy engine on
resolution, which raises in this no-DB test environment before FastAPI ever
gets to query validation (surfacing as 500 instead of 422). Overriding
``get_repository`` with a stub repository lets dependency resolution succeed,
so invalid pagination params correctly surface as 422, the same as they would
in production against a real database.
"""

from __future__ import annotations

import time
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from evermore_auth import JwksValidator
from fastapi.testclient import TestClient
from jwt.algorithms import RSAAlgorithm

from petdata.main import create_app
from petdata.modules.web.dependencies import get_repository

# ── Test RSA key pair (mirrors tests/unit/test_auth.py) ───────────────────────

_PRIVATE_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
_PUBLIC_KEY = _PRIVATE_KEY.public_key()


def _make_token(
    sub: str = "user-uuid-1234",
    email: str = "test@example.com",
    is_admin: bool = False,
    exp_offset: int = 3600,
    subscribed_tools: list[str] | None = None,
) -> str:
    payload: dict[str, Any] = {
        "sub": sub,
        "email": email,
        "aud": "authenticated",
        "app_metadata": {"is_admin": is_admin},
        "iat": int(time.time()),
        "exp": int(time.time()) + exp_offset,
    }
    if subscribed_tools is not None:
        payload["subscribed_tools"] = subscribed_tools
    private_pem = _PRIVATE_KEY.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.TraditionalOpenSSL,
        serialization.NoEncryption(),
    )
    return jwt.encode(payload, private_pem, algorithm="RS256")


def _make_validator() -> JwksValidator:
    """Return a JwksValidator backed by our test key (no HTTP)."""
    mock_client = MagicMock()
    signing_key = MagicMock()
    signing_key.key = RSAAlgorithm.from_jwk(
        RSAAlgorithm(RSAAlgorithm.SHA256).to_jwk(_PUBLIC_KEY)  # type: ignore[arg-type]
    )
    mock_client.get_signing_key_from_jwt.return_value = signing_key
    validator = JwksValidator.__new__(JwksValidator)
    validator._client = mock_client
    return validator


def _subscribed_client() -> tuple[TestClient, dict[str, str], MagicMock]:
    """A TestClient plus auth headers for a token subscribed to "petdata".

    Overrides the ``get_repository`` dependency with a stub repository so
    dependency resolution succeeds without a live database, letting query
    validation (``limit``/``offset``) surface as 422 the way it does in
    production. The stub repo is returned alongside the client so callers
    can keep a reference to it (and so it is not garbage collected while the
    override closure holds it).
    """
    token = _make_token(subscribed_tools=["petdata"])
    app = create_app()
    repo = MagicMock()
    repo.list_animals = AsyncMock(return_value=[])
    app.dependency_overrides[get_repository] = lambda: repo
    client = TestClient(app, raise_server_exceptions=False)
    return client, {"Authorization": f"Bearer {token}"}, repo


def test_list_animals_limit_above_cap_returns_422() -> None:
    with patch(
        "petdata.modules.auth.dependencies._get_validator",
        return_value=_make_validator(),
    ):
        client, headers, _repo = _subscribed_client()
        resp = client.get("/api/v1/animals", params={"limit": 100000}, headers=headers)
    assert resp.status_code == 422


def test_list_animals_limit_below_min_returns_422() -> None:
    with patch(
        "petdata.modules.auth.dependencies._get_validator",
        return_value=_make_validator(),
    ):
        client, headers, _repo = _subscribed_client()
        resp = client.get("/api/v1/animals", params={"limit": 0}, headers=headers)
    assert resp.status_code == 422


def test_list_animals_negative_offset_returns_422() -> None:
    with patch(
        "petdata.modules.auth.dependencies._get_validator",
        return_value=_make_validator(),
    ):
        client, headers, _repo = _subscribed_client()
        resp = client.get("/api/v1/animals", params={"offset": -1}, headers=headers)
    assert resp.status_code == 422


def test_list_animals_offset_above_cap_returns_422() -> None:
    # offset is capped at int32 max (2_147_483_647) to stay safely within
    # Postgres bigint OFFSET and avoid unbounded values reaching asyncpg.
    # One past the cap must be rejected.
    with patch(
        "petdata.modules.auth.dependencies._get_validator",
        return_value=_make_validator(),
    ):
        client, headers, _repo = _subscribed_client()
        resp = client.get(
            "/api/v1/animals", params={"offset": 2147483648}, headers=headers
        )
    assert resp.status_code == 422


def test_list_animals_valid_pagination_returns_200() -> None:
    # With get_repository overridden by a stub whose list_animals resolves
    # to an empty list, valid pagination params clear both query validation
    # and the auth/subscription guards, and the route renders a 200 with an
    # empty AnimalListResponse.
    with patch(
        "petdata.modules.auth.dependencies._get_validator",
        return_value=_make_validator(),
    ):
        client, headers, _repo = _subscribed_client()
        resp = client.get(
            "/api/v1/animals", params={"limit": 10, "offset": 0}, headers=headers
        )
    assert resp.status_code == 200
    assert resp.json()["count"] == 0


def test_list_animals_limit_at_max_returns_200() -> None:
    # limit is capped with ge=1, le=1000 (inclusive); 1000 must be accepted.
    # Would fail under an exclusive (gt/lt) implementation of the bound.
    with patch(
        "petdata.modules.auth.dependencies._get_validator",
        return_value=_make_validator(),
    ):
        client, headers, _repo = _subscribed_client()
        resp = client.get(
            "/api/v1/animals", params={"limit": 1000, "offset": 0}, headers=headers
        )
    assert resp.status_code == 200
    assert resp.json()["count"] == 0


def test_list_animals_limit_at_min_returns_200() -> None:
    # limit is capped with ge=1, le=1000 (inclusive); 1 must be accepted.
    # Would fail under an exclusive (gt/lt) implementation of the bound.
    with patch(
        "petdata.modules.auth.dependencies._get_validator",
        return_value=_make_validator(),
    ):
        client, headers, _repo = _subscribed_client()
        resp = client.get(
            "/api/v1/animals", params={"limit": 1, "offset": 0}, headers=headers
        )
    assert resp.status_code == 200
    assert resp.json()["count"] == 0

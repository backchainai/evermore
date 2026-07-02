"""Unit tests for JWKS-based JWT auth (no live Supabase or Postgres required)."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Annotated, Any
from unittest.mock import MagicMock, patch

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from evermore_auth import AuthUser, JwksValidator
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from jwt.algorithms import RSAAlgorithm

from petdata.main import create_app
from petdata.modules.auth.dependencies import require_admin, require_auth

if TYPE_CHECKING:
    from collections.abc import Generator

# ── Test RSA key pair ─────────────────────────────────────────────────────────

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


def _make_token_other_key() -> str:
    """Sign a token with a foreign key so the validator rejects the signature."""
    other_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    other_pem = other_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.TraditionalOpenSSL,
        serialization.NoEncryption(),
    )
    return jwt.encode(
        {"sub": "x", "aud": "authenticated", "exp": int(time.time()) + 60},
        other_pem,
        algorithm="RS256",
    )


@pytest.fixture
def validator() -> JwksValidator:
    return _make_validator()


# ── JwksValidator unit tests ──────────────────────────────────────────────────


def test_decode_valid_token(validator: JwksValidator) -> None:
    token = _make_token()
    payload = validator.decode(token)
    assert payload["sub"] == "user-uuid-1234"
    assert payload["email"] == "test@example.com"


def test_decode_expired_token(validator: JwksValidator) -> None:
    token = _make_token(exp_offset=-1)
    with pytest.raises(jwt.ExpiredSignatureError):
        validator.decode(token)


def test_decode_invalid_signature() -> None:
    token = _make_token_other_key()
    validator = _make_validator()
    with pytest.raises(jwt.InvalidSignatureError):
        validator.decode(token)


# ── FastAPI dependency tests (isolated mini app) ──────────────────────────────


def _make_app() -> FastAPI:
    app = FastAPI()

    @app.get("/protected")
    def protected(user: Annotated[AuthUser, Depends(require_auth)]) -> dict:
        return {"sub": user.sub, "is_admin": user.is_admin}

    @app.get("/admin")
    def admin_only(user: Annotated[AuthUser, Depends(require_admin)]) -> dict:
        return {"sub": user.sub}

    return app


@pytest.fixture
def client() -> Generator[TestClient]:
    # Patch _get_validator (resolved by name at call time) so the request-time
    # auth check uses the test key. The patch stays active for the request.
    with patch(
        "petdata.modules.auth.dependencies._get_validator",
        return_value=_make_validator(),
    ):
        yield TestClient(_make_app(), raise_server_exceptions=True)


def test_require_auth_valid_token(client: TestClient) -> None:
    token = _make_token()
    resp = client.get("/protected", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["sub"] == "user-uuid-1234"


def test_require_auth_missing_token(client: TestClient) -> None:
    resp = client.get("/protected")
    assert resp.status_code == 401


def test_require_auth_invalid_signature(client: TestClient) -> None:
    token = _make_token_other_key()
    resp = client.get("/protected", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401


def test_require_auth_expired_token(client: TestClient) -> None:
    token = _make_token(exp_offset=-1)
    resp = client.get("/protected", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401


def test_require_admin_non_admin(client: TestClient) -> None:
    token = _make_token(is_admin=False)
    resp = client.get("/admin", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403


def test_require_admin_is_admin(client: TestClient) -> None:
    token = _make_token(is_admin=True)
    resp = client.get("/admin", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["sub"] == "user-uuid-1234"


# ── Real-app checks (no DB: auth fires before the repository) ──────────────────


@pytest.fixture
def app_client() -> Generator[TestClient]:
    with patch(
        "petdata.modules.auth.dependencies._get_validator",
        return_value=_make_validator(),
    ):
        yield TestClient(create_app(), raise_server_exceptions=True)


def test_animals_route_requires_auth(app_client: TestClient) -> None:
    # No token: auth rejects before the DB-backed repository is ever touched.
    resp = app_client.get("/api/v1/animals")
    assert resp.status_code == 401


def test_animals_route_requires_subscription(app_client: TestClient) -> None:
    # Authenticated but not subscribed to petdata: the subscription guard
    # rejects before the DB-backed repository is ever touched.
    token = _make_token(subscribed_tools=["some-other-tool"])
    resp = app_client.get(
        "/api/v1/animals", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 403
    assert resp.json()["detail"] == {
        "error": "subscription_required",
        "module": "petdata",
    }


def test_animals_route_subscribed_passes_guard() -> None:
    # Subscribed to petdata: the request clears the auth + subscription
    # guards. There's no database in unit tests, so the DB-backed repository
    # raises once the guard passes; use a local client with
    # raise_server_exceptions=False so that failure surfaces as a status
    # code rather than an exception, and assert only that the guard itself
    # did not reject (not 401/403).
    token = _make_token(subscribed_tools=["petdata"])
    with patch(
        "petdata.modules.auth.dependencies._get_validator",
        return_value=_make_validator(),
    ):
        local_client = TestClient(create_app(), raise_server_exceptions=False)
        resp = local_client.get(
            "/api/v1/animals", headers={"Authorization": f"Bearer {token}"}
        )
    assert resp.status_code not in (401, 403)


def test_health_stays_open(app_client: TestClient) -> None:
    # /health is unauthenticated and degrades gracefully without a database.
    resp = app_client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] in {"healthy", "degraded"}

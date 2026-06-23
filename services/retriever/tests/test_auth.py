"""Unit tests for JWKS-based JWT auth (no live Supabase required)."""

import time
from collections.abc import Generator
from typing import Annotated, Any
from unittest.mock import MagicMock, patch

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from jwt.algorithms import RSAAlgorithm

from retriever.modules.auth.dependencies import require_admin, require_auth
from retriever.modules.auth.jwks import JwksValidator
from retriever.modules.auth.schemas import AuthUser

# ── Test RSA key pair ─────────────────────────────────────────────────────────

_PRIVATE_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
_PUBLIC_KEY = _PRIVATE_KEY.public_key()


def _make_token(
    sub: str = "user-uuid-1234",
    email: str = "test@example.com",
    is_admin: bool = False,
    exp_offset: int = 3600,
) -> str:
    payload: dict[str, Any] = {
        "sub": sub,
        "email": email,
        "aud": "authenticated",
        "app_metadata": {"is_admin": is_admin},
        "iat": int(time.time()),
        "exp": int(time.time()) + exp_offset,
    }
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


@pytest.fixture
def validator() -> JwksValidator:
    return _make_validator()


@pytest.fixture
def override_validator() -> Generator[None]:
    """Patch _get_validator so FastAPI dependencies use the test key."""
    with patch(
        "retriever.modules.auth.dependencies._get_validator",
        return_value=_make_validator(),
    ):
        yield


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
    other_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    other_pem = other_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.TraditionalOpenSSL,
        serialization.NoEncryption(),
    )
    token = jwt.encode(
        {"sub": "x", "aud": "authenticated", "exp": int(time.time()) + 60},
        other_pem,
        algorithm="RS256",
    )
    validator = _make_validator()
    with pytest.raises(jwt.InvalidSignatureError):
        validator.decode(token)


# ── FastAPI dependency tests ──────────────────────────────────────────────────


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
def client(override_validator: None) -> TestClient:
    return TestClient(_make_app(), raise_server_exceptions=True)


def test_require_auth_valid_token(client: TestClient) -> None:
    token = _make_token()
    resp = client.get("/protected", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["sub"] == "user-uuid-1234"


def test_require_auth_missing_token(client: TestClient) -> None:
    resp = client.get("/protected")
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

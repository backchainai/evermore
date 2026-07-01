"""Unit tests for the shared evermore_auth package (no live Supabase required)."""

import time
from typing import Annotated, Any
from unittest.mock import MagicMock

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from jwt.algorithms import RSAAlgorithm

from evermore_auth import AuthDependencies, AuthUser, JwksValidator

# ── Test RSA key pair ─────────────────────────────────────────────────────────

_PRIVATE_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
_PUBLIC_KEY = _PRIVATE_KEY.public_key()


def _make_token(
    sub: str = "user-uuid-1234",
    email: str = "test@example.com",
    is_admin: bool = False,
    subscribed_tools: list[str] | None = None,
    exp_offset: int = 3600,
) -> str:
    payload: dict[str, Any] = {
        "sub": sub,
        "email": email,
        "aud": "authenticated",
        "app_metadata": {"is_admin": is_admin},
        "subscribed_tools": subscribed_tools if subscribed_tools is not None else [],
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


@pytest.fixture
def deps() -> AuthDependencies:
    return AuthDependencies(_make_validator)


@pytest.fixture
def client(deps: AuthDependencies) -> TestClient:
    app = FastAPI()
    require_auth = deps.require_auth
    require_admin = deps.require_admin
    require_widgets = deps.require_subscription("widgets")

    @app.get("/protected")
    def protected(user: Annotated[AuthUser, Depends(require_auth)]) -> dict[str, Any]:
        return {
            "sub": user.sub,
            "is_admin": user.is_admin,
            "subscribed_tools": list(user.subscribed_tools),
        }

    @app.get("/admin")
    def admin_only(user: Annotated[AuthUser, Depends(require_admin)]) -> dict[str, Any]:
        return {"sub": user.sub}

    @app.get("/widgets")
    def widgets(user: Annotated[AuthUser, Depends(require_widgets)]) -> dict[str, Any]:
        return {"sub": user.sub}

    return TestClient(app, raise_server_exceptions=True)


def test_require_auth_valid_token(client: TestClient) -> None:
    token = _make_token(subscribed_tools=["widgets"])
    resp = client.get("/protected", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["sub"] == "user-uuid-1234"
    assert body["subscribed_tools"] == ["widgets"]


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


def test_require_subscription_present(client: TestClient) -> None:
    token = _make_token(subscribed_tools=["widgets", "gadgets"])
    resp = client.get("/widgets", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["sub"] == "user-uuid-1234"


def test_require_subscription_absent(client: TestClient) -> None:
    token = _make_token(subscribed_tools=["gadgets"])
    resp = client.get("/widgets", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403
    assert resp.json()["detail"] == {
        "error": "subscription_required",
        "module": "widgets",
    }


# ── AuthUser claim population ──────────────────────────────────────────────────


def test_auth_user_subscribed_tools_default() -> None:
    user = AuthUser(sub="s", email="e", is_admin=False)
    assert user.subscribed_tools == ()


def test_auth_user_populated_from_claim() -> None:
    deps = AuthDependencies(_make_validator)
    require_auth = deps.require_auth
    app = FastAPI()

    @app.get("/me")
    def me(
        user: Annotated[AuthUser, Depends(require_auth)],
    ) -> dict[str, Any]:
        return {"subscribed_tools": list(user.subscribed_tools)}

    client = TestClient(app, raise_server_exceptions=True)
    token = _make_token(subscribed_tools=["widgets", "gadgets"])
    resp = client.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["subscribed_tools"] == ["widgets", "gadgets"]

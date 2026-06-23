"""Shared fixtures for live-server integration tests.

These tests hit real running services (backend on :8000, Supabase on :54321).
They are fundamentally different from the unit tests which mock all dependencies.

Required environment:
    SUPABASE_ANON_KEY       — from `supabase status`
    SUPABASE_SERVICE_ROLE_KEY — from `supabase status` (for admin promotion)

Optional overrides:
    RETRIEVER_BASE_URL      — default http://localhost:8000
    SUPABASE_URL            — default http://127.0.0.1:54321
"""

from __future__ import annotations

import os
import uuid
from collections.abc import AsyncGenerator

import httpx
import pytest
import pytest_asyncio

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

RETRIEVER_BASE_URL = os.getenv("RETRIEVER_BASE_URL", "http://localhost:8000")
SUPABASE_URL = os.getenv("SUPABASE_URL", "http://127.0.0.1:54321")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

# Unique per-run to avoid collisions with leftover test data
_RUN_ID = uuid.uuid4().hex[:8]
_REGULAR_EMAIL = f"inttest-regular-{_RUN_ID}@test.local"
_ADMIN_EMAIL = f"inttest-admin-{_RUN_ID}@test.local"
_PASSWORD = "testpass123"

# Shared test constant
NIL_UUID = "00000000-0000-0000-0000-000000000000"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _signup(
    client: httpx.AsyncClient,
    email: str,
    password: str,
    anon_key: str,
) -> tuple[str, str]:
    """Sign up a user via Supabase GoTrue.

    Local Supabase auto-confirms emails, so signup returns a full session.

    Returns:
        (user_id, access_token) tuple.
    """
    resp = await client.post(
        f"{SUPABASE_URL}/auth/v1/signup",
        headers={"apikey": anon_key, "Content-Type": "application/json"},
        json={"email": email, "password": password},
    )
    resp.raise_for_status()
    data = resp.json()
    return str(data["user"]["id"]), str(data["access_token"])


async def _signin(
    client: httpx.AsyncClient,
    email: str,
    password: str,
    anon_key: str,
) -> str:
    """Sign in and return the access_token."""
    resp = await client.post(
        f"{SUPABASE_URL}/auth/v1/token?grant_type=password",
        headers={"apikey": anon_key, "Content-Type": "application/json"},
        json={"email": email, "password": password},
    )
    resp.raise_for_status()
    return str(resp.json()["access_token"])


async def _promote_admin(
    client: httpx.AsyncClient,
    user_id: str,
    service_role_key: str,
) -> None:
    """Promote a user to admin via the Supabase admin API."""
    resp = await client.put(
        f"{SUPABASE_URL}/auth/v1/admin/users/{user_id}",
        headers={
            "apikey": service_role_key,
            "Authorization": f"Bearer {service_role_key}",
            "Content-Type": "application/json",
        },
        json={
            "app_metadata": {
                "provider": "email",
                "providers": ["email"],
                "is_admin": True,
            }
        },
    )
    resp.raise_for_status()


# ---------------------------------------------------------------------------
# Skip logic
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True, scope="session")
def _require_integration_env() -> None:
    """Skip the entire integration suite if keys are missing."""
    if not SUPABASE_ANON_KEY:
        pytest.skip("SUPABASE_ANON_KEY not set — skipping integration tests")
    if not SUPABASE_SERVICE_ROLE_KEY:
        pytest.skip("SUPABASE_SERVICE_ROLE_KEY not set — skipping integration tests")


# ---------------------------------------------------------------------------
# Session-scoped fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def base_url() -> str:
    return RETRIEVER_BASE_URL


@pytest.fixture(scope="session")
def anon_key() -> str:
    return SUPABASE_ANON_KEY


@pytest.fixture(scope="session")
def service_role_key() -> str:
    return SUPABASE_SERVICE_ROLE_KEY


@pytest_asyncio.fixture(scope="session")
async def _session_client() -> AsyncGenerator[httpx.AsyncClient]:
    """Long-lived client for session-scoped auth setup."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        yield client


@pytest_asyncio.fixture(scope="session")
async def _backend_reachable(
    base_url: str,
    _session_client: httpx.AsyncClient,
) -> None:
    """Ping /health; skip entire suite if backend is not running."""
    try:
        resp = await _session_client.get(f"{base_url}/health", timeout=5.0)
        resp.raise_for_status()
    except (httpx.ConnectError, httpx.HTTPStatusError):
        pytest.skip(f"Backend not reachable at {base_url} — skipping integration tests")


@pytest_asyncio.fixture(scope="session")
async def regular_user_token(
    _backend_reachable: None,
    _session_client: httpx.AsyncClient,
    anon_key: str,
) -> str:
    """Sign up a regular (non-admin) user and return their JWT."""
    _user_id, token = await _signup(
        _session_client, _REGULAR_EMAIL, _PASSWORD, anon_key
    )
    return token


@pytest_asyncio.fixture(scope="session")
async def admin_user_token(
    _backend_reachable: None,
    _session_client: httpx.AsyncClient,
    anon_key: str,
    service_role_key: str,
) -> str:
    """Sign up a user, promote to admin, re-sign-in for a fresh JWT."""
    user_id, _initial_token = await _signup(
        _session_client, _ADMIN_EMAIL, _PASSWORD, anon_key
    )
    await _promote_admin(_session_client, user_id, service_role_key)
    # Re-sign-in to pick up updated app_metadata.is_admin in the JWT
    return await _signin(_session_client, _ADMIN_EMAIL, _PASSWORD, anon_key)


# ---------------------------------------------------------------------------
# Per-test fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def http_client(
    base_url: str,
    _backend_reachable: None,
) -> AsyncGenerator[httpx.AsyncClient]:
    """Fresh httpx client pointing at the backend, per test."""
    async with httpx.AsyncClient(base_url=base_url, timeout=30.0) as client:
        yield client


@pytest_asyncio.fixture
async def authed_client(
    base_url: str,
    regular_user_token: str,
) -> AsyncGenerator[httpx.AsyncClient]:
    """Client pre-configured with a regular user's Bearer token."""
    async with httpx.AsyncClient(
        base_url=base_url,
        timeout=30.0,
        headers={"Authorization": f"Bearer {regular_user_token}"},
    ) as client:
        yield client


@pytest_asyncio.fixture
async def admin_client(
    base_url: str,
    admin_user_token: str,
) -> AsyncGenerator[httpx.AsyncClient]:
    """Client pre-configured with an admin user's Bearer token."""
    async with httpx.AsyncClient(
        base_url=base_url,
        timeout=30.0,
        headers={"Authorization": f"Bearer {admin_user_token}"},
    ) as client:
        yield client

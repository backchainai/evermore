"""Unit tests for the async engine URL coercion."""

from __future__ import annotations

import pytest

from petdata.models.base import _async_url


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (
            "postgres://u:p@host:5432/db",
            "postgresql+asyncpg://u:p@host:5432/db",
        ),
        (
            "postgresql://u:p@host:5432/db",
            "postgresql+asyncpg://u:p@host:5432/db",
        ),
        (
            "postgresql+asyncpg://u:p@host:5432/db",
            "postgresql+asyncpg://u:p@host:5432/db",
        ),
        (
            "postgresql+psycopg://u:p@host/db",
            "postgresql+asyncpg://u:p@host/db",
        ),
    ],
)
def test_async_url_coerces_driver(raw: str, expected: str) -> None:
    assert _async_url(raw) == expected


def test_async_url_strips_trailing_sslmode() -> None:
    result = _async_url("postgresql://u:p@host/db?sslmode=require")
    assert result == "postgresql+asyncpg://u:p@host/db"


def test_async_url_strips_leading_sslmode_keeps_other_params() -> None:
    result = _async_url("postgresql://u:p@host/db?sslmode=require&application_name=x")
    assert result == "postgresql+asyncpg://u:p@host/db?application_name=x"

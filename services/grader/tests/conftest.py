"""Pytest configuration and shared fixtures."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from fastapi.testclient import TestClient

from grader.main import create_app

if TYPE_CHECKING:
    from collections.abc import Iterator


@pytest.fixture
def client() -> Iterator[TestClient]:
    """Provide a TestClient for the grader app.

    grader has no data layer, so constructing the app needs no external
    service; the client is safe to build directly in the fixture.
    """
    with TestClient(create_app()) as test_client:
        yield test_client

"""Pytest configuration and shared fixtures."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

# Force the SQLite path to a per-process temp location before importing the
# app: its module-level singleton (`petbio.main.app`) instantiates on import,
# so an inherited PETBIO_DATABASE_PATH would otherwise run migrations on the
# developer's real database. A fresh mkdtemp per session avoids cross-worker
# (pytest-xdist) and cross-run collisions on a shared file.
os.environ["PETBIO_DATABASE_PATH"] = str(
    Path(tempfile.mkdtemp(prefix="petbio-test-import-")) / "petbio.db"
)

from fastapi.testclient import TestClient

from petbio.main import create_app

if TYPE_CHECKING:
    from collections.abc import Iterator


@pytest.fixture
def sample_data() -> dict[str, str]:
    """Provide sample test data."""
    return {"key": "value"}


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    """Provide a TestClient backed by a fresh per-test SQLite database."""
    monkeypatch.setenv("PETBIO_DATABASE_PATH", str(tmp_path / "petbio.db"))
    with TestClient(create_app()) as test_client:
        yield test_client

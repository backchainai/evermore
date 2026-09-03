"""Structural checks on docker-compose.yml and its Dockerfile (AC1 grade).

The compose file is parsed as YAML (not matched as raw text) so an invalid
document, a commented-out port mapping, or a "/health" that only appears in
a comment all fail the relevant assertion instead of silently passing.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

SERVICE_ROOT = Path(__file__).parent.parent
COMPOSE_PATH = SERVICE_ROOT / "docker-compose.yml"
DOCKERFILE_PATH = SERVICE_ROOT / "Dockerfile"


def _grader_service() -> dict[str, Any]:
    """Parse docker-compose.yml and return the grader service definition.

    A malformed document fails here, not later.
    """
    doc = yaml.safe_load(COMPOSE_PATH.read_text())
    assert isinstance(doc, dict)
    service = doc["services"]["grader"]
    assert isinstance(service, dict)
    return service


def test_compose_maps_port_8003() -> None:
    """The grader service publishes host port 8003 mapped to container 8000."""
    service = _grader_service()

    assert "8003:8000" in service["ports"]


def test_compose_has_health_healthcheck() -> None:
    """The grader service's healthcheck targets /health."""
    service = _grader_service()

    healthcheck = service["healthcheck"]
    assert "/health" in " ".join(healthcheck["test"])


def test_compose_port_matches_dockerfile_expose_and_uvicorn_port() -> None:
    """The compose mapping's container-side port matches what the Dockerfile
    actually EXPOSEs and serves on.

    Nothing else ties these together: the Dockerfile's EXPOSE/uvicorn
    --port could change (e.g. to 8080) and `docker compose up` would break
    even with every other test green.
    """
    service = _grader_service()
    container_port = service["ports"][0].split(":")[1]

    dockerfile_text = DOCKERFILE_PATH.read_text()

    expose_match = re.search(r"^EXPOSE\s+(\d+)", dockerfile_text, re.MULTILINE)
    assert expose_match is not None, "Dockerfile has no EXPOSE instruction"
    assert expose_match.group(1) == container_port

    uvicorn_port_match = re.search(r'"--port",\s*"(\d+)"', dockerfile_text)
    assert uvicorn_port_match is not None, "Dockerfile CMD has no --port flag"
    assert uvicorn_port_match.group(1) == container_port

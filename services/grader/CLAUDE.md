# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project: Profile Grader (grader)

Mechanical and, later, LLM-assisted grading for Evermore kennel card
Compositions. This is the tech-stack scaffold (issue #293): a health
endpoint, `/llms.txt` discovery, and structured logging/tracing. No
domain grading logic, data layer, or auth are wired up yet: those land in
#294 (domain), #296 (data layer), #298 (auth).

**Architecture:** Standalone FastAPI service, no database (yet).

**Stack:** Python 3.14, FastAPI, Pydantic 2.x, pydantic-settings, structlog
(JSON logging), OpenTelemetry API (tracing scaffolding only, no SDK/exporter).

## Commands

Run from this directory (`services/grader/`):

```bash
# Install dependencies (including dev tooling)
uv sync --extra dev

# Run development server
uv run uvicorn grader.main:app --reload --port 8003

# Tests
uv run pytest

# Quality gates (must all pass before commit)
uv run ruff format src/ tests/
uv run ruff check src/ tests/
uvx bandit -r src/ -q
uv run mypy src/
```

## Environment

Environment variables use the `GRADER_` prefix (pydantic-settings). Copy
`.env.example` to `.env` and adjust. See `src/grader/config.py` for the
full `Settings` model.

## Local development (Docker)

```bash
cp .env.example .env
docker compose up -d          # builds and runs grader on host port 8003
docker compose down
```

Port 8003 is reserved for grader in the local stack (8001 retriever, 8002
petdata are taken).

## Project structure

```
src/grader/
├── config.py                      # Settings via pydantic-settings (GRADER_ prefix)
├── main.py                        # FastAPI application factory (create_app)
└── observability/
    ├── logging.py                 # structlog JSON configuration + OTel trace correlation
    └── tracing.py                 # OpenTelemetry API-only tracer + traced_span helper

tests/
├── conftest.py                    # TestClient(create_app()) fixture
├── test_health.py                 # GET /health, create_app() smoke test
├── test_llms_txt.py               # GET /llms.txt
├── test_logging.py                # structlog JSON rendering
└── test_compose.py                # docker-compose.yml port/healthcheck assertions
```

## Coding conventions

### Configuration management

```python
from grader.config import get_settings

settings = get_settings()
```

### Observability

- `configure_logging(debug=...)` (called from `create_app()`) sets up
  structlog to emit one line of JSON per event in production, and a
  human-readable console renderer in debug mode.
- `tracing.py` exposes a module-level `tracer` and a `traced_span(name)`
  context manager. No `TracerProvider`/exporter is configured here (API
  only, per the tech-stack standard); spans are no-ops until a host
  process installs a real SDK provider.

### Type hints

Required everywhere (mypy --strict enforced): typed signatures and return
types (including `-> None`). Use `from __future__ import annotations` for
forward references.

## Out of scope (tracked separately)

- Domain grading logic: #294
- Data layer (persistence for grades/history): #296
- Auth: #298
- CI wiring (`.github/workflows/`): follow-up, not part of this scaffold

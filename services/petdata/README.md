---
name: readme
description: Read for project overview, setup instructions, and usage. Entry point for new contributors.
category: root
when_to_use:
- Starting a new project
---
# petdata

Automated adoption profile generator for animal shelters

## Overview

petdata extracts animal data from shelter management systems, analyzes behavioral trends using time-decay algorithms, and generates evidence-based adoption profiles using LLMs. Built for nonprofit animal shelters.

**Current Status:** Phase 1 complete (data extraction and storage infrastructure)

## Features

### Phase 1: Data Extraction and Storage (✓ Complete)

- **7 Pydantic data models:** Animal, VolunteerNote, KennelCard, StaffAssessment, WalkRecord, AnimalImage, SyncLog
- **Supabase Postgres + pgvector** accessed through async SQLAlchemy 2.0 (asyncpg), with foreign keys, indexes, and cascade deletes
- **Repository pattern** with full async CRUD operations over a request-scoped session
- **Alembic migrations** own the schema (`uv run alembic upgrade head`)
- **Comprehensive test coverage:** unit suite plus a Postgres-backed integration suite
- **Quality tooling:** ruff, mypy (strict mode), bandit, pytest with coverage

### Phase 2: Behavioral Analysis (Planned)

- Time-decay algorithm for volunteer behavioral ratings
- Recent observations weighted more heavily (exponential decay)
- Behavioral trend detection over animal's shelter stay
- Aggregate scoring with confidence levels

### Phase 3: LLM Profile Generation (Planned)

- Automated adoption profile creation using Claude/GPT
- Evidence-based behavioral descriptions from analysis
- Shelter-approved content guidelines and templates
- Profile quality validation and versioning

## Quick Start

### Prerequisites

- Python 3.14
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- Docker (for the local Postgres + pgvector container)

### Installation

```bash
# Clone the repository
git clone https://github.com/backchainai/evermore.git
cd evermore/services/petdata

# Install dependencies (including dev tooling)
uv sync --extra dev

# Configure the environment
cp .env.example .env        # adjust PETDATA_DATABASE_URL if needed
```

### Local database (one command)

petdata stores data in Supabase Postgres with the pgvector extension. For local
development and tests, `docker-compose.test.yml` brings up an ephemeral pgvector
container on port 5434:

```bash
docker compose -f docker-compose.test.yml up -d   # start local Postgres + pgvector
uv run alembic upgrade head                        # apply the schema
```

The default `PETDATA_DATABASE_URL` in `.env.example` points at this container.
Stop and discard it with `docker compose -f docker-compose.test.yml down`.

## Usage

```bash
# Run the API (schema must already be migrated; see Local database above)
uv run uvicorn petdata.main:app --reload
```

## Configuration

Configuration is handled via environment variables (prefix: `PETDATA_`). See
`.env.example` for the full set; the database options are:

| Variable | Description | Default |
|----------|-------------|---------|
| `PETDATA_DATABASE_URL` | Async Postgres connection URL (`postgres://`/`postgresql://` accepted) | `` (empty) |
| `PETDATA_DATABASE_REQUIRE_SSL` | Enforce SSL on the connection (set `true` in production) | `false` |
| `PETDATA_REQUEST_DELAY_MS` | Extraction API request throttling delay (ms) | `500` |

## HTTP API

petdata exposes a FastAPI service (run with `uv run uvicorn petdata.main:app`).

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/health` | none | Service and database health check. |
| `GET` | `/api/v1/animals` | none | List animals (paginated via `limit`, `offset`). |
| `GET` | `/api/v1/animals/{animal_id}` | none | Animal detail with related records. |
| `GET` | `/llms.txt` | none | LLM-friendly API manifest generated from the OpenAPI schema. |

### `/llms.txt`

Per the Evermore tech-stack standard, the service publishes an [llms.txt](https://llmstxt.org/) manifest at `/llms.txt` so LLM agents can discover the API surface at runtime without parsing the full OpenAPI spec. It is generated from the live OpenAPI schema by [`fast-llms-txt`](https://pypi.org/project/fast-llms-txt/) and served unauthenticated as a discovery endpoint.

```bash
curl http://localhost:8000/llms.txt
```

## Development

### Setup

```bash
# Clone repository
git clone https://github.com/backchainai/evermore.git
cd evermore/services/petdata

# Install dependencies (including dev tooling)
uv sync --extra dev

# Start local Postgres + pgvector and run tests
docker compose -f docker-compose.test.yml up -d
uv run pytest
```

The integration suite (`tests/integration/db/`) requires the local Postgres
container above and skips automatically when no database is reachable, so the
unit suite still runs on a bare checkout. Override the connection string with
`TEST_DATABASE_URL`.

### Quality Gates

All checks must pass before committing:

```bash
uv run ruff format src/ tests/        # Auto-format code
uv run ruff check src/ tests/         # Lint
uv run bandit -r src/                 # Security scan
uv run mypy src/                      # Type check (strict mode)
uv run pytest tests/ --cov=src --cov-report=term-missing  # Tests + coverage
```

### Project Structure

```
src/petdata/
├── config.py                      # pydantic-settings configuration
├── main.py                        # FastAPI application factory
├── models/                        # SQLAlchemy ORM layer
│   ├── base.py                    # Declarative base + async engine/session factory
│   ├── tables.py                  # 7 ORM tables (petdata_ prefix, tenant_id for RLS)
│   └── mappers.py                 # ORM row <-> Pydantic domain model mapping
├── infrastructure/
│   └── database/session.py        # FastAPI async session dependency
└── modules/
    ├── db/
    │   ├── models.py              # 7 Pydantic domain models
    │   └── repository.py          # Async Database class with CRUD operations
    ├── api/                       # SMS extraction client
    └── web/                       # API routes and schemas

alembic/                           # Migration environment (schema source of truth)
alembic.ini

tests/
├── unit/                          # Fast, isolated tests (no database)
└── integration/                   # Postgres-backed tests
    └── db/                        # Repository round-trips, Alembic upgrade/downgrade
```

## Documentation

- [Architecture Overview](docs/design/architecture.md) - System design and patterns
- [Phase 1 Design](docs/design/phase1-data-extraction.md) - Data extraction implementation details
- [Development Standards](docs/design/development-standards.md) - Git workflow, testing, quality gates
- [Architecture Decision Records](docs/adr/) - Key architectural decisions
- [TODO](TODO.md) - Future work and roadmap

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Development setup and workflow
- Code quality requirements
- Testing guidelines
- PR process

## License

Apache License 2.0 (Apache-2.0). See [LICENSE](LICENSE) for the full text and [NOTICE](NOTICE) for attribution.

Copyright (C) 2026 Backchain LLC

## Acknowledgments

Built for nonprofit animal shelters

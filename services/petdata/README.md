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
- **SQLite database** with foreign keys, indexes, and migration-based schema management
- **Repository pattern** with full CRUD operations and transaction support
- **Migration system** with version tracking, checksum verification, and idempotent SQL
- **Comprehensive test coverage:** 187 passing tests (unit + integration)
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

- Python 3.13
- [uv](https://docs.astral.sh/uv/) (Python package manager)

### Installation

```bash
# Clone the repository
git clone https://github.com/backchainai/evermore.git
cd evermore/services/petdata

# Install dependencies
uv sync

# Run the application
uv run petdata
```

## Usage

```bash
# Example command
uv run petdata --help
```

## Configuration

Configuration is handled via environment variables (prefix: `PETDATA_`):

| Variable | Description | Default |
|----------|-------------|---------|
| `PETDATA_DATABASE_PATH` | SQLite database file location | `data/petdata.db` |
| `PETDATA_REQUEST_DELAY_MS` | API request throttling delay (ms) | `500` |

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

# Install dependencies
uv sync

# Run tests
uv run pytest
```

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
└── modules/
    └── db/                        # Phase 1: Data layer
        ├── models.py              # 7 Pydantic models
        ├── schema.py              # SQLite table definitions
        ├── migrate.py             # Migration engine with version tracking
        ├── repository.py          # Database class with CRUD operations
        └── migrations/            # Numbered SQL migration files

tests/
├── unit/                          # Fast, isolated tests
│   └── db/                        # Model, migration, schema tests
└── integration/                   # Tests with real SQLite database
    └── db/                        # Repository, migration flow tests
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

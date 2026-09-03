# grader

Profile Grader for Evermore kennel card compositions.

## Overview

grader mechanically and, later, model-assisted grades a generated
Composition against its source Package, so staff and pipelines get a score
before a card goes out. This is the tech-stack scaffold (issue #293): a
health endpoint, `/llms.txt` discovery, and structured logging/tracing. No
domain grading logic, data layer, or auth are wired up yet (tracked
separately: #294, #296, #298).

## Quick start

```bash
cd services/grader
uv sync --extra dev
cp .env.example .env
uv run uvicorn grader.main:app --reload --port 8003
```

## Configuration

Environment variables use the `GRADER_` prefix (pydantic-settings). See
`.env.example` for the full set.

## Development

```bash
uv run pytest                          # tests
uv run ruff format src/ tests/         # format
uv run ruff check src/ tests/          # lint
uvx bandit -r src/ -q                  # security scan
uv run mypy src/                       # type check (strict)
```

See `CLAUDE.md` for the full gate sequence and project layout.

## License

Apache License 2.0 (Apache-2.0). See the root
[LICENSE](../../LICENSE) for the full text.

Copyright (C) 2026 Backchain LLC

# syntax=docker/dockerfile:1

# This Dockerfile builds from the SERVICE-DIRECTORY context (services/grader/),
# unlike services/petdata's Dockerfile, which builds from the repo root because
# petdata depends on a sibling `packages/*` path source. grader has no such
# dependency, so all COPY paths below are service-relative and the build
# context is just this directory.

# --- Build stage ---
FROM python:3.14-slim AS builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /app

# Build the venv at its final runtime path so uv's console-script shebangs
# (absolute, non-relocatable) stay valid after COPY into the runtime stage.
ENV UV_PROJECT_ENVIRONMENT=/app/.venv

# Dependency manifests first for layer caching.
COPY pyproject.toml uv.lock ./

# --no-editable installs grader (once copied below) as a built wheel, so the
# runtime stage needs only the venv, not the source tree.
RUN uv sync --frozen --no-install-project --no-dev --no-editable

# Copy source and README (needed by the project-wheel build) and install the
# project itself.
COPY src/ ./src/
COPY README.md ./
RUN uv sync --frozen --no-dev --no-editable

# --- Runtime stage ---
FROM python:3.14-slim AS runtime

# curl for the healthcheck (no libpq/asyncpg: grader has no data layer)
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Non-root user
RUN useradd --system --create-home --shell /bin/bash grader
WORKDIR /app

# Copy the virtualenv from builder. The venv is built directly at
# /app/.venv (UV_PROJECT_ENVIRONMENT), so no relocation happens here.
# grader is installed into the venv as a non-editable wheel, so no
# separate copy of src/ is needed at runtime.
COPY --from=builder /app/.venv /app/.venv

USER grader

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f "http://localhost:8000/health" || exit 1

CMD ["uvicorn", "grader.main:app", "--host", "0.0.0.0", "--port", "8000"]

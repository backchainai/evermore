# syntax=docker/dockerfile:1

# This Dockerfile builds from the REPO-ROOT context, not the service directory
# (see services/retriever/wrangler.jsonc `image_build_context: "../.."`).
# retriever depends on the sibling shared package `packages/auth` via a uv path
# source (`../../packages/auth`); a service-root context would place that path
# outside the build context and break `uv sync --frozen`. Building from the repo
# root keeps the sibling reachable. This is the monorepo pattern for any
# `services/*` module that consumes a `packages/*` sibling. All COPY paths below
# are repo-root-relative; nothing uses `COPY . .`, so no worker/env/secret files
# enter the image.

# --- Build stage ---
FROM python:3.13-slim AS builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /app

# Copy the shared package this service depends on via a uv path source
# (services/retriever/pyproject.toml -> ../../packages/auth). The build context
# is the repo root (wrangler image_build_context), so the sibling is reachable.
COPY packages/auth/ ./packages/auth/

# retriever dependency manifests first for layer caching
COPY services/retriever/pyproject.toml services/retriever/uv.lock services/retriever/README.md ./services/retriever/

WORKDIR /app/services/retriever

# --no-editable installs evermore-auth (and later retriever) as built wheels into
# the venv, so the runtime stage needs only the venv, not the source trees.
RUN uv sync --frozen --no-install-project --no-dev --no-editable

# Copy source and install project
COPY services/retriever/src/ ./src/
RUN uv sync --frozen --no-dev --no-editable

# --- Runtime stage ---
FROM python:3.13-slim AS runtime

# Install libpq for asyncpg and curl for the healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends libpq5 curl \
    && rm -rf /var/lib/apt/lists/*

# Non-root user
RUN useradd --system --create-home --shell /bin/bash retriever
WORKDIR /app

# Copy virtualenv and source from builder. The builder assembled them under
# /app/services/retriever (its WORKDIR); map them to /app so the runtime layout,
# PATH, entrypoint, and WORKDIR below stay unchanged.
COPY --from=builder /app/services/retriever/.venv /app/.venv
COPY --from=builder /app/services/retriever/src /app/src

COPY services/retriever/entrypoint.sh ./
RUN chmod +x entrypoint.sh

USER retriever

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

ENTRYPOINT ["./entrypoint.sh"]

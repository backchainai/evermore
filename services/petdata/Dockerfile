# syntax=docker/dockerfile:1

# This Dockerfile builds from the REPO-ROOT context, not the service directory
# (see services/petdata/wrangler.jsonc `image_build_context: "../.."`). petdata
# depends on the sibling shared package `packages/schema` via a uv path source
# (`../../packages/schema`); a service-root context would place that path outside
# the build context and break `uv sync --frozen`. Building from the repo root
# keeps the sibling reachable. This is the monorepo pattern for any `services/*`
# module that consumes a `packages/*` sibling. All COPY paths below are
# repo-root-relative; nothing uses `COPY . .`, so no worker/env/secret files
# enter the image.

# --- Build stage ---
FROM python:3.14-slim AS builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /app

# Copy the shared packages this service depends on via uv path sources
# (services/petdata/pyproject.toml -> ../../packages/schema and
# ../../packages/auth). The build context is the repo root (wrangler
# image_build_context), so the siblings are reachable.
COPY packages/schema/ ./packages/schema/
COPY packages/auth/ ./packages/auth/

# petdata dependency manifests first for layer caching
COPY services/petdata/pyproject.toml services/petdata/uv.lock services/petdata/README.md ./services/petdata/

WORKDIR /app/services/petdata

# --no-editable installs evermore-schema (and later petdata) as built wheels into
# the venv, so the runtime stage needs only the venv, not the source trees.
RUN uv sync --frozen --no-install-project --no-dev --no-editable

# Copy source and install project
COPY services/petdata/src/ ./src/
RUN uv sync --frozen --no-dev --no-editable

# --- Runtime stage ---
FROM python:3.14-slim AS runtime

# Install libpq for asyncpg and curl for the healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends libpq5 curl \
    && rm -rf /var/lib/apt/lists/*

# Non-root user
RUN useradd --system --create-home --shell /bin/bash petdata
WORKDIR /app

# Copy virtualenv and source from builder. The builder assembled them under
# /app/services/petdata (its WORKDIR); map them to /app so the runtime layout,
# PATH, entrypoint, and WORKDIR below stay unchanged.
COPY --from=builder /app/services/petdata/.venv /app/.venv
COPY --from=builder /app/services/petdata/src /app/src

COPY services/petdata/entrypoint.sh ./
RUN chmod +x entrypoint.sh

USER petdata

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f "http://localhost:${PORT:-8000}/health" || exit 1

ENTRYPOINT ["./entrypoint.sh"]

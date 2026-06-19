# syntax=docker/dockerfile:1

# --- Build stage ---
FROM python:3.13-slim AS builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /app

# Copy dependency files first for layer caching
COPY pyproject.toml uv.lock* README.md ./

# Install dependencies (without project source)
RUN uv sync --frozen --no-install-project --no-dev

# Copy source and install project
COPY src/ src/
RUN uv sync --frozen --no-dev

# --- Runtime stage ---
FROM python:3.13-slim AS runtime

# Install libpq for asyncpg
RUN apt-get update && apt-get install -y --no-install-recommends libpq5 curl \
    && rm -rf /var/lib/apt/lists/*

# Non-root user
RUN useradd --system --create-home --shell /bin/bash retriever
WORKDIR /app

# Copy virtualenv from builder
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/src /app/src

COPY entrypoint.sh ./
RUN chmod +x entrypoint.sh

USER retriever

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

ENTRYPOINT ["./entrypoint.sh"]

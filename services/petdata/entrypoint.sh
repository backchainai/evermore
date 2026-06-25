#!/bin/bash
set -euo pipefail
exec uvicorn petdata.main:app \
    --host "${HOST:-0.0.0.0}" \
    --port "${PORT:-8000}" \
    --workers "${WORKERS:-1}"

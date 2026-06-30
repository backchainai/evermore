# Copyright (C) 2025 Backchain LLC
# SPDX-License-Identifier: Apache-2.0

"""Export the FastAPI OpenAPI spec to a committed ``openapi.json``.

The committed spec is the contract source of truth consumed by the stacker
portal to generate its TypeScript types. A pytest verifies the committed file
stays in sync with ``app.openapi()``; CI fails on drift.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from retriever.main import app

# Resolve relative to this file so the output path is stable regardless of CWD.
OPENAPI_PATH = Path(__file__).resolve().parent.parent / "openapi.json"


def get_openapi_spec() -> dict[str, Any]:
    """Return the FastAPI-generated OpenAPI spec as a dict."""
    return app.openapi()


def serialize_spec(spec: dict[str, Any]) -> str:
    """Serialize the spec deterministically, with a trailing newline."""
    return json.dumps(spec, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def main() -> None:
    """Write the committed ``openapi.json`` from the live app spec."""
    OPENAPI_PATH.write_text(serialize_spec(get_openapi_spec()), encoding="utf-8")


if __name__ == "__main__":
    main()

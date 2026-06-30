# Copyright (C) 2025 Backchain LLC
# SPDX-License-Identifier: Apache-2.0

"""Verify the committed ``openapi.json`` stays in sync with the live app spec.

This guards the contract consumed by the stacker portal: the committed spec is
the source of truth for generated TypeScript types. If a route or model changes
without regenerating ``openapi.json``, this test fails and CI blocks the drift.
"""

from __future__ import annotations

from scripts.export_openapi import (
    OPENAPI_PATH,
    get_openapi_spec,
    serialize_spec,
)


def test_committed_openapi_spec_is_fresh() -> None:
    """The committed openapi.json equals the freshly serialized app spec."""
    committed = OPENAPI_PATH.read_text(encoding="utf-8")
    expected = serialize_spec(get_openapi_spec())
    assert committed == expected, (
        "services/retriever/openapi.json is stale. Regenerate it with "
        "`uv run python scripts/export_openapi.py`."
    )

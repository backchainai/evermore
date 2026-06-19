# Copyright (C) 2025 Backchain LLC
# SPDX-License-Identifier: Apache-2.0

"""Supabase Auth: JWKS-based JWT validation and FastAPI dependencies."""

from retriever.modules.auth.dependencies import require_admin, require_auth
from retriever.modules.auth.schemas import AuthUser

__all__ = ["AuthUser", "require_auth", "require_admin"]

# Copyright (C) 2025 Backchain LLC
# SPDX-License-Identifier: Apache-2.0

"""Supabase Auth: JWKS-based JWT validation and FastAPI dependencies."""

from evermore_auth import AuthUser

from retriever.modules.auth.dependencies import (
    require_admin,
    require_auth,
    require_subscription,
)

__all__ = ["AuthUser", "require_admin", "require_auth", "require_subscription"]

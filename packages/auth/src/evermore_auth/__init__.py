# Copyright (C) 2025 Backchain LLC
# SPDX-License-Identifier: Apache-2.0

"""Shared Supabase auth for Evermore: JWT validation and entitlement gating.

This package is the single canonical source for the JWKS-based Supabase JWT
validator (:class:`JwksValidator`), the validated-user record
(:class:`AuthUser`), and the service-agnostic FastAPI dependency factory
(:class:`AuthDependencies`) that builds ``require_auth``, ``require_admin``, and
``require_subscription`` route guards.
"""

from evermore_auth.dependencies import AuthDependencies
from evermore_auth.jwks import JwksValidator
from evermore_auth.schemas import AuthUser

__all__ = [
    "AuthDependencies",
    "AuthUser",
    "JwksValidator",
]

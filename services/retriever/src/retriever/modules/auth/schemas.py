# Copyright (C) 2025 Backchain LLC
# SPDX-License-Identifier: Apache-2.0

"""Auth data types."""

from dataclasses import dataclass


@dataclass(frozen=True)
class AuthUser:
    """Validated Supabase JWT payload."""

    sub: str  # Supabase user UUID
    email: str
    is_admin: bool  # from app_metadata.is_admin

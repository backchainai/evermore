# Copyright (C) 2025 Backchain LLC
# SPDX-License-Identifier: Apache-2.0

"""JWKS-based JWT validation for Supabase RS256 tokens."""

from typing import Any

import jwt


class JwksValidator:
    """Validates JWTs using the JWKS endpoint (RS256 only)."""

    def __init__(self, jwks_url: str) -> None:
        self._client = jwt.PyJWKClient(jwks_url, cache_keys=True)

    def decode(self, token: str) -> dict[str, Any]:
        """Decode and validate a JWT, returning the payload.

        Raises:
            jwt.PyJWTError: On any validation failure (expired, invalid sig, etc.).
        """
        signing_key = self._client.get_signing_key_from_jwt(token)
        return jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256", "ES256"],
            audience="authenticated",  # Supabase default audience claim
        )

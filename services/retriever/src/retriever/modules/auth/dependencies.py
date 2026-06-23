# Copyright (C) 2025 Backchain LLC
# SPDX-License-Identifier: Apache-2.0

"""FastAPI auth dependencies for route protection."""

from functools import lru_cache
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from retriever.config import get_settings
from retriever.modules.auth.jwks import JwksValidator
from retriever.modules.auth.schemas import AuthUser

_bearer = HTTPBearer()


@lru_cache(maxsize=1)
def _get_validator() -> JwksValidator:
    # Singleton: PyJWKClient(cache_keys=True) already handles key rotation
    # with a 300-second TTL, so a single instance is safe and avoids a
    # JWKS endpoint fetch on every authenticated request.
    settings = get_settings()
    if not settings.supabase_url:
        raise RuntimeError("SUPABASE_URL is not configured — cannot validate JWTs")
    jwks_url = f"{settings.supabase_url}/auth/v1/.well-known/jwks.json"
    return JwksValidator(jwks_url)


def require_auth(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_bearer)],
) -> AuthUser:
    """Validate Bearer JWT and return the authenticated user.

    Raises:
        HTTPException 401: If the token is missing, expired, or invalid.
    """
    try:
        payload = _get_validator().decode(credentials.credentials)
        sub = payload["sub"]
    except (jwt.PyJWTError, KeyError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    return AuthUser(
        sub=str(sub),
        email=str(payload.get("email", "")),
        is_admin=bool(payload.get("app_metadata", {}).get("is_admin", False)),
    )


def require_admin(
    user: Annotated[AuthUser, Depends(require_auth)],
) -> AuthUser:
    """Require the authenticated user to have admin privileges.

    Raises:
        HTTPException 403: If the user is not an admin.
    """
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user

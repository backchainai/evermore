# Copyright (C) 2025 Backchain LLC
# SPDX-License-Identifier: Apache-2.0

"""Service-agnostic FastAPI auth dependencies.

Each service constructs one :class:`AuthDependencies` from its own settings by
passing a ``validator_provider`` callable (typically a cached factory that reads
the service's Supabase URL and returns a :class:`JwksValidator`). The instance
exposes ``require_auth``, ``require_admin``, and ``require_subscription`` as
FastAPI dependencies. ``require_admin`` and ``require_subscription`` both chain
off the SAME instance's ``require_auth`` so a single request decodes the token
once.
"""

from collections.abc import Callable
from typing import TYPE_CHECKING, Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from evermore_auth.schemas import AuthUser

if TYPE_CHECKING:
    from evermore_auth.jwks import JwksValidator

AuthDependency = Callable[..., AuthUser]


class AuthDependencies:
    """Builds FastAPI auth dependencies bound to one validator provider."""

    require_auth: AuthDependency
    require_admin: AuthDependency

    def __init__(self, validator_provider: Callable[[], JwksValidator]) -> None:
        self._validator_provider = validator_provider
        bearer = HTTPBearer()

        def require_auth(
            credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer)],
        ) -> AuthUser:
            """Validate the Bearer JWT and return the authenticated user.

            Raises:
                HTTPException 401: If the token is missing, expired, or invalid.
            """
            return self._authenticate(credentials)

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

        # Bind the closures as instance attributes so they carry a `self`-free
        # signature FastAPI can introspect directly, and so require_admin
        # depends on THIS instance's require_auth.
        self.require_auth = require_auth
        self.require_admin = require_admin

    def _authenticate(self, credentials: HTTPAuthorizationCredentials) -> AuthUser:
        try:
            payload = self._validator_provider().decode(credentials.credentials)
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
            subscribed_tools=tuple(payload.get("subscribed_tools", [])),
        )

    def require_subscription(self, module_id: str) -> AuthDependency:
        """Return a dependency that requires a subscription to ``module_id``.

        Raises (at request time):
            HTTPException 403: If ``module_id`` is not in the user's
            ``subscribed_tools``.
        """

        def dependency(
            user: Annotated[AuthUser, Depends(self.require_auth)],
        ) -> AuthUser:
            if module_id not in user.subscribed_tools:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={"error": "subscription_required", "module": module_id},
                )
            return user

        return dependency

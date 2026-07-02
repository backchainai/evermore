"""FastAPI auth dependencies for route protection.

The auth logic lives in the shared ``evermore_auth`` package. This module wires
that package to petdata's own settings: a cached validator provider reads the
service's Supabase URL, and a single :class:`AuthDependencies` instance exposes
the ``require_auth``, ``require_admin``, and ``require_subscription`` route
guards other modules import.
"""

from __future__ import annotations

from functools import lru_cache

from evermore_auth import AuthDependencies, JwksValidator

from petdata.config import get_settings


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


# Resolve _get_validator by name at call time (not capture the function object)
# so tests patching this module's `_get_validator` are honored.
_deps = AuthDependencies(lambda: _get_validator())

require_auth = _deps.require_auth
require_admin = _deps.require_admin
require_subscription = _deps.require_subscription

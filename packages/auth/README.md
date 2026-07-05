# evermore-auth

Shared Supabase authentication and entitlement gating for the Evermore
services. One canonical copy of the JWT plumbing, consumed by every service that
protects routes:

- `evermore_auth.jwks` provides `JwksValidator`, which validates Supabase RS256
  (and ES256) tokens against the project JWKS endpoint.
- `evermore_auth.schemas` provides `AuthUser`, the frozen record built from a
  validated token (`sub`, `email`, `is_admin`, `subscribed_tools`).
- `evermore_auth.dependencies` provides `AuthDependencies`, a service-agnostic
  factory. Each service constructs one instance from its own settings (passing a
  `validator_provider` callable) and gets `require_auth`, `require_admin`, and
  `require_subscription(module_id)` FastAPI dependencies bound to that instance.

The end-to-end token flow and the subscription-entitlement policy this package
enforces are owned by [`docs/auth-flow.md`](../../docs/auth-flow.md) and
[`docs/subscriptions.md`](../../docs/subscriptions.md); this README covers only
the package's own API surface.

## Usage

```python
from evermore_auth import AuthDependencies, JwksValidator

def _get_validator() -> JwksValidator:
    return JwksValidator(f"{settings.supabase_url}/auth/v1/.well-known/jwks.json")

auth = AuthDependencies(_get_validator)
require_auth = auth.require_auth
require_admin = auth.require_admin
require_subscription = auth.require_subscription
```

## Deviations from repo defaults

Pinned to Python 3.13+, not the repo's 3.14 floor: it matches its current
consumer, `services/retriever`. ADR
[`0024-standardized-tech-stack.md`](../../docs/adr/0024-standardized-tech-stack.md)
already tracks retriever's move to 3.14 as outstanding work, not grandfathered.

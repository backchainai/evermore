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

The subscription gate reads the `subscribed_tools` JWT claim and returns a 403
(`{"error": "subscription_required", "module": module_id}`) when the requested
module is not present.

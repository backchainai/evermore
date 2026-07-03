# Subscriptions

Specification for Evermore's subscription model. Source of truth for the table schema, the entitlement check pattern, and the Stripe integration.

## Data model

Single Supabase Postgres table, owned by the platform (not by any module). The schema below is applied by the migration at `apps/stacker/supabase/migrations/20260702000000_subscriptions.sql`.

```sql
create table public.subscriptions (
  user_id                uuid          not null references auth.users(id) on delete cascade,
  module_id              text          not null,
  status                 text          not null check (status in (
                                          'active', 'trialing', 'past_due', 'canceled', 'incomplete'
                                        )),
  current_period_end     timestamptz,
  stripe_subscription_id text,
  created_at             timestamptz   not null default now(),
  updated_at             timestamptz   not null default now(),
  primary key (user_id, module_id)
);

create index subscriptions_user_id_idx on public.subscriptions (user_id);
create index subscriptions_stripe_sub_id_idx on public.subscriptions (stripe_subscription_id);
```

### Module IDs

Match the module's `id` field in `apps/stacker/src/lib/portal/config.ts`. Currently:

- `retriever`
- `petdata`

When adding a module, use its registry id verbatim.

### Active entitlement definition

A user is entitled to a module if a row exists with:

- `user_id = auth.uid()`
- `module_id = '<module>'`
- `status in ('active', 'trialing')`

`past_due`, `canceled`, and `incomplete` do NOT grant access.

## RLS policies

```sql
alter table public.subscriptions enable row level security;

-- Users can read their own subscriptions
create policy "users_read_own_subs"
  on public.subscriptions
  for select
  using (auth.uid() = user_id);

-- No INSERT/UPDATE/DELETE for authenticated role.
-- The Stripe webhook in stacker writes via service_role key, which bypasses RLS.
```

## Entitlement check — stacker (UI gate)

`stacker/src/routes/app/+layout.server.ts` queries the table on every authenticated portal request:

```typescript
const { data, error } = await locals.supabase
  .from('subscriptions')
  .select('module_id')
  .eq('user_id', session.user.id)
  .in('status', ['active', 'trialing']);

const subscriptions = data?.map((row) => row.module_id) ?? [];
```

The result feeds `SubscriptionGate.svelte`, which renders locked-state UI for any module the user lacks.

## Entitlement check — backend (defense in depth)

Each module backend MUST also enforce subscription, even though the UI already gates it. Without backend enforcement, a user could hit `https://retriever.example.com/api/v1/ask` directly with a valid JWT and bypass the portal.

The check is claim-based, not a DB query. Stacker's Stripe webhook keeps the `subscriptions` table current, and a Supabase auth hook projects the user's active module ids into a `subscribed_tools` claim on the JWT itself (per-request, at token-issue time, not per-request DB round-trip). The backend validates the JWT (JWKS) and reads `subscribed_tools` straight off the decoded payload: no DB read, no `service_role` key on the request path.

The shared `evermore_auth` package (`packages/auth/`) implements this once. `AuthDependencies.require_subscription(module_id)` returns a FastAPI dependency that chains off the same instance's `require_auth` (so the JWT decodes once per request, and 401 for missing/invalid tokens is still raised before 403 for a missing subscription) and raises 403 when `module_id` is absent from `subscribed_tools`:

```python
def require_subscription(self, module_id: str) -> AuthDependency:
    def dependency(
        user: Annotated[AuthUser, Depends(self.require_auth)],
    ) -> AuthUser:
        if module_id not in user.subscribed_tools:
            raise HTTPException(
                status_code=403,
                detail={"error": "subscription_required", "module": module_id},
            )
        return user

    return dependency
```

Each module wires it as a router-level dependency in `create_app()`, gating every route under the router in one place rather than annotating each endpoint individually. Retriever's wiring:

```python
from fastapi import Depends
from retriever.modules.auth import require_subscription

retriever_subscription = Depends(require_subscription("retriever"))

app.include_router(health_router)  # ungated: no /api/v1 prefix, liveness probe
app.include_router(messages_router, dependencies=[retriever_subscription])
app.include_router(documents_router, dependencies=[retriever_subscription])
app.include_router(rag_router, dependencies=[retriever_subscription])
```

Router-level `dependencies=[...]` do not add a documented response to the OpenAPI spec (there is no request body or response model attached to a dependency), so `openapi.json` is unaffected by this gate.

## Stripe integration

Stripe is the billing source of truth. A webhook in stacker upserts the subscriptions table on relevant events.

### Endpoint

`stacker/src/routes/api/webhooks/stripe/+server.ts` — public, authenticated by Stripe signature header.

### Handled events

| Stripe event | DB action |
|---|---|
| `customer.subscription.created` | Insert row(s), one per module on the subscription |
| `customer.subscription.updated` | Update `status`, `current_period_end` |
| `customer.subscription.deleted` | Update `status = 'canceled'` |
| `invoice.payment_failed` | Update `status = 'past_due'` |
| `invoice.payment_succeeded` | (no-op if subscription already active) |

### Mapping Stripe products to module IDs

Each Stripe Price object has `metadata.module_id` set to the Evermore module id. The webhook reads this metadata to determine which row(s) to write.

### Signature verification

```typescript
const sig = request.headers.get('stripe-signature');
const rawBody = await request.text(); // raw body required for signature verification
const event = await stripe.webhooks.constructEventAsync(
  rawBody,
  sig,
  STRIPE_WEBHOOK_SECRET,
  undefined,
  Stripe.createSubtleCryptoProvider()
);
```

The Cloudflare adapter runs on Web Crypto, so verification uses the async `constructEventAsync` with `Stripe.createSubtleCryptoProvider()`, and the raw request body is read with `await request.text()` (not `.json()`).

Reject with 400 on signature failure. Never process unverified payloads.

## Defense-in-depth rationale

| Layer | What it prevents |
|---|---|
| UI gate (stacker `+layout.server.ts`) | Honest user clicking a module they don't pay for |
| Backend gate (per-module FastAPI dep) | Direct API call bypassing the portal |
| RLS on subscriptions table | A compromised module/key reading other tenants' subscriptions |
| Stripe signature verification | Forged webhook events flipping entitlement state |

All four are required. Removing any one breaks the model.

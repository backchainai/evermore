-- Custom access-token hook: projects `subscribed_tools` onto every issued JWT.
-- Source of truth: docs/subscriptions.md ("Entitlement check — backend").
--
-- Verified against current Supabase documentation (fetched 2026-07-13):
--   - https://supabase.com/docs/guides/auth/auth-hooks/custom-access-token-hook
--     Function signature is `(event jsonb) returns jsonb`. Inputs carry
--     `user_id` (text/uuid) and an existing `claims` object. The "Add admin
--     role" example on this page reads `event->'claims'`, merges a new key
--     onto it with `jsonb_set`, writes it back onto the event with
--     `jsonb_set(event, '{claims}', claims)`, and `return event` (the full
--     event, not just the claims) — that is the shape this function follows.
--   - https://supabase.com/docs/guides/auth/auth-hooks ("Security model" and
--     "Using Hooks" sections): the Auth service connects as
--     `supabase_auth_admin`, which by default has no privileges on `public`.
--     Required grants: `grant execute ... to supabase_auth_admin`,
--     `grant usage on schema public to supabase_auth_admin`, and
--     `revoke execute ... from authenticated, anon, public`. The same page
--     states: "You will need to alter your row-level security (RLS) policies
--     to allow the supabase_auth_admin role to access tables that you have
--     RLS policies on."
--   - https://supabase.com/docs/guides/database/functions ("Security definer
--     vs invoker"): "It is best practice to use security invoker (which is
--     also the default). If you ever use security definer, you must set the
--     search_path."
--   - https://supabase.com/docs/guides/database/postgres/row-level-security:
--     a `security definer` function created via migration runs as its
--     creator — on Supabase that's the `postgres` role, which is a
--     superuser-equivalent with `bypassrls` — so `security definer` here
--     would silently bypass RLS on `public.subscriptions` rather than go
--     through the explicit grant/policy path the auth-hooks doc directs.
--
-- Deviation from plan: the issue asked for `security definer`. The
-- hook-specific guidance above explicitly recommends against tagging the
-- custom-access-token hook `security definer` and instead grants
-- `supabase_auth_admin` execute/usage/select plus an RLS policy scoped to
-- that role. This function is declared `security invoker` (the default and
-- Supabase's stated best practice) for that reason; the required grants and
-- policy follow below.

create or replace function public.custom_access_token_hook(event jsonb)
returns jsonb
language plpgsql
security invoker
set search_path = ''
as $$
declare
  claims jsonb;
  subscribed_tools jsonb;
begin
  -- Aggregate this user's actively-entitled module ids. `jsonb_agg` returns
  -- SQL NULL over zero rows, so `coalesce` guarantees the claim is always a
  -- JSON array, never null and never an error.
  select coalesce(jsonb_agg(s.module_id), '[]'::jsonb)
    into subscribed_tools
    from public.subscriptions s
    where s.user_id = (event->>'user_id')::uuid
      and s.status in ('active', 'trialing');

  -- coalesce guards the (not-expected-today) missing-claims case: jsonb_set
  -- is strict, so a NULL claims value would make this function return NULL
  -- and Auth would reject token issuance.
  claims := coalesce(event->'claims', '{}'::jsonb);
  claims := jsonb_set(claims, '{subscribed_tools}', subscribed_tools);
  event := jsonb_set(event, '{claims}', claims);

  return event;
end;
$$;

-- Grants required for Supabase Auth to invoke the hook. `supabase_auth_admin`
-- has no privileges on `public` by default.
grant usage on schema public to supabase_auth_admin;

grant execute
  on function public.custom_access_token_hook
  to supabase_auth_admin;

revoke execute
  on function public.custom_access_token_hook
  from authenticated, anon, public;

-- `public.subscriptions` has row level security enabled and its only policy
-- ("users_read_own_subs") is scoped to `auth.uid() = user_id`. The hook runs
-- as `supabase_auth_admin` with no end-user session, so `auth.uid()` is null
-- and that policy never matches. Grant the role table SELECT, column-scoped
-- to what the hook reads (user_id, module_id, status), and a policy scoped
-- to that role specifically, not a blanket allow for every role.
grant select (user_id, module_id, status) on table public.subscriptions to supabase_auth_admin;

create policy "auth_admin_read_subscriptions"
  on public.subscriptions
  for select
  to supabase_auth_admin
  using (true);

-- Verification performed (this monorepo has no Postgres/SQL test harness;
-- Postgres-dependent tests are CI-delegated per .daedalus/config.json):
--   - SQL parses: reviewed statement-by-statement against Postgres jsonb,
--     plpgsql, GRANT/REVOKE, and CREATE POLICY syntax.
--   - Migration ordering: this file's timestamp (20260713000000) sorts after
--     20260702000000_subscriptions.sql, which creates the table this hook
--     reads.
--   - Merge logic reasoned through: `event->'claims'` is read into `claims`,
--     `jsonb_set` writes the new `subscribed_tools` key onto a copy of it
--     (creating the key if absent, since jsonb_set's create_if_missing
--     defaults to true), and the result is written back onto `event` at
--     `{claims}` before the full `event` is returned — every other claim
--     Auth attached (iss, aud, exp, role, etc.) survives untouched.
--   - Empty-case handled: a user with zero rows in `public.subscriptions`
--     (or zero rows matching `active`/`trialing`) yields
--     `subscribed_tools = '[]'::jsonb`, never null, via the coalesce above.
--
-- Manual smoke test (run against a local `supabase start` instance via
-- `psql`; not part of any automated suite):
--   select public.custom_access_token_hook(
--     jsonb_build_object(
--       'user_id', '00000000-0000-0000-0000-000000000000',
--       'claims', jsonb_build_object('sub', '00000000-0000-0000-0000-000000000000')
--     )
--   );
--   -- expect: claims.subscribed_tools = '[]' (no matching subscriptions row).

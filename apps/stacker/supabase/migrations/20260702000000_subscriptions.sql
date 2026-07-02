-- Subscriptions table for Evermore's subscription model.
-- Source of truth: docs/subscriptions.md. Owned by the platform, not by any module.

create table if not exists public.subscriptions (
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

create index if not exists subscriptions_user_id_idx on public.subscriptions (user_id);
create index if not exists subscriptions_stripe_sub_id_idx on public.subscriptions (stripe_subscription_id);

alter table public.subscriptions enable row level security;

-- Users can read their own subscriptions
create policy "users_read_own_subs"
  on public.subscriptions
  for select
  using (auth.uid() = user_id);

-- No INSERT/UPDATE/DELETE policy for the authenticated role.
-- The Stripe webhook in stacker writes via the service_role key, which bypasses RLS.

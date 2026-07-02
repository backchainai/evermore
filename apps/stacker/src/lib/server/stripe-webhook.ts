// Stripe webhook processing for the subscriptions table.
//
// The raw request body must be the exact bytes returned by `request.text()`.
// stacker deploys on `@sveltejs/adapter-cloudflare`, whose Web Crypto backing
// requires the async `constructEventAsync` verification form (with
// `Stripe.createSubtleCryptoProvider()`), not the sync `constructEvent`.
import Stripe from 'stripe';
import { createClient, type SupabaseClient } from '@supabase/supabase-js';

type SubscriptionRow = {
	user_id: string;
	module_id: string;
	status: string;
	current_period_end: string | null;
	stripe_subscription_id: string;
};

const ALLOWED_STATUSES = new Set(['active', 'trialing', 'past_due', 'canceled', 'incomplete']);

// Map a Stripe subscription status onto the subscriptions.status check set.
// Unmapped Stripe states (incomplete_expired, unpaid, paused, ...) collapse to
// 'incomplete', the safest non-entitling value.
function mapStatus(status: string): string {
	return ALLOWED_STATUSES.has(status) ? status : 'incomplete';
}

// Build one row per subscription item that carries a module_id in price metadata.
function buildRows(subscription: Stripe.Subscription, userId: string, status: string): SubscriptionRow[] {
	const rows: SubscriptionRow[] = [];
	for (const item of subscription.items.data) {
		const moduleId = item.price?.metadata?.module_id;
		if (!moduleId) continue;
		const periodEndSeconds =
			item.current_period_end ?? (subscription as { current_period_end?: number }).current_period_end;
		const periodEnd = periodEndSeconds ? new Date(periodEndSeconds * 1000).toISOString() : null;
		rows.push({
			user_id: userId,
			module_id: moduleId,
			status,
			current_period_end: periodEnd,
			stripe_subscription_id: subscription.id
		});
	}
	return rows;
}

// Fresh service-role client. Not the SSR/cookie client: service_role bypasses
// RLS so the webhook can write public.subscriptions (which has no authenticated
// write policy). Never expose this key to the browser.
export function createStripeAdminClient(supabaseUrl: string, serviceKey: string): SupabaseClient {
	return createClient(supabaseUrl, serviceKey, {
		auth: { persistSession: false, autoRefreshToken: false }
	});
}

export async function processStripeWebhook(params: {
	rawBody: string;
	signature: string | null;
	webhookSecret: string;
	stripe: Stripe;
	admin: SupabaseClient;
	cryptoProvider?: Stripe.CryptoProvider;
}): Promise<Response> {
	const { rawBody, signature, webhookSecret, stripe, admin, cryptoProvider } = params;

	if (!signature) {
		return new Response('Missing signature', { status: 400 });
	}

	let event: Stripe.Event;
	try {
		event = await stripe.webhooks.constructEventAsync(
			rawBody,
			signature,
			webhookSecret,
			undefined,
			cryptoProvider
		);
	} catch {
		return new Response('Invalid signature', { status: 400 });
	}

	switch (event.type) {
		case 'customer.subscription.created':
		case 'customer.subscription.updated':
		case 'customer.subscription.deleted': {
			const subscription = event.data.object as Stripe.Subscription;
			// Stripe events carry a Stripe customer id, not a Supabase auth.users
			// uuid. The uuid is set on subscription/customer metadata at checkout
			// (checkout not yet built). Without it we cannot key the row, so ack
			// with 200 and skip the write rather than fail the webhook.
			const userId = subscription.metadata?.supabase_user_id;
			if (!userId) {
				console.warn('stripe webhook: subscription %s missing supabase_user_id', subscription.id);
				return new Response(null, { status: 200 });
			}
			const status =
				event.type === 'customer.subscription.deleted'
					? 'canceled'
					: mapStatus(subscription.status);
			const rows = buildRows(subscription, userId, status);
			if (rows.length > 0) {
				await admin.from('subscriptions').upsert(rows, { onConflict: 'user_id,module_id' });
			}
			return new Response(null, { status: 200 });
		}
		default:
			// Unhandled event types are acknowledged as no-ops.
			return new Response(null, { status: 200 });
	}
}

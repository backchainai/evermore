import type { RequestHandler } from './$types';
import Stripe from 'stripe';
import { PUBLIC_SUPABASE_URL } from '$env/static/public';
import { env } from '$env/dynamic/private';
import { createStripeAdminClient, processStripeWebhook } from '$lib/server/stripe-webhook';

// This endpoint only verifies webhook signatures and never calls the Stripe
// REST API, so no secret API key is needed. The placeholder keeps the env
// surface to the two documented secrets (STRIPE_WEBHOOK_SECRET,
// STRIPE_WEBHOOK_SUPABASE_SERVICE_KEY).
const stripe = new Stripe('webhook_no_api_calls');
const cryptoProvider = Stripe.createSubtleCryptoProvider();

export const POST: RequestHandler = async ({ request }) => {
	const rawBody = await request.text();
	const signature = request.headers.get('stripe-signature');
	const admin = createStripeAdminClient(
		PUBLIC_SUPABASE_URL,
		env.STRIPE_WEBHOOK_SUPABASE_SERVICE_KEY
	);
	return processStripeWebhook({
		rawBody,
		signature,
		webhookSecret: env.STRIPE_WEBHOOK_SECRET,
		stripe,
		admin,
		cryptoProvider
	});
};

import { describe, it, expect, vi } from 'vitest';
import Stripe from 'stripe';
import type { SupabaseClient } from '@supabase/supabase-js';
import { processStripeWebhook } from './stripe-webhook';

function makeAdmin() {
	const upsert = vi.fn(async (_rows: unknown, _opts?: unknown) => ({ error: null }));
	const admin = { from: vi.fn(() => ({ upsert })) } as unknown as SupabaseClient;
	return { admin, upsert };
}

const stripe = new Stripe('sk_test_dummy');
const secret = 'whsec_test';

function subEvent(type: string, status: string) {
	return JSON.stringify({
		id: 'evt_1',
		type,
		data: {
			object: {
				id: 'sub_123',
				status,
				metadata: { supabase_user_id: '00000000-0000-0000-0000-000000000001' },
				current_period_end: 1893456000,
				items: {
					data: [
						{ current_period_end: 1893456000, price: { metadata: { module_id: 'retriever' } } }
					]
				}
			}
		}
	});
}

describe('processStripeWebhook', () => {
	it('returns 400 and skips the write when the signature header is missing', async () => {
		const { admin, upsert } = makeAdmin();
		const res = await processStripeWebhook({
			rawBody: subEvent('customer.subscription.created', 'active'),
			signature: null,
			webhookSecret: secret,
			stripe,
			admin
		});

		expect(res.status).toBe(400);
		expect(upsert).not.toHaveBeenCalled();
	});

	it('returns 400 and skips the write when the signature does not verify', async () => {
		const { admin, upsert } = makeAdmin();
		const payload = subEvent('customer.subscription.created', 'active');
		const header = stripe.webhooks.generateTestHeaderString({
			payload,
			secret: 'whsec_wrong'
		});

		const res = await processStripeWebhook({
			rawBody: payload,
			signature: header,
			webhookSecret: secret,
			stripe,
			admin
		});

		expect(res.status).toBe(400);
		expect(upsert).not.toHaveBeenCalled();
	});

	it('upserts an active subscription row on customer.subscription.created', async () => {
		const { admin, upsert } = makeAdmin();
		const payload = subEvent('customer.subscription.created', 'active');
		const header = stripe.webhooks.generateTestHeaderString({ payload, secret });

		const res = await processStripeWebhook({
			rawBody: payload,
			signature: header,
			webhookSecret: secret,
			stripe,
			admin
		});

		expect(res.status).toBe(200);
		expect(upsert).toHaveBeenCalledTimes(1);
		const rows = upsert.mock.calls[0][0];
		const conflictTarget = upsert.mock.calls[0][1];
		expect(rows).toEqual([
			{
				user_id: '00000000-0000-0000-0000-000000000001',
				module_id: 'retriever',
				status: 'active',
				current_period_end: new Date(1893456000 * 1000).toISOString(),
				stripe_subscription_id: 'sub_123'
			}
		]);
		expect(conflictTarget).toEqual({ onConflict: 'user_id,module_id' });
	});

	it('upserts a canceled subscription row on customer.subscription.deleted', async () => {
		const { admin, upsert } = makeAdmin();
		const payload = subEvent('customer.subscription.deleted', 'canceled');
		const header = stripe.webhooks.generateTestHeaderString({ payload, secret });

		const res = await processStripeWebhook({
			rawBody: payload,
			signature: header,
			webhookSecret: secret,
			stripe,
			admin
		});

		expect(res.status).toBe(200);
		expect(upsert).toHaveBeenCalledTimes(1);
		const rows = upsert.mock.calls[0][0];
		expect(rows).toEqual([
			{
				user_id: '00000000-0000-0000-0000-000000000001',
				module_id: 'retriever',
				status: 'canceled',
				current_period_end: new Date(1893456000 * 1000).toISOString(),
				stripe_subscription_id: 'sub_123'
			}
		]);
	});

	it('skips the write and returns 200 when subscription metadata has no supabase_user_id', async () => {
		const { admin, upsert } = makeAdmin();
		const payload = JSON.stringify({
			id: 'evt_2',
			type: 'customer.subscription.updated',
			data: {
				object: {
					id: 'sub_456',
					status: 'active',
					metadata: {},
					current_period_end: 1893456000,
					items: {
						data: [
							{ current_period_end: 1893456000, price: { metadata: { module_id: 'retriever' } } }
						]
					}
				}
			}
		});
		const header = stripe.webhooks.generateTestHeaderString({ payload, secret });

		const res = await processStripeWebhook({
			rawBody: payload,
			signature: header,
			webhookSecret: secret,
			stripe,
			admin
		});

		expect(res.status).toBe(200);
		expect(upsert).not.toHaveBeenCalled();
	});
});

import { test, expect } from '@playwright/test';

test.describe('Security headers', () => {
	test('public route carries hardening headers and a Report-Only CSP', async ({ request }) => {
		const res = await request.get('/');
		const headers = res.headers();

		expect(headers['x-content-type-options']).toBe('nosniff');
		expect(headers['referrer-policy']).toBe('strict-origin-when-cross-origin');
		expect(headers['x-frame-options']).toBe('DENY');
		expect(headers['content-security-policy-report-only']).toBeTruthy();
		expect(headers['content-security-policy-report-only']).toContain("default-src 'self'");
	});
});

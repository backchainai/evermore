import { test, expect } from '@playwright/test';

test.describe('Favicon', () => {
	test('GET /favicon.png returns 200 image/png', async ({ request }) => {
		const res = await request.get('/favicon.png');
		expect(res.status()).toBe(200);
		expect(res.headers()['content-type']).toContain('image/png');
	});

	test('home page declares a reachable favicon', async ({ page }) => {
		await page.goto('/');
		const href = await page.locator('link[rel="icon"]').getAttribute('href');
		expect(href, 'app.html must declare a favicon').toBeTruthy();
		const res = await page.request.get(href!);
		expect(res.status()).toBe(200);
	});
});

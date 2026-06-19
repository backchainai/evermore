import { test, expect } from '@playwright/test';

test.describe('Admin page (unauthenticated)', () => {
	test('redirects to login', async ({ page }) => {
		await page.goto('/app/retriever/admin');
		await expect(page).toHaveURL(/\/login/);
	});
});

// Note: Admin page tests with authenticated users require Supabase auth mocking.
// The server-side guard in +page.server.ts checks locals.user.app_metadata.is_admin
// which requires a valid Supabase session cookie.

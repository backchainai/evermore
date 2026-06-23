import { test, expect } from '@playwright/test';

test.describe('Chat page (unauthenticated)', () => {
	test('redirects to login', async ({ page }) => {
		await page.goto('/app/retriever/chat');
		await expect(page).toHaveURL(/\/login/);
	});
});

// Note: Full chat interaction tests require Supabase auth mocking.
// These tests verify the redirect behavior works correctly for unauthenticated users.
// Integration tests with mocked API responses would be added when a test auth
// harness is set up (e.g., via Supabase test helpers or session cookie injection).

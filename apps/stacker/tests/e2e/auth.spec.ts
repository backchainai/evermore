import { test, expect } from '@playwright/test';

test.describe('Authentication', () => {
	test('unauthenticated user is redirected from /app/retriever/chat to /login', async ({ page }) => {
		await page.goto('/app/retriever/chat');
		await expect(page).toHaveURL(/\/login/);
	});

	test('unauthenticated user is redirected from /app/retriever/admin to /login', async ({ page }) => {
		await page.goto('/app/retriever/admin');
		await expect(page).toHaveURL(/\/login/);
	});

	test('unauthenticated user is redirected from /app to /login', async ({ page }) => {
		await page.goto('/app');
		await expect(page).toHaveURL(/\/login/);
	});

	test('login page renders form', async ({ page }) => {
		await page.goto('/login');
		await expect(page.getByRole('heading', { name: 'Sign In' })).toBeVisible();
		await expect(page.getByRole('textbox', { name: /email/i })).toBeVisible();
		await expect(page.getByText('Password')).toBeVisible();
		await expect(page.getByRole('button', { name: 'Sign In' })).toBeVisible();
	});

	test('login form blocks empty submission via native required validation', async ({ page }) => {
		await page.goto('/login');
		const submitButton = page.getByRole('button', { name: 'Sign In' });
		await submitButton.click();
		// Native HTML5 required validation blocks the POST, so the page stays on /login.
		await expect(page).toHaveURL(/\/login/);
		const emailInvalid = await page
			.getByRole('textbox', { name: /email/i })
			.evaluate((el) => (el as HTMLInputElement).validity.valueMissing);
		expect(emailInvalid).toBe(true);
	});

	test('login page offers an invite-acceptance affordance', async ({ page }) => {
		await page.goto('/login');
		await expect(page.getByText(/accounts are created by invitation/i)).toBeVisible();
		await expect(page.getByRole('link', { name: /accept an invitation/i })).toHaveAttribute(
			'href',
			'/invite/accept'
		);
	});

	test('invite accept page without a valid invite shows the expired state', async ({ page }) => {
		await page.goto('/invite/accept');
		await expect(page.getByRole('heading', { name: 'Accept Invitation' })).toBeVisible();
		await expect(page.getByText(/invitation link is invalid or has expired/i)).toBeVisible();
		await expect(page.getByRole('link', { name: 'Back to Sign In' })).toBeVisible();
	});
});

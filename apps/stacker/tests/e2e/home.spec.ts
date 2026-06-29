import { test, expect } from '@playwright/test';

test.describe('Home page', () => {
	test('shows sign in link when unauthenticated', async ({ page }) => {
		await page.goto('/');
		await expect(page.getByRole('link', { name: 'Sign In to Get Started' })).toBeVisible();
	});

	test('renders heading and tagline', async ({ page }) => {
		await page.goto('/');
		await expect(page.getByRole('heading', { name: 'Evermore' })).toBeVisible();
		await expect(page.getByText('AI tools for nonprofit animal shelters')).toBeVisible();
	});
});

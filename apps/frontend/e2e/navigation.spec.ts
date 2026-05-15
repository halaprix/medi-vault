import { test, expect } from '@playwright/test';

test('login page loads', async ({ page }) => {
  await page.goto('/login');
  await expect(page.locator('text=medi-vault')).toBeVisible();
});

test('upload page redirects to login when unauthenticated', async ({ page }) => {
  await page.goto('/upload');
  await expect(page).toHaveURL(/\/login/);
});

test('dashboard redirects to login when unauthenticated', async ({ page }) => {
  await page.goto('/dashboard');
  await expect(page).toHaveURL(/\/login/);
});

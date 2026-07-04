import { test, expect } from '@playwright/test';

test.describe('Authentication', () => {
  test('shows login page with form elements', async ({ page }) => {
    await page.goto('/login');
    await expect(page.locator('h1')).toContainText('1C Аналитик');
    await expect(page.locator('input[type="text"]')).toBeVisible();
    await expect(page.locator('input[type="password"]')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeVisible();
  });

  test('shows error on invalid credentials', async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[type="text"]', 'invalid');
    await page.fill('input[type="password"]', 'invalid');
    await page.click('button[type="submit"]');
    await page.waitForTimeout(2000);
    const currentUrl = page.url();
    expect(currentUrl.includes('/login')).toBeTruthy();
  });

  test('login page is accessible without auth', async ({ page }) => {
    const response = await page.goto('/login');
    expect(response?.status()).toBe(200);
  });
});

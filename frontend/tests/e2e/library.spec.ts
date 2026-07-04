import { test, expect } from '@playwright/test';

test.describe('Library', () => {
  test('renders library page', async ({ page }) => {
    await page.goto('/library');
    await expect(page.locator('h1')).toContainText('Библиотека');
  });

  test('has search input', async ({ page }) => {
    await page.goto('/library');
    await expect(page.locator('input[placeholder*="Поиск"]')).toBeVisible();
  });

  test('shows create button', async ({ page }) => {
    await page.goto('/library');
    await expect(page.locator('a[href*="dashboards"]').first()).toBeVisible();
  });

  test('can navigate to dashboard view', async ({ page }) => {
    await page.goto('/library');
    // If there are dashboard cards, click the first one
    const cards = page.locator('a[href*="/library/"]');
    const count = await cards.count();
    if (count > 0) {
      await cards.first().click();
      await page.waitForTimeout(1000);
      expect(page.url()).toContain('/library/');
    }
  });
});

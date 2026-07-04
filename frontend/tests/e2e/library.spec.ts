import { test, expect } from '@playwright/test';

test.describe('Library', () => {
  test('renders library page with title', async ({ page }) => {
    await page.goto('/library');
    await expect(page.locator('h1')).toContainText('Библиотека');
  });

  test('has search input', async ({ page }) => {
    await page.goto('/library');
    await expect(page.locator('input[placeholder*="Поиск"]')).toBeVisible();
  });

  test('has create button linking to dashboards', async ({ page }) => {
    await page.goto('/library');
    const createBtn = page.locator('a[href="/dashboards"]');
    await expect(createBtn).toBeVisible();
    await expect(createBtn).toContainText('Создать');
  });

  test('shows stats cards', async ({ page }) => {
    await page.goto('/library');
    const stats = page.locator('.grid.grid-cols-4 > div');
    const count = await stats.count();
    expect(count).toBeGreaterThanOrEqual(4);
  });

  test('has sort select', async ({ page }) => {
    await page.goto('/library');
    await expect(page.locator('select')).toBeVisible();
  });

  test('can navigate to dashboard view', async ({ page }) => {
    await page.goto('/library');
    const cards = page.locator('a[href*="/library/"]');
    const count = await cards.count();
    if (count > 0) {
      await cards.first().click();
      await page.waitForURL(/\/library\//);
      expect(page.url()).toContain('/library/');
    }
  });
});

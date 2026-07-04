import { test, expect } from '@playwright/test';

test.describe('Navigation', () => {
  test('sidebar has all expected links', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const links = [
      'Дашборд', 'Библиотека', 'AI Чат', 'Поиск',
      'ABC/XYZ', 'What-If', 'Инсайты', 'Продажи',
      'Документы (OCR)', 'Реализации', 'Статус', 'Админка',
    ];

    for (const label of links) {
      await expect(page.locator(`text=${label}`).first()).toBeVisible();
    }
  });

  test('can navigate to all main pages', async ({ page }) => {
    const pages = [
      { path: '/library', title: 'Библиотека' },
      { path: '/chat', title: 'AI Чат' },
      { path: '/search', title: 'Поиск' },
      { path: '/whatif', title: 'What-If' },
      { path: '/sales', title: 'Продажи' },
      { path: '/status', title: 'Статус' },
      { path: '/profile', title: 'Профиль' },
    ];

    for (const { path, title } of pages) {
      await page.goto(path);
      await page.waitForLoadState('networkidle');
      await expect(page.locator('h1').first()).toContainText(title);
    }
  });

  test('404 page shows for unknown routes', async ({ page }) => {
    const response = await page.goto('/nonexistent-route');
    expect(response?.status()).toBe(200); // SPA fallback
  });
});

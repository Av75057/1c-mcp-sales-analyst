import { test, expect } from '@playwright/test';

test.describe('AI Chat', () => {
  test('renders chat page', async ({ page }) => {
    await page.goto('/chat');
    await expect(page.locator('h1')).toContainText('AI Чат');
  });

  test('has input field', async ({ page }) => {
    await page.goto('/chat');
    await expect(page.locator('input[placeholder*="вопрос"]')).toBeVisible();
  });

  test('has session sidebar', async ({ page }) => {
    await page.goto('/chat');
    await expect(page.locator('text=Новый чат')).toBeVisible();
  });

  test('shows suggested queries', async ({ page }) => {
    await page.goto('/chat');
    const suggestions = page.locator('button:has-text("продажи")');
    await expect(suggestions.first()).toBeVisible();
  });
});

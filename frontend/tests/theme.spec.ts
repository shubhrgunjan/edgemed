import { test, expect } from '@playwright/test';
import path from 'node:path';

test.skip(!process.env.EDGEMED_THEME_URL, 'Run against the built local interface.');

test('local interface supports Latte and Mocha and remembers the switch', async ({ page }) => {
  await page.goto(process.env.EDGEMED_THEME_URL!);
  await page.evaluate(() => localStorage.setItem('edgemed-theme', 'latte'));
  await page.reload();
  await expect(page.getByRole('heading', { name: 'Keep working. Even offline.' })).toBeVisible();
  const toggle = page.getByRole('switch', { name: /Theme:/ });
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'latte');
  await expect(toggle).toHaveAttribute('aria-checked', 'false');
  await page.screenshot({ path: path.resolve(process.cwd(), '../test-results/login-latte.png'), fullPage: true });
  await toggle.click();
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'mocha');
  await expect(toggle).toHaveAttribute('aria-checked', 'true');
  await page.screenshot({ path: path.resolve(process.cwd(), '../test-results/login-mocha.png'), fullPage: true });
  await page.reload();
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'mocha');
  expect(await page.evaluate(() => Object.keys(localStorage))).toEqual(['edgemed-theme']);
});

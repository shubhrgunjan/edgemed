import { test, expect } from '@playwright/test';
import path from 'node:path';

test.skip(!process.env.EDGEMED_PUBLIC_DEMO_URL, 'Run against the static public demo URL.');

test('public sample uses only local assets, keeps notes ephemeral, and switches themes', async ({ page }) => {
  const requests: string[] = [];
  const errors: string[] = [];
  page.on('request', request => requests.push(request.url()));
  page.on('pageerror', error => errors.push(error.message));
  await page.goto(process.env.EDGEMED_PUBLIC_DEMO_URL!);
  await expect(page.getByRole('heading', { name: 'Memory that stays close to care.' })).toBeVisible();
  await expect(page.getByText('PUBLIC SYNTHETIC DEMO')).toBeVisible();
  await page.evaluate(() => localStorage.setItem('edgemed-theme', 'latte'));
  await page.reload();

  const toggle = page.getByRole('switch', { name: /Theme:/ });
  await expect(toggle).toHaveAttribute('aria-checked', 'false');
  await toggle.click();
  await expect(toggle).toHaveAttribute('aria-checked', 'true');
  const flavor = await page.locator('html').getAttribute('data-theme');
  await page.reload();
  await expect(page.locator('html')).toHaveAttribute('data-theme', flavor!);

  await page.getByRole('button', { name: 'Add note' }).click();
  await page.getByRole('dialog', { name: 'Add synthetic note' }).getByLabel('Title').fill('Invented demo note');
  await page.getByRole('dialog', { name: 'Add synthetic note' }).getByRole('textbox', { name: 'Note', exact: true }).fill('<script>window.demoLeak=true</script> invented example');
  await page.getByRole('button', { name: 'Save in this tab' }).click();
  await expect(page.getByText('Invented demo note', { exact: true })).toBeVisible();
  await page.getByRole('textbox', { name: 'Search synthetic notes' }).fill('invented');
  await page.getByRole('button', { name: 'Search', exact: true }).click();
  await expect(page.getByText('1 keyword matches')).toBeVisible();
  await page.getByText('Invented demo note', { exact: true }).click();
  await expect(page.getByRole('dialog', { name: 'Synthetic note detail' })).toContainText('<script>');
  expect(await page.evaluate(() => Object.hasOwn(window, 'demoLeak'))).toBe(false);
  await page.getByRole('button', { name: 'Remove from this tab' }).click();
  await expect(page.getByText('Invented demo note', { exact: true })).toHaveCount(0);
  await page.getByRole('button', { name: 'Clear search' }).click();
  await page.screenshot({ path: path.resolve(process.cwd(), '../test-results/public-demo-desktop.png'), fullPage: true });
  await page.setViewportSize({ width: 390, height: 844 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.screenshot({ path: path.resolve(process.cwd(), '../test-results/public-demo-mobile.png'), fullPage: true });
  await page.setViewportSize({ width: 320, height: 700 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.reload();
  await expect(page.getByText('Invented demo note', { exact: true })).toHaveCount(0);
  expect(await page.evaluate(() => Object.keys(localStorage))).toEqual(['edgemed-theme']);
  expect(requests.every(url => url.startsWith(new URL(page.url()).origin + '/') && !url.includes('/api/'))).toBe(true);
  expect(errors).toEqual([]);
});

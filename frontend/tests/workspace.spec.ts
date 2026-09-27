import { test, expect } from '@playwright/test';
import { execFileSync } from 'node:child_process';
import path from 'node:path';

const root = path.resolve(process.cwd(), '..');
function password() { return execFileSync(path.join(root, '.venv/bin/python'), ['-c', 'from edgemed.security import load_secret; print(load_secret("edge-a")["initial_password"])'], { cwd: root, encoding: 'utf8' }).trim(); }
async function signIn(page: import('@playwright/test').Page) {
  await page.goto('/');
  await page.getByLabel('Password', { exact: true }).fill(password());
  await page.getByRole('button', { name: 'Sign in locally' }).click();
  await expect(page.getByRole('heading', { name: 'Memory explorer', exact: true })).toBeVisible();
}

test('capture, search, inspect, delete and truthful sharing', async ({ page }) => {
  const errors: string[] = []; page.on('pageerror', e => errors.push(e.message));
  await signIn(page);
  await page.getByRole('button', { name: 'Load examples' }).click();
  await expect(page.getByText('Persistent cough and fever', { exact: true })).toBeVisible();
  await page.getByRole('textbox', { name: 'Search memory' }).fill('high temperature and coughing');
  await page.getByRole('button', { name: 'Search', exact: true }).click();
  await expect(page.getByText(/ms backend/)).toBeVisible();
  await page.getByText('Persistent cough and fever', { exact: true }).click();
  await expect(page.getByRole('dialog', { name: 'Memory inspector' })).toBeVisible();
  await expect(page.getByText('Shared in workspace', { exact: true })).toBeVisible();
  await page.keyboard.press('Escape');
  await page.getByRole('button', { name: 'Add observation', exact: true }).click();
  await page.getByLabel('Title', { exact: true }).fill('Browser verification observation');
  await page.getByLabel('Observation', { exact: true }).fill('<script>window.privateLeak=true</script> Synthetic observation.');
  await page.getByRole('button', { name: 'Save locally' }).click();
  await expect(page.getByText('Browser verification observation', { exact: true })).toBeVisible();
  await page.getByText('Browser verification observation', { exact: true }).click();
  await expect(page.locator('.note-content')).toContainText('<script>');
  expect(await page.evaluate(() => Object.hasOwn(window, 'privateLeak'))).toBe(false);
  await page.getByText('Archive / deletion').click();
  await page.getByRole('button', { name: 'Remove from active memory' }).click();
  await expect(page.getByRole('dialog')).toHaveCount(0);
  await page.screenshot({ path: path.join(root, 'test-results/desktop-next.png'), fullPage: true });
  await page.getByRole('button', { name: 'Sharing & activity', exact: true }).click();
  await expect(page.getByText('Central acceptance does not confirm receipt on another device.', { exact: false })).toBeVisible();
  await page.screenshot({ path: path.join(root, 'test-results/sharing-next.png'), fullPage: true });
  await page.getByRole('button', { name: 'Sign out', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Unlock your workspace' })).toBeVisible();
  expect(errors).toEqual([]);
});

test('mobile and keyboard dialog focus stay usable', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await signIn(page);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.getByRole('button', { name: 'Add observation', exact: true }).click();
  const close = page.getByRole('button', { name: 'Close Add observation' });
  await expect(close).toBeFocused();
  await page.keyboard.press('Shift+Tab');
  await expect(page.getByRole('button', { name: 'Save locally' })).toBeFocused();
  await page.keyboard.press('Escape');
  await expect(page.getByRole('button', { name: 'Add observation', exact: true })).toBeFocused();
  await page.screenshot({ path: path.join(root, 'test-results/mobile-next.png'), fullPage: true });
});

test('late search after sign-out cannot restore query or private results', async ({ page }) => {
  await signIn(page);
  let release!: () => void;
  const held = new Promise<void>(resolve => { release = resolve; });
  await page.route('**/api/search', async route => {
    await held;
    await route.fulfill({ json: { results: [{ id: 'private', title: 'STALE_PRIVATE_RESPONSE' }], elapsed_ms: 1 } }).catch(() => {});
  });
  await page.getByRole('textbox', { name: 'Search memory' }).fill('PRIVATE_QUERY_CANARY');
  const pending = page.waitForRequest('**/api/search');
  await page.getByRole('button', { name: 'Search', exact: true }).click();
  await pending;
  await page.getByRole('button', { name: 'Sign out', exact: true }).click();
  release();
  await expect(page.getByRole('heading', { name: 'Unlock your workspace' })).toBeVisible();
  await page.getByLabel('Password', { exact: true }).fill(password());
  await page.getByRole('button', { name: 'Sign in locally' }).click();
  await expect(page.getByRole('textbox', { name: 'Search memory' })).toHaveValue('');
  await expect(page.getByText('STALE_PRIVATE_RESPONSE')).toHaveCount(0);
});

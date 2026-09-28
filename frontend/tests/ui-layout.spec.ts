import { test, expect } from '@playwright/test';
import path from 'node:path';

test.skip(!process.env.EDGEMED_UI_REVIEW_URL, 'Run against the built frontend for visual review.');

const notes = [
  { id: 'one', title: 'Persistent cough and fever', content: 'Synthetic subject reports a persistent cough.', subject: 'SYN-001', category: 'OBSERVATION', privacy: 'SENSITIVE', release: 'LOCAL', heads: ['r1'], fixture: null, conflicting: false, index_state: 'indexed', created: 1 },
  { id: 'two', title: 'Penicillin allergy reported', content: 'Synthetic subject reports a rash.', subject: 'SYN-002', category: 'ALLERGY', privacy: 'HIGHLY_SENSITIVE', release: 'LOCAL', heads: ['r2'], fixture: null, conflicting: false, index_state: 'indexed', created: 2 },
  { id: 'three', title: 'Reviewed handoff checklist', content: 'Approved synthetic reference for local search.', subject: null, category: 'NOTE', privacy: 'SENSITIVE', release: 'APPROVED', heads: ['r3'], fixture: 'checklist', conflicting: false, index_state: 'indexed', created: 3 },
];

test('app layout remains usable across themes, views, and widths', async ({ page }) => {
  let visibleNotes = notes;
  let generation = 1;
  const errors: string[] = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.route('**/api/**', route => {
    const url = new URL(route.request().url());
    const pathname = url.pathname;
    let body: unknown = {};
    if (pathname === '/api/session') body = { csrf: 'synthetic-token', role: 'admin', username: 'operator' };
    else if (pathname === '/api/status') body = { generation, deployment: 'local', workspace: 'Synthetic workspace', role: 'admin', device: 'edge-a', total: visibleNotes.length, local_only: visibleNotes.length, conflicts: visibleNotes.filter(note => note.conflicting).length, indexed: visibleNotes.length, vault: true, worker_error: null };
    else if (pathname === '/api/sync/status') body = { enabled: false, connection: 'paused', error: null, counts: { pending: 0, retry_wait: 0, failed: 0, acknowledged: 0 }, items: [] };
    else if (pathname === '/api/memories') body = url.searchParams.get('conflicts') === 'true' ? visibleNotes.filter(note => note.conflicting) : visibleNotes;
    else if (pathname === '/api/activity') body = [{ action: 'synthetic_reference_reviewed', time: 1770000000, device: 'edge-a' }];
    else if (pathname === '/api/search') body = { results: visibleNotes.slice(0, 1), elapsed_ms: 12 };
    else if (pathname.startsWith('/api/memories/')) {
      const note = visibleNotes.find(entry => entry.id === pathname.split('/').at(-1)) ?? notes[0];
      body = { ...note, revisions: note.heads.map((id, index) => ({ id, content: index ? 'Alternate synthetic branch.' : note.content, created: index + 1, parents: [], variant: 0, device: index ? 'edge-b' : 'edge-a' })), reason: 'Visible in this synthetic workspace.' };
    }
    return route.fulfill({ json: body });
  });
  await page.goto(process.env.EDGEMED_UI_REVIEW_URL!);
  await expect(page.getByRole('heading', { name: 'Memory explorer' })).toBeVisible();
  await expect(page.getByText('Persistent cough and fever')).toBeVisible();
  await page.evaluate(() => localStorage.setItem('edgemed-theme', 'latte'));
  await page.reload();
  await expect(page.getByRole('heading', { name: 'Memory explorer' })).toBeVisible();
  await page.screenshot({ path: path.resolve(process.cwd(), '../test-results/ui-memory-latte-wide.png'), fullPage: true });
  await page.getByRole('switch', { name: /Theme:/ }).click();
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'mocha');
  await page.waitForTimeout(200);
  await page.screenshot({ path: path.resolve(process.cwd(), '../test-results/ui-memory-mocha-wide.png'), fullPage: true });
  await page.getByRole('textbox', { name: 'Search memory' }).focus();
  await page.screenshot({ path: path.resolve(process.cwd(), '../test-results/ui-search-focus.png'), fullPage: true });
  await page.getByRole('button', { name: 'Add observation', exact: true }).click();
  await expect(page.getByRole('dialog', { name: 'Add observation' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Close Add observation' })).toBeFocused();
  await page.screenshot({ path: path.resolve(process.cwd(), '../test-results/ui-dialog-mocha.png'), fullPage: true });
  await page.keyboard.press('Escape');
  await expect(page.getByRole('button', { name: 'Add observation', exact: true })).toBeFocused();
  await page.getByText('Persistent cough and fever', { exact: true }).click();
  await expect(page.getByRole('dialog', { name: 'Memory inspector' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Close Memory inspector' })).toBeFocused();
  await page.keyboard.press('Shift+Tab');
  await expect(page.getByText('Archive / deletion')).toBeFocused();
  await page.screenshot({ path: path.resolve(process.cwd(), '../test-results/ui-inspector-mocha.png'), fullPage: true });
  await page.keyboard.press('Escape');
  await page.getByRole('button', { name: 'Sharing & activity', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Activity history' })).toBeVisible();
  await page.screenshot({ path: path.resolve(process.cwd(), '../test-results/ui-sharing-mocha.png'), fullPage: true });
  await page.getByRole('navigation', { name: 'Primary' }).getByRole('button', { name: /^Needs review/ }).click();
  await expect(page.getByText('No conflicts to review')).toBeVisible();
  await page.screenshot({ path: path.resolve(process.cwd(), '../test-results/ui-review-empty.png'), fullPage: true });
  visibleNotes = [{ ...notes[0], conflicting: true, heads: ['r1', 'r2'] }];
  generation = 2;
  await page.reload();
  await expect(page.getByRole('heading', { name: 'Memory explorer' })).toBeVisible();
  await page.getByRole('navigation', { name: 'Primary' }).getByRole('button', { name: /^Needs review/ }).click();
  await expect(page.getByText('Persistent cough and fever', { exact: true })).toBeVisible();
  await page.getByText('Persistent cough and fever', { exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Compare current branches' })).toBeVisible();
  await page.screenshot({ path: path.resolve(process.cwd(), '../test-results/ui-conflict-dialog.png'), fullPage: true });
  await page.keyboard.press('Escape');
  visibleNotes = notes;
  generation = 3;
  await page.reload();
  await expect(page.getByRole('heading', { name: 'Memory explorer' })).toBeVisible();
  await page.getByRole('navigation', { name: 'Primary' }).getByRole('button', { name: /^Needs review/ }).click();
  await page.setViewportSize({ width: 1100, height: 850 });
  await page.screenshot({ path: path.resolve(process.cwd(), '../test-results/ui-narrow.png'), fullPage: true });
  await page.setViewportSize({ width: 900, height: 850 });
  await page.screenshot({ path: path.resolve(process.cwd(), '../test-results/ui-tablet.png'), fullPage: true });
  await page.setViewportSize({ width: 390, height: 844 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.screenshot({ path: path.resolve(process.cwd(), '../test-results/ui-mobile.png'), fullPage: true });
  await page.getByRole('button', { name: 'Open navigation' }).click();
  await page.waitForTimeout(200);
  await expect(page.getByRole('navigation', { name: 'Primary' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Close navigation' }).last()).toBeFocused();
  await page.screenshot({ path: path.resolve(process.cwd(), '../test-results/ui-mobile-menu.png'), fullPage: true });
  await page.getByRole('button', { name: 'Memory', exact: true }).click();
  await page.waitForTimeout(200);
  await expect(page.getByText('Synthetic data')).toBeVisible();
  await page.screenshot({ path: path.resolve(process.cwd(), '../test-results/ui-mobile-populated.png'), fullPage: true });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  visibleNotes = [];
  generation = 2;
  await page.reload();
  await expect(page.getByText('No observations yet')).toBeVisible();
  await page.screenshot({ path: path.resolve(process.cwd(), '../test-results/ui-mobile-empty.png'), fullPage: true });
  await page.setViewportSize({ width: 320, height: 700 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  expect(errors).toEqual([]);
});

test('login stays legible and within the mobile viewport in both themes', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto(process.env.EDGEMED_UI_REVIEW_URL!);
  await expect(page.getByRole('heading', { name: 'Unlock your workspace' })).toBeVisible();
  await page.evaluate(() => localStorage.setItem('edgemed-theme', 'latte'));
  await page.reload();
  await expect(page.getByRole('heading', { name: 'Unlock your workspace' })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.screenshot({ path: path.resolve(process.cwd(), '../test-results/ui-login-mobile-latte.png'), fullPage: true });
  await page.getByRole('switch', { name: /Theme:/ }).click();
  await page.waitForTimeout(200);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.screenshot({ path: path.resolve(process.cwd(), '../test-results/ui-login-mobile-mocha.png'), fullPage: true });
});

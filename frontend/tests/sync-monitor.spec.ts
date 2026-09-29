import { test, expect } from '@playwright/test';

test.skip(!process.env.EDGEMED_UI_REVIEW_URL, 'Run against the built frontend for visual review.');

// Mock sync state with items in various states
const mockSync = {
  enabled: true,
  connection: 'connected',
  error: null,
  last_sync: Math.floor(Date.now() / 1000) - 120,
  counts: { pending: 2, in_flight: 0, acknowledged: 5, retry_wait: 1, failed: 1, cancelled: 0 },
  items: [
    { id: 'op-aaa-111-pending-one', state: 'pending', attempts: 0, error: null },
    { id: 'op-bbb-222-retry-two', state: 'retry_wait', attempts: 3, error: 'Connection timeout' },
    { id: 'op-ccc-333-acked-three', state: 'acknowledged', attempts: 1, error: null },
    { id: 'op-ddd-444-acked-four', state: 'acknowledged', attempts: 1, error: null },
    { id: 'op-eee-555-failed-five', state: 'failed', attempts: 5, error: 'Schema validation rejected' },
    { id: 'op-fff-666-acked-six', state: 'acknowledged', attempts: 2, error: null },
    { id: 'op-ggg-777-acked-seven', state: 'acknowledged', attempts: 1, error: null },
    { id: 'op-hhh-888-acked-eight', state: 'acknowledged', attempts: 1, error: null },
    { id: 'op-iii-999-pending-nine', state: 'pending', attempts: 0, error: null },
  ],
};

const mockStatus = {
  generation: 1,
  deployment: 'local',
  workspace: 'Synthetic clinical workspace',
  role: 'admin',
  device: 'edge-a',
  total: 12,
  local_only: 9,
  conflicts: 1,
  indexed: 11,
  vault: true,
  worker_error: null,
  database: 'SQLCipher',
  engine: 'Qdrant Edge',
  model: 'bge-small-en-v1.5',
};

const mockEvents = [
  { action: 'memory_created', time: Math.floor(Date.now() / 1000) - 3600, device: 'edge-a' },
  { action: 'memory_indexed', time: Math.floor(Date.now() / 1000) - 3500, device: 'edge-a' },
  { action: 'sync_triggered', time: Math.floor(Date.now() / 1000) - 1800, device: 'edge-a' },
  { action: 'reference_snapshot_refreshed', time: Math.floor(Date.now() / 1000) - 900, device: 'edge-a' },
  { action: 'memory_archived', time: Math.floor(Date.now() / 1000) - 300, device: 'edge-a' },
];

/**
 * Helper: Sets up the route handler. Because the mock /api/session
 * immediately returns a valid user, the app auto-logs in — no login form appears.
 */
async function setupRoutes(
  page: import('@playwright/test').Page,
  overrides: { sync?: Partial<typeof mockSync>; status?: Partial<typeof mockStatus> } = {},
) {
  let syncEnabled = overrides.sync?.enabled ?? true;
  const syncPayload = { ...mockSync, ...overrides.sync };
  const statusPayload = { ...mockStatus, ...overrides.status };

  await page.route('**/api/**', route => {
    const url = new URL(route.request().url());
    const pathname = url.pathname;
    const method = route.request().method();
    let body: unknown = {};

    if (pathname === '/api/session') {
      body = { csrf: 'synthetic-token', role: 'admin', username: 'operator' };
    } else if (pathname === '/api/status') {
      body = statusPayload;
    } else if (pathname === '/api/sync/status') {
      body = { ...syncPayload, enabled: syncEnabled };
    } else if (pathname === '/api/memories') {
      body = [];
    } else if (pathname === '/api/activity') {
      body = mockEvents;
    } else if (pathname === '/api/sync/transport' && method === 'POST') {
      syncEnabled = !syncEnabled;
      body = { ok: true };
    } else if (pathname === '/api/sync' && method === 'POST') {
      body = { ok: true };
    } else if (pathname === '/api/sync/reference-snapshot' && method === 'POST') {
      body = { ok: true };
    } else if (pathname === '/api/session/activity' && method === 'POST') {
      body = { ok: true };
    } else {
      body = {};
    }

    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(body) });
  });
}

test('Sync Monitor & Memory Lab workspace behaves truthfully and responsively', async ({ page }) => {
  const errors: string[] = [];
  page.on('pageerror', err => errors.push(err.message));

  await setupRoutes(page);
  await page.goto(process.env.EDGEMED_UI_REVIEW_URL!);

  // Wait for the app to be ready (mock session auto-logs in)
  const nav = page.getByRole('navigation', { name: 'Primary' });
  await expect(nav.getByRole('button', { name: /Sync monitor/i })).toBeVisible();

  // ── Navigate to Sync monitor ──────────────────────────────────────────────
  await nav.getByRole('button', { name: /Sync monitor/i }).click();
  await expect(page.getByRole('heading', { name: /Sync monitor/i })).toBeVisible();
  await expect(page.getByText(/Outbound queue, delivery receipts/i)).toBeVisible();

  // ── Connectivity hero ─────────────────────────────────────────────────────
  await expect(page.getByRole('heading', { name: 'Shared service connected' })).toBeVisible();
  await expect(page.getByText(/Last verified contact/i)).toBeVisible();

  // ── Stat cards ───────────────────────────────────────────────────────────
  await expect(page.getByText('Waiting / retrying')).toBeVisible();
  await expect(page.locator('.sm-stat-label', { hasText: 'Accepted centrally' })).toBeVisible();
  await expect(page.getByText('Private (local only)')).toBeVisible();
  await expect(page.locator('.sm-stat-card', { hasText: 'Private (local only)' }).locator('.sm-stat-value')).toHaveText('9');

  // ── Queue tab (default) ───────────────────────────────────────────────────
  await expect(page.getByText('Outbound queue', { exact: true }).first()).toBeVisible();
  await expect(page.getByText('Approved synthetic reference update').first()).toBeVisible();

  // ── Queue filter chips ────────────────────────────────────────────────────
  await page.getByRole('button', { name: /^Failed/ }).click();
  await expect(page.getByText('Schema validation rejected')).toBeVisible();

  await page.getByRole('button', { name: /^All/ }).click();
  await expect(page.getByText('Approved synthetic reference update').first()).toBeVisible();

  // ── Expand a queue item ───────────────────────────────────────────────────
  const firstItem = page.locator('.sm-queue-row').first();
  await firstItem.click();
  await expect(page.getByText('Operation ID')).toBeVisible();
  await expect(page.getByText(/Private observations never enter this queue/i)).toBeVisible();

  // ── Activity tab ──────────────────────────────────────────────────────────
  await page.getByRole('tab', { name: /Activity/i }).click();
  await expect(page.getByText('memory created')).toBeVisible();
  await expect(page.getByText('sync triggered')).toBeVisible();

  // Activity filter search
  const filterInput = page.getByPlaceholder('Filter events…');
  await filterInput.fill('sync');
  await expect(page.getByText('sync triggered')).toBeVisible();
  // 'memory created' should be filtered out
  expect(await page.getByText('memory created').count()).toBe(0);
  await filterInput.fill('');

  // ── Storage & index tab ───────────────────────────────────────────────────
  await page.getByRole('tab', { name: /Storage/i }).click();
  const storageGrid = page.locator('.sm-storage-grid');
  await expect(storageGrid.getByText('Encrypted vault')).toBeVisible();
  await expect(storageGrid.getByText('Verified at startup')).toBeVisible();
  await expect(storageGrid.getByText('Qdrant Edge')).toBeVisible();
  await expect(page.locator('.sm-index-bar')).toBeVisible();
  await expect(page.getByText('11/12 indexed')).toBeVisible();

  // ── Memory Lab tab (admin only) ───────────────────────────────────────────
  await page.getByRole('tab', { name: /Memory Lab/i }).click();
  await expect(page.getByRole('heading', { name: 'Memory Lab', exact: true })).toBeVisible();
  await expect(page.getByText('Synthetic-only simulation controls')).toBeVisible();

  // Expand a lab step
  await page.getByRole('button', { name: /Transport enabled/i }).click();
  await expect(page.getByText(/Sharing is currently/i)).toBeVisible();

  // Expand policy invariants step
  await page.getByRole('button', { name: /Policy invariants/i }).click();
  await expect(page.getByText(/hard system invariant/i)).toBeVisible();

  // ── Privacy policy disclaimer ─────────────────────────────────────────────
  await page.getByRole('tab', { name: /Outbound queue/i }).click();
  await expect(page.getByText(/Private observations never appear here/i)).toBeVisible();

  // ── Sync controls visible ─────────────────────────────────────────────────
  await expect(page.getByRole('button', { name: /Pause sharing/i }).first()).toBeVisible();
  await expect(page.getByRole('button', { name: /Sync now/i }).first()).toBeVisible();

  // ── No JavaScript errors ──────────────────────────────────────────────────
  expect(errors).toHaveLength(0);
});

test('Sync Monitor shows correct state when offline / sharing paused', async ({ page }) => {
  const errors: string[] = [];
  page.on('pageerror', err => errors.push(err.message));

  await page.route('**/api/**', route => {
    const url = new URL(route.request().url());
    const pathname = url.pathname;
    let body: unknown = {};

    if (pathname === '/api/session') {
      body = { csrf: 'synthetic-token', role: 'admin', username: 'operator' };
    } else if (pathname === '/api/status') {
      body = { ...mockStatus, total: 0, indexed: 0, conflicts: 0 };
    } else if (pathname === '/api/sync/status') {
      body = {
        enabled: false,
        connection: 'unavailable',
        error: 'Cannot reach central service. Check network settings.',
        last_sync: undefined,
        counts: { pending: 0, in_flight: 0, acknowledged: 0, retry_wait: 0, failed: 0, cancelled: 0 },
        items: [],
      };
    } else if (pathname === '/api/memories') {
      body = [];
    } else if (pathname === '/api/activity') {
      body = [];
    } else if (pathname === '/api/session/activity') {
      body = { ok: true };
    } else {
      body = {};
    }

    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(body) });
  });

  await page.goto(process.env.EDGEMED_UI_REVIEW_URL!);
  const nav = page.getByRole('navigation', { name: 'Primary' });
  await expect(nav.getByRole('button', { name: /Sync monitor/i })).toBeVisible();
  await nav.getByRole('button', { name: /Sync monitor/i }).click();

  // Connection shows unavailable
  await expect(page.getByRole('heading', { name: 'Shared service unavailable' })).toBeVisible();
  // Error message displayed
  await expect(page.getByText('Cannot reach central service')).toBeVisible();
  // Enable sharing button visible (not pause)
  await expect(page.getByRole('button', { name: /Enable sharing/i }).first()).toBeVisible();
  // Sync now is disabled when not enabled
  await expect(page.getByRole('button', { name: /Sync now/i }).first()).toBeDisabled();

  // Queue shows empty state
  await expect(page.getByText('No items in this view')).toBeVisible();
  await expect(page.getByText(/Private observations never enter this queue/i)).toBeVisible();

  // Storage with 0 records shows 0% index
  await page.getByRole('tab', { name: /Storage/i }).click();
  await expect(page.getByText('0/0 indexed')).toBeVisible();

  expect(errors).toHaveLength(0);
});

test('Sync Monitor nav badge shows pending count', async ({ page }) => {
  page.on('pageerror', err => { throw new Error(err.message); });

  await setupRoutes(page);
  await page.goto(process.env.EDGEMED_UI_REVIEW_URL!);

  const nav = page.getByRole('navigation', { name: 'Primary' });
  const syncNavButton = nav.getByRole('button', { name: /Sync monitor/i });
  await expect(syncNavButton).toBeVisible();

  // Nav badge should show pending count (2 pending + 1 retry_wait = 3)
  await expect(syncNavButton.locator('.count')).toHaveText('3');
});

test('Sync Monitor is responsive on mobile viewport', async ({ page }) => {
  page.on('pageerror', err => { throw new Error(err.message); });

  await page.setViewportSize({ width: 390, height: 844 });
  await setupRoutes(page);
  await page.goto(process.env.EDGEMED_UI_REVIEW_URL!);

  // Open mobile menu to access navigation
  await page.getByRole('button', { name: 'Open navigation' }).click();
  await page.getByRole('button', { name: /Sync monitor/i }).click();

  await expect(page.getByRole('heading', { name: 'Shared service connected' })).toBeVisible();

  // Stat cards should still be visible (2-col layout on mobile)
  await expect(page.getByText('Waiting / retrying')).toBeVisible();
  await expect(page.locator('.sm-stat-label', { hasText: 'Accepted centrally' })).toBeVisible();

  // Tabs should be scrollable and usable
  await expect(page.locator('.sm-tabs')).toBeVisible();
  await page.getByRole('tab', { name: /Activity/i }).click();
  await expect(page.locator('.sm-activity-panel')).toBeVisible();
});

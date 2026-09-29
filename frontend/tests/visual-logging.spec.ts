import { test, expect } from '@playwright/test';
import path from 'node:path';

test.skip(!process.env.EDGEMED_UI_REVIEW_URL, 'Run against the built frontend for visual review.');

const initialNotes = [
  {
    id: 'one',
    title: 'Persistent cough and fever',
    content: '[SYNTHETIC CLINICAL OBSERVATION]\nSubject: SYN-001\nOrgan System: Respiratory\nPrimary Finding: Persistent cough and fever\nSeverity: Moderate\nDetailed Assessment: Bilateral crackles.',
    subject: 'SYN-001',
    category: 'OBSERVATION',
    privacy: 'SENSITIVE',
    release: 'LOCAL_ONLY',
    heads: ['r1'],
    fixture: null,
    conflicting: false,
    index_state: 'indexed',
    created: 1727500000,
  },
  {
    id: 'two',
    title: 'Vitals: BP 120/80, HR 72 bpm, SpO2 98%, Temp 37.0°C',
    content: '[SYNTHETIC VITAL SIGNS RECORD]\nSubject: SYN-001\nBlood Pressure: 120/80 mmHg\nHeart Rate: 72 bpm\nOxygen Saturation: 98%\nTemperature: 37.0 °C\nClinical Context: Stable resting vitals.',
    subject: 'SYN-001',
    category: 'VITAL_SIGN',
    privacy: 'SENSITIVE',
    release: 'LOCAL_ONLY',
    heads: ['r2'],
    fixture: null,
    conflicting: false,
    index_state: 'indexed',
    created: 1727503600,
  },
  {
    id: 'three',
    title: 'Vitals: BP 130/85, HR 88 bpm, SpO2 97%, Temp 37.8°C',
    content: '[SYNTHETIC VITAL SIGNS RECORD]\nSubject: SYN-001\nBlood Pressure: 130/85 mmHg\nHeart Rate: 88 bpm\nOxygen Saturation: 97%\nTemperature: 37.8 °C\nClinical Context: Low-grade fever observed.',
    subject: 'SYN-001',
    category: 'VITAL_SIGN',
    privacy: 'SENSITIVE',
    release: 'LOCAL_ONLY',
    heads: ['r3'],
    fixture: null,
    conflicting: false,
    index_state: 'indexed',
    created: 1727507200,
  },
  {
    id: 'four',
    title: 'Penicillin allergy reported',
    content: '[SYNTHETIC ALLERGY ALERT]\nSubject: SYN-002\nAllergen: Penicillin\nReaction: Maculopapular rash\nSeverity: Moderate\nStatus: Confirmed.',
    subject: 'SYN-002',
    category: 'ALLERGY',
    privacy: 'HIGHLY_SENSITIVE',
    release: 'LOCAL_ONLY',
    heads: ['r4'],
    fixture: null,
    conflicting: false,
    index_state: 'indexed',
    created: 1727510800,
  },
  {
    id: 'five',
    title: 'Medication: Amoxicillin 500 mg Oral TID',
    content: '[SYNTHETIC MEDICATION RECORD]\nSubject: SYN-003\nMedication: Amoxicillin\nDosage: 500 mg\nRoute: Oral\nFrequency: TID\nIndication: Prophylaxis.',
    subject: 'SYN-003',
    category: 'MEDICATION',
    privacy: 'SENSITIVE',
    release: 'LOCAL_ONLY',
    heads: ['r5'],
    fixture: null,
    conflicting: false,
    index_state: 'indexed',
    created: 1727514400,
  },
  {
    id: 'six',
    title: 'Reviewed handoff checklist',
    content: 'Approved synthetic reference for local clinical memory.',
    subject: null,
    category: 'NOTE',
    privacy: 'SENSITIVE',
    release: 'ELIGIBLE',
    heads: ['r6'],
    fixture: 'checklist',
    conflicting: false,
    index_state: 'indexed',
    created: 1727518000,
  },
];

test('Visual Data Logging & Monitoring workspace behaves truthfully and responsively', async ({ page }) => {
  let visibleNotes = [...initialNotes];
  let generation = 1;
  const errors: string[] = [];
  page.on('pageerror', err => errors.push(err.message));

  await page.route('**/api/**', route => {
    const url = new URL(route.request().url());
    const pathname = url.pathname;
    const method = route.request().method();

    if (pathname === '/api/session') {
      return route.fulfill({ json: { csrf: 'synthetic-token', role: 'admin', username: 'operator' } });
    }
    if (pathname === '/api/status') {
      return route.fulfill({
        json: {
          generation,
          deployment: 'local',
          workspace: 'Synthetic workspace',
          role: 'admin',
          device: 'edge-a',
          total: visibleNotes.length,
          local_only: visibleNotes.filter(n => !n.fixture).length,
          conflicts: visibleNotes.filter(n => n.conflicting).length,
          indexed: visibleNotes.filter(n => n.index_state === 'indexed').length,
          vault: true,
          worker_error: null,
          database: 'SQLCipher',
          engine: 'Qdrant Edge 0.8.0',
          model: 'bge-small-en-v1.5',
        },
      });
    }
    if (pathname === '/api/sync/status') {
      return route.fulfill({
        json: {
          enabled: true,
          connection: 'connected',
          error: null,
          last_sync: 1727520000,
          counts: { pending: 1, retry_wait: 0, failed: 0, acknowledged: 2 },
          items: [{ id: 'op-1', state: 'pending', attempts: 0, error: null }],
        },
      });
    }
    if (pathname === '/api/memories' && method === 'GET') {
      const isConflicts = url.searchParams.get('conflicts') === 'true';
      return route.fulfill({ json: isConflicts ? visibleNotes.filter(n => n.conflicting) : visibleNotes });
    }
    if (pathname === '/api/memories' && method === 'POST') {
      const data = route.request().postDataJSON();
      const newMemory = {
        id: `new-${Date.now()}`,
        title: data.title,
        content: data.content,
        subject: data.subject || 'SYN-001',
        category: data.category || 'OBSERVATION',
        privacy: data.privacy || 'SENSITIVE',
        release: 'LOCAL_ONLY',
        heads: [`r-${Date.now()}`],
        fixture: null,
        conflicting: false,
        index_state: 'indexed',
        created: Math.floor(Date.now() / 1000),
      };
      visibleNotes = [newMemory, ...visibleNotes];
      generation++;
      return route.fulfill({ status: 201, json: newMemory });
    }
    if (pathname.startsWith('/api/memories/') && pathname.endsWith('/revisions') && method === 'POST') {
      const id = pathname.split('/')[3];
      const data = route.request().postDataJSON();
      const target = visibleNotes.find(n => n.id === id);
      if (target) {
        target.content = data.content;
        target.heads = [`r-${Date.now()}`];
      }
      generation++;
      return route.fulfill({ status: 201, json: { ok: true } });
    }
    if (pathname.startsWith('/api/memories/') && pathname.endsWith('/resolve') && method === 'POST') {
      const id = pathname.split('/')[3];
      const data = route.request().postDataJSON();
      const target = visibleNotes.find(n => n.id === id);
      if (target) {
        target.conflicting = false;
        target.heads = [data.chosen];
      }
      generation++;
      return route.fulfill({ json: { ok: true } });
    }
    if (pathname.startsWith('/api/memories/') && method === 'GET') {
      const id = pathname.split('/').at(-1);
      const note = visibleNotes.find(n => n.id === id) ?? visibleNotes[0];
      return route.fulfill({
        json: {
          ...note,
          revisions: note.heads.map((h, i) => ({
            id: h,
            content: i ? 'Concurrent branch B from edge-b.' : note.content,
            created: note.created + i * 60,
            parents: [],
            variant: 0,
            device: i ? 'edge-b' : 'edge-a',
          })),
          reason: 'Protected workspace observation in canonical vault.',
        },
      });
    }
    return route.fulfill({ json: {} });
  });

  await page.goto(process.env.EDGEMED_UI_REVIEW_URL!);
  await expect(page.getByRole('heading', { name: 'Memory explorer' })).toBeVisible();

  // 1. Navigate to "Visual logging" workspace
  await page.getByRole('navigation', { name: 'Primary' }).getByRole('button', { name: 'Visual logging' }).click();
  await expect(page.getByRole('heading', { name: 'Visual logging & monitoring' })).toBeVisible();

  // 2. Check Telemetry Status indicators
  await expect(page.getByText('Canonical Storage')).toBeVisible();
  await expect(page.getByText('Encrypted Vault')).toBeVisible();
  await expect(page.getByText('Retrieval Engine')).toBeVisible();
  await expect(page.getByText('Qdrant Edge')).toBeVisible();
  await expect(page.getByText('Indexing Pipeline')).toBeVisible();
  await expect(page.getByText('Selective Sync')).toBeVisible();

  // 3. Check Quick-Entry Cards
  await expect(page.getByText('Quick-entry logging')).toBeVisible();
  const quickGrid = page.locator('.quick-entry-grid');
  await expect(quickGrid.locator('.quick-card-title', { hasText: 'Log Vitals' })).toBeVisible();
  await expect(quickGrid.locator('.quick-card-title', { hasText: 'Observation' })).toBeVisible();
  await expect(quickGrid.locator('.quick-card-title', { hasText: 'Medication' })).toBeVisible();
  await expect(quickGrid.locator('.quick-card-title', { hasText: 'Allergy / Alert' })).toBeVisible();
  await expect(quickGrid.locator('.quick-card-title', { hasText: 'SBAR Note' })).toBeVisible();

  // 4. Check Real-Data Charts
  await expect(page.getByRole('heading', { name: 'Category distribution' })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Observations by subject' })).toBeVisible();
  await expect(page.getByText('Heart Rate trend')).toBeVisible();

  // 5. Open Quick-Entry "Log Vitals" modal and submit structured vitals
  await quickGrid.getByRole('button', { name: /Log Vitals/ }).click();
  await expect(page.getByRole('dialog', { name: 'Add observation' })).toBeVisible();
  await expect(page.getByText('Live Structured Preview')).toBeVisible();

  // Modify systolic BP
  await page.getByLabel('Systolic BP (mmHg)').fill('135');
  await page.getByRole('button', { name: 'Save locally' }).click();
  await expect(page.getByRole('dialog')).toHaveCount(0);

  // Newly saved vitals should appear in the timeline
  await expect(page.locator('.timeline-stream').getByText('BP 135/80')).toBeVisible();

  // 6. Test Observation Timeline Filters
  // Filter by Category: Allergy
  await page.locator('.category-filter-pills').getByRole('button', { name: /Allergy/ }).click();
  await expect(page.locator('.timeline-stream').getByText('Penicillin allergy reported')).toBeVisible();
  await expect(page.locator('.timeline-stream').getByText('BP 135/80')).toHaveCount(0);

  // Reset filter
  await page.locator('.category-filter-pills').getByRole('button', { name: /^All \(\d+\)$/ }).click();
  await expect(page.locator('.timeline-stream').getByText('BP 135/80')).toBeVisible();

  // Search input within timeline
  const searchInput = page.getByRole('searchbox', { name: 'Filter observation timeline' });
  await searchInput.fill('Penicillin');
  await expect(page.locator('.timeline-stream').getByText('Penicillin allergy reported')).toBeVisible();
  await expect(page.locator('.timeline-stream').getByText('BP 135/80')).toHaveCount(0);
  await page.getByRole('button', { name: 'Clear filter search' }).click();
  await expect(page.locator('.timeline-stream').getByText('BP 135/80')).toBeVisible();

  // 7. Click an observation card to open Record Inspector
  await page.locator('.timeline-stream').getByText('Penicillin allergy reported').click();
  await expect(page.getByRole('dialog', { name: 'Memory inspector' })).toBeVisible();
  await expect(page.getByText('Revision history (1)')).toBeVisible();
  await expect(page.getByLabel('Add a corrected observation')).toBeVisible();

  // Add a corrected revision
  await page.getByLabel('Add a corrected observation').fill('Updated allergy note: also sensitive to Cephalosporins.');
  await page.getByRole('button', { name: 'Save revision' }).click();
  await expect(page.getByText('Revision saved locally.')).toBeVisible();
  await page.keyboard.press('Escape');

  // 8. Test Conflict Alert Banner and Resolution Workflow
  visibleNotes = [
    { ...visibleNotes[0], conflicting: true, heads: ['head-1', 'head-2'] },
    ...visibleNotes.slice(1),
  ];
  generation++;
  await page.reload();
  await expect(page.getByRole('heading', { name: 'Memory explorer' })).toBeVisible();
  await page.getByRole('navigation', { name: 'Primary' }).getByRole('button', { name: 'Visual logging' }).click();

  // Conflict banner should appear
  await expect(page.getByText(/conflicting observation branch.*detected/i)).toBeVisible();
  await page.getByRole('button', { name: 'Review & resolve' }).click();
  await expect(page.getByRole('heading', { name: 'Needs review' })).toBeVisible();

  // 9. Responsive layout tests across viewports
  await page.getByRole('navigation', { name: 'Primary' }).getByRole('button', { name: 'Visual logging' }).click();
  await expect(page.getByRole('heading', { name: 'Visual logging & monitoring' })).toBeVisible();

  // Desktop wide (1440)
  await page.setViewportSize({ width: 1440, height: 900 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);

  // Narrow (1100)
  await page.setViewportSize({ width: 1100, height: 850 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);

  // Tablet (900)
  await page.setViewportSize({ width: 900, height: 850 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);

  // Mobile (390)
  await page.setViewportSize({ width: 390, height: 844 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);

  // Mobile narrow (320)
  await page.setViewportSize({ width: 320, height: 700 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);

  expect(errors).toEqual([]);
});

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
    content: '[SYNTHETIC VITAL SIGNS RECORD]\nSubject: SYN-001\nBlood Pressure: 120/80 mmHg\nHeart Rate: 72 bpm\nOxygen Saturation (SpO2): 98%\nBody Temperature: 37.0 °C\nClinical Context: Stable resting vitals.',
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
    content: '[SYNTHETIC VITAL SIGNS RECORD]\nSubject: SYN-001\nBlood Pressure: 130/85 mmHg\nHeart Rate: 88 bpm\nOxygen Saturation (SpO2): 97%\nBody Temperature: 37.8 °C\nClinical Context: Low-grade fever observed.',
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
    content: '[SYNTHETIC ALLERGY & ADVERSE REACTION]\nSubject: SYN-002\nAllergen: Penicillin\nReaction: Maculopapular rash\nSeverity: Moderate\nStatus: Confirmed\nClinical Guidance: Avoid all beta-lactam class antibiotics.',
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
    content: '[SYNTHETIC MEDICATION ADMINISTRATION]\nSubject: SYN-003\nMedication Name: Amoxicillin\nDosage & Unit: 500 mg\nRoute: Oral\nFrequency / Schedule: TID (Three times daily)\nIndication: Lower respiratory tract prophylaxis.',
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
    title: 'Reviewed clinical reference protocol',
    content: 'Approved synthetic reference variant for hospital LAN demonstrations.',
    subject: null,
    category: 'NOTE',
    privacy: 'SENSITIVE',
    release: 'ELIGIBLE',
    heads: ['r6'],
    fixture: 'protocol',
    conflicting: false,
    index_state: 'indexed',
    created: 1727518000,
  },
];

test('Synthetic Subjects / Patient Roster workspace behaves truthfully and responsively', async ({ page }) => {
  let visibleNotes = [...initialNotes];
  let generation = 1;
  const errors: string[] = [];
  page.on('pageerror', err => errors.push(err.message));

  await page.route('**/api/**', route => {
    const url = new URL(route.request().url());
    const pathname = url.pathname;
    let body: unknown = {};

    if (pathname === '/api/session') {
      body = { csrf: 'synthetic-token', role: 'admin', username: 'operator' };
    } else if (pathname === '/api/status') {
      body = {
        generation,
        deployment: 'local',
        workspace: 'Synthetic clinical workspace',
        role: 'admin',
        device: 'edge-a',
        total: visibleNotes.length,
        local_only: visibleNotes.length,
        conflicts: visibleNotes.filter(n => n.conflicting).length,
        indexed: visibleNotes.length,
        vault: true,
        worker_error: null,
        database: 'SQLCipher AES-256',
        engine: 'Qdrant Edge',
      };
    } else if (pathname === '/api/sync/status') {
      body = {
        enabled: true,
        connection: 'connected',
        error: null,
        counts: { pending: 0, retry_wait: 0, failed: 0, acknowledged: 1 },
        items: [],
      };
    } else if (pathname === '/api/memories' && route.request().method() === 'GET') {
      body = url.searchParams.get('conflicts') === 'true'
        ? visibleNotes.filter(n => n.conflicting)
        : visibleNotes;
    } else if (pathname === '/api/memories' && route.request().method() === 'POST') {
      const payload = route.request().postDataJSON();
      const newMemory = {
        id: 'new-' + Date.now(),
        title: payload.title,
        content: payload.content,
        subject: payload.subject,
        category: payload.category,
        privacy: payload.privacy,
        release: 'LOCAL_ONLY',
        heads: ['new-head'],
        fixture: null,
        conflicting: false,
        index_state: 'indexed',
        created: Math.floor(Date.now() / 1000),
      };
      visibleNotes.unshift(newMemory);
      generation++;
      body = newMemory;
    } else if (pathname.startsWith('/api/memories/')) {
      const memoryId = pathname.split('/').at(-1);
      const note = visibleNotes.find(entry => entry.id === memoryId) ?? visibleNotes[0];
      body = {
        ...note,
        revisions: note.heads.map((h, i) => ({
          id: h,
          content: i ? 'Conflicting branch content' : note.content,
          created: note.created + i,
          parents: [],
          variant: 0,
          device: i ? 'edge-b' : 'edge-a',
        })),
        reason: 'Visible in this synthetic clinical workspace.',
      };
    }

    return route.fulfill({ json: body });
  });

  await page.goto(process.env.EDGEMED_UI_REVIEW_URL!);

  // 1. Navigate to Subjects view
  const primaryNav = page.getByRole('navigation', { name: 'Primary' });
  await expect(primaryNav.getByRole('button', { name: 'Subjects' })).toBeVisible();
  await primaryNav.getByRole('button', { name: 'Subjects' }).click();

  // 2. Verify workspace header
  await expect(page.getByRole('heading', { name: 'Synthetic subjects / patient roster' })).toBeVisible();
  await expect(page.getByText('Consolidated patient charts, longitudinal vital trends, allergy alerts, and chronological history.')).toBeVisible();

  // 3. Verify Subject Roster sidebar
  const roster = page.locator('.subject-roster-panel');
  await expect(roster.getByRole('heading', { name: 'Synthetic subjects' })).toBeVisible();
  await expect(roster.getByText('3 subjects')).toBeVisible();

  // Verify subjects appear in the roster
  await expect(roster.getByText('SYN-001')).toBeVisible();
  await expect(roster.getByText('SYN-002')).toBeVisible();
  await expect(roster.getByText('SYN-003')).toBeVisible();

  // Verify badges on roster cards
  await expect(roster.locator('.subject-roster-card').filter({ hasText: 'SYN-002' }).getByText('Allergy alert')).toBeVisible();
  await expect(roster.locator('.subject-roster-card').filter({ hasText: 'SYN-001' }).getByText('2 vitals')).toBeVisible();

  // 4. Test Roster Search
  const searchInput = roster.getByRole('textbox', { name: 'Search synthetic subjects' });
  await searchInput.fill('SYN-002');
  await expect(roster.getByText('SYN-002')).toBeVisible();
  await expect(roster.getByText('SYN-001')).not.toBeVisible();
  await expect(roster.getByText('1 subjects')).toBeVisible();

  // Clear search
  await roster.getByRole('button', { name: 'Clear subject search' }).click();
  await expect(roster.getByText('SYN-001')).toBeVisible();
  await expect(roster.getByText('3 subjects')).toBeVisible();

  // 5. Inspect SYN-001 Chart (Vitals & NKDA)
  await roster.locator('.subject-roster-card').filter({ hasText: 'SYN-001' }).click();
  const chart = page.locator('.patient-chart-panel');
  await expect(chart.getByRole('heading', { name: 'SYN-001' })).toBeVisible();

  // Vitals section
  await expect(chart.getByRole('heading', { name: 'Longitudinal Vital Signs Trend' })).toBeVisible();
  await expect(chart.getByText('Heart Rate', { exact: true })).toBeVisible();
  await expect(chart.getByText('Blood Pressure', { exact: true })).toBeVisible();
  await expect(chart.getByText('Body Temperature', { exact: true })).toBeVisible();
  await expect(chart.getByText('Oxygen Saturation (SpO₂)', { exact: true })).toBeVisible();

  // Vitals measurements
  await expect(chart.getByText('88', { exact: true })).toBeVisible(); // Latest HR
  await expect(chart.getByText('130', { exact: true })).toBeVisible(); // Latest systolic
  await expect(chart.getByText('85', { exact: true })).toBeVisible(); // Latest diastolic

  // Allergies section for SYN-001: should show NKDA (no invented allergies!)
  await expect(chart.getByText('No Known Drug Allergies (NKDA)')).toBeVisible();

  // 6. Inspect SYN-002 Chart (Confirmed Allergy Alert)
  await roster.locator('.subject-roster-card').filter({ hasText: 'SYN-002' }).click();
  await expect(chart.getByRole('heading', { name: 'SYN-002' })).toBeVisible();
  const allergiesSection = chart.locator('.allergies-section');
  await expect(allergiesSection.getByText('Penicillin', { exact: true })).toBeVisible();
  await expect(allergiesSection.getByText('Maculopapular rash')).toBeVisible();
  await expect(allergiesSection.getByText('Avoid all beta-lactam class antibiotics.')).toBeVisible();

  // Click allergy card to open canonical Memory Inspector
  await chart.locator('.allergy-alert-card').click();
  const inspector = page.getByRole('dialog', { name: 'Memory inspector' });
  await expect(inspector).toBeVisible();
  await expect(inspector.getByText('Penicillin allergy reported')).toBeVisible();
  await expect(inspector.getByText('SYN-002', { exact: true })).toBeVisible();
  await expect(inspector.getByText('Personal · only you')).toBeVisible(); // HIGHLY_SENSITIVE
  await page.keyboard.press('Escape');
  await expect(inspector).not.toBeVisible();

  // 7. Inspect SYN-003 Chart (Active Medication)
  await roster.locator('.subject-roster-card').filter({ hasText: 'SYN-003' }).click();
  await expect(chart.getByRole('heading', { name: 'SYN-003' })).toBeVisible();
  const medsSection = chart.locator('.medications-section');
  await expect(medsSection.getByText('Amoxicillin', { exact: true })).toBeVisible();
  await expect(medsSection.getByText('500 mg · Oral')).toBeVisible();
  await expect(medsSection.getByText('TID (Three times daily)')).toBeVisible();

  // Click medication card to open canonical Memory Inspector
  await chart.locator('.medication-card').click();
  const medInspector = page.getByRole('dialog', { name: 'Memory inspector' });
  await expect(medInspector).toBeVisible();
  await expect(medInspector.getByText('Medication: Amoxicillin 500 mg Oral TID')).toBeVisible();
  await page.keyboard.press('Escape');
  await expect(medInspector).not.toBeVisible();

  // 8. Test Timeline filtering and inspection on SYN-001
  await roster.locator('.subject-roster-card').filter({ hasText: 'SYN-001' }).click();
  await expect(chart.getByRole('heading', { name: 'Chronological Observation History' })).toBeVisible();

  // Filter by category pills
  await chart.locator('.timeline-pill').filter({ hasText: 'Vital Signs' }).click();
  await expect(chart.locator('.timeline-item-card')).toHaveCount(2);

  // Click a timeline item to open canonical Inspector
  await chart.locator('.timeline-item-card').first().click();
  await expect(page.getByRole('dialog', { name: 'Memory inspector' })).toBeVisible();
  await page.keyboard.press('Escape');
  await expect(page.getByRole('dialog', { name: 'Memory inspector' })).not.toBeVisible();

  // 9. Conflict / Needs Review branch handling
  visibleNotes = [
    { ...initialNotes[0], conflicting: true, heads: ['r1', 'r1-divergent'] },
    ...initialNotes.slice(1),
  ];
  generation = 2;
  await page.reload();
  await primaryNav.getByRole('button', { name: 'Subjects' }).click();
  await roster.locator('.subject-roster-card').filter({ hasText: 'SYN-001' }).click();

  // Conflict alert banner should be visible
  await expect(chart.getByText('Divergent Branch History Needs Review')).toBeVisible();
  await chart.getByRole('button', { name: 'Compare branches' }).click();
  await expect(page.getByRole('dialog', { name: 'Memory inspector' })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Compare current branches' })).toBeVisible();
  await page.keyboard.press('Escape');

  // 10. Responsive layout testing down to mobile (1100, 900, 390, 320px)
  await page.setViewportSize({ width: 1100, height: 850 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);

  await page.setViewportSize({ width: 900, height: 850 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);

  // Mobile 390px
  await page.setViewportSize({ width: 390, height: 844 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);

  // On mobile with subject selected, chart is visible and back button works
  await expect(chart.getByRole('button', { name: 'Back to Subject Roster' })).toBeVisible();
  await chart.getByRole('button', { name: 'Back to Subject Roster' }).click();
  await expect(roster.getByText('SYN-001')).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);

  // Mobile 320px
  await page.setViewportSize({ width: 320, height: 700 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);

  // Take screenshot for visual verification
  await page.screenshot({
    path: path.resolve(process.cwd(), '../test-results/subjects-mobile-320.png'),
    fullPage: true,
  });

  // Zero unhandled console page errors
  expect(errors).toEqual([]);
});

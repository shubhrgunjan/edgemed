import { test, expect } from '@playwright/test';
import { readFileSync } from 'node:fs';

const file = process.env.EDGEMED_STAFF_TEST_CREDENTIALS;
test('two staff browsers share a workspace without exposing personal notes', async ({ browser }) => {
  test.skip(!file, 'Requires isolated staff accounts in an encrypted verification vault');
  const passwords = JSON.parse(readFileSync(file!, 'utf8')) as Record<string, string>;
  const alice = await browser.newContext({ viewport: { width: 390, height: 844 }, ignoreHTTPSErrors: process.env.EDGEMED_TEST_UNTRUSTED_CA === '1' });
  const bob = await browser.newContext({ viewport: { width: 390, height: 844 }, ignoreHTTPSErrors: process.env.EDGEMED_TEST_UNTRUSTED_CA === '1' });
  const first = await alice.newPage(), second = await bob.newPage();
  const shared = `Shared ward note ${Date.now()}`, personal = `Personal staff note ${Date.now()}`;
  async function login(page: typeof first, name: string) {
    await page.goto('/');
    await page.getByLabel('Username').fill(name);
    await page.getByLabel('Password', { exact: true }).fill(passwords[name]);
    await page.getByRole('button', { name: 'Sign in locally' }).click();
    await expect(page.getByRole('heading', { name: 'Memory explorer', exact: true })).toBeVisible();
  }
  async function save(page: typeof first, title: string, privacy: string) {
    await page.getByRole('button', { name: 'Add observation', exact: true }).click();
    await page.getByLabel('Title', { exact: true }).fill(title);
    await page.getByLabel('Observation', { exact: true }).fill(`Synthetic ${title}`);
    await page.getByLabel('Privacy').selectOption(privacy);
    await page.getByRole('button', { name: 'Save locally' }).click();
    await expect(page.getByText(title, { exact: true })).toBeVisible();
  }
  try {
    await login(first, 'alice');
    expect((await (await first.request.get('/api/status')).json()).deployment).toBe('hospital_lan');
    await save(first, shared, 'SENSITIVE');
    await save(first, personal, 'HIGHLY_SENSITIVE');
    await login(second, 'bob');
    await expect(second.getByText(shared, { exact: true })).toBeVisible();
    await expect(second.getByText(personal, { exact: true })).toHaveCount(0);
    await second.getByRole('textbox', { name: 'Search memory' }).fill(personal);
    await second.getByRole('button', { name: 'Search', exact: true }).click();
    await expect(second.getByText(personal, { exact: true })).toHaveCount(0);
    expect(await second.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  } finally { await alice.close(); await bob.close(); }
});

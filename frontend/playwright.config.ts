import { defineConfig } from '@playwright/test';
export default defineConfig({testDir:'./tests',timeout:30000,workers:1,reporter:'list',use:{baseURL:'http://127.0.0.1:8765',headless:true,viewport:{width:1440,height:1000},launchOptions:{executablePath:process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE}},outputDir:'../test-results/browser'});

import {defineConfig} from '@playwright/test';
export default defineConfig({
  testDir:'./tests',testMatch:'live.spec.ts',timeout:90000,retries:0,workers:1,
  outputDir:'test-results/live',
  reporter:[['list'],['json',{outputFile:'test-results/live/results.json'}]],
  use:{browserName:'chromium',channel:'chrome',viewport:{width:1280,height:900},trace:'retain-on-failure'},
});

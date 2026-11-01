import {defineConfig} from '@playwright/test';
export default defineConfig({
  testDir:'./tests',timeout:60000,workers:1,
  use:{baseURL:'http://127.0.0.1:4173/mlspend/',headless:true,trace:'retain-on-failure'},
  webServer:{command:'cd .. && python -m scripts.serve_frontend_test',url:'http://127.0.0.1:4173/mlspend/',reuseExistingServer:false},
  reporter:[['list'],['json',{outputFile:'test-results/browser-results.json'}]]
});

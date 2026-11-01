import {test,expect} from '@playwright/test';
import {writeFile,mkdir} from 'node:fs/promises';
import manifest from '../data.json';

test('published estimator persists one request and returns a measured cost',async({page,request})=>{
  const site='https://mekala27-45.github.io/mlspend/';
  const api='https://mlspend.vercel.app';
  const shipped=await request.get(site+'data.json');
  expect(shipped.ok()).toBe(true);
  const shippedData=await shipped.json();
  expect(shippedData.price_digest).toBe(manifest.price_digest);
  expect(shippedData.portfolio).toEqual(manifest.portfolio);
  const firstStart=performance.now();
  const health=await request.get(api+'/health');
  expect(health.ok()).toBe(true);
  expect((await health.json()).price_digest).toBe(shippedData.price_digest);
  const firstObservedMs=performance.now()-firstStart;
  const errors:string[]=[];
  page.on('pageerror',error=>errors.push(error.message));
  await page.goto(site+'estimate/');
  await page.getByLabel('Hosting price').selectOption('azure-t4');
  await page.getByRole('spinbutton',{name:'Requests per day',exact:true}).fill('23');
  await page.getByRole('spinbutton',{name:'Days',exact:true}).fill('1');
  const estimateResponse=page.waitForResponse(response=>response.url()===api+'/v1/estimate'&&response.request().method()==='POST');
  await page.getByRole('button',{name:'Calculate workload cost'}).click();
  const response=await estimateResponse;
  expect(response.ok()).toBe(true);
  const result=await response.json();
  await expect(page.getByText('Saved reference: '+result.id)).toBeVisible();
  expect(result.shadow_cost_usd).toBe('12.624');
  const meter=response.headers()['x-shadow-cost-usd'];
  expect(meter).toBeTruthy();
  expect(Number(meter)).toBeGreaterThanOrEqual(0);
  const readback=await request.get(api+'/v1/estimates/'+result.id);
  expect(readback.ok()).toBe(true);
  const saved=(await readback.json()).estimate;
  expect(JSON.parse(saved.payload).requests_per_day).toBe(23);
  expect(JSON.parse(saved.result).shadow_cost_usd).toBe(result.shadow_cost_usd);
  expect(errors).toEqual([]);
  const latencies:number[]=[];
  for(let i=0;i<20;i++) {
    const start=performance.now();
    const probe=await request.get(api+'/health');
    expect(probe.ok()).toBe(true);
    expect((await probe.json()).database).toBe('connected');
    latencies.push(performance.now()-start);
  }
  const ordered=[...latencies].sort((a,b)=>a-b);
  await mkdir('test-results/live',{recursive:true});
  await page.screenshot({path:'test-results/live/published-estimate.png',fullPage:true});
  await writeFile('test-results/live/evidence.json',JSON.stringify({
    checked_at:new Date().toISOString(),site,api,estimate_id:result.id,
    shadow_cost_usd:result.shadow_cost_usd,request_meter_usd:meter,
    price_digest:shippedData.price_digest,status:'passed',
    latency:{endpoint:'/health',first_observed_ms:firstObservedMs,samples_ms:latencies,p50_ms:ordered[9],p99_ms:ordered[19],method:'nearest rank over 20 sequential requests; includes network',cold_start:'not isolated; first observed request is not proof of a cold invocation'},
    checks:['published data matches commit','real cross-origin browser POST','saved reference visible','independent HTTP readback','no page errors'],
  },null,2));
});

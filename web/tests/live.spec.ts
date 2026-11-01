import {test,expect} from '@playwright/test';
import {writeFile,mkdir,readFile} from 'node:fs/promises';
import manifest from '../expanded.json';

test('published Chrome flow compares hosting, persists a forecast and exposes measured cost',async({page,request})=>{
  const site='https://mekala27-45.github.io/mlspend/',api='https://mlspend.vercel.app';
  const shipped=await request.get(site+'expanded.json');
  expect(shipped.ok()).toBe(true);
  const shippedData=await shipped.json();
  expect(shippedData.source_digest).toBe(manifest.source_digest);
  const before=JSON.parse(await readFile('test-results/idle-before.json','utf8'));
  const start=performance.now(),health=await request.get(api+'/health',{timeout:45000});
  expect(health.ok()).toBe(true);
  const first=await health.json(),firstMs=performance.now()-start;
  const idleSeconds=(Date.now()-Date.parse(before.checked_at))/1000;
  expect(idleSeconds).toBeGreaterThanOrEqual(1200);
  const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto(site+'estimate/');
  await page.getByLabel('Hosting price').selectOption('azure-t4');
  await page.getByRole('spinbutton',{name:'Requests per day',exact:true}).fill('23');
  await page.getByRole('spinbutton',{name:'Days',exact:true}).fill('1');
  const pending=page.waitForResponse(r=>r.url()===api+'/v1/estimate'&&r.request().method()==='POST');
  await page.getByRole('button',{name:'Calculate workload cost'}).click();
  const response=await pending;expect(response.ok()).toBe(true);const result=await response.json();
  await expect(page.getByText('Saved reference: '+result.id)).toBeVisible();
  expect(result.shadow_cost_usd).toBe('12.624');
  expect(result.options.map((r:{option:string})=>r.option)).toEqual(expect.arrayContaining(['azure-t4','aws-g4dn.xlarge','openai-gpt-6.1-terra','openai-gpt-6-luna']));
  const meter=response.headers()['x-shadow-cost-usd'];expect(Number(meter)).toBeGreaterThanOrEqual(0);
  const readback=await request.get(api+'/v1/estimates/'+result.id);expect(readback.ok()).toBe(true);
  expect(JSON.parse((await readback.json()).estimate.payload).requests_per_day).toBe(23);
  await mkdir('test-results/live',{recursive:true});
  await page.screenshot({path:'test-results/live/estimate.png'});
  await page.goto(site+'forecast/');
  const now=new Date(),next=new Date(Date.UTC(now.getUTCFullYear(),now.getUTCMonth()+1,1));
  const period=next.toISOString().slice(0,7),cutoff=now.toISOString().slice(0,10);
  await page.getByLabel('Team or project').fill('trajectory-ci-known-subtotal');
  await page.getByLabel('Future month').fill(period);await page.getByLabel('Data cutoff').fill(cutoff);
  // Explicit scenario forecast for the known CI subtotal; no missing GPU/token charge is zeroed.
  await page.getByLabel('Point USD',{exact:true}).fill('25');await page.getByLabel('Lower USD').fill('10');await page.getByLabel('Upper USD').fill('50');
  const forecastPending=page.waitForResponse(r=>r.url()===api+'/v1/forecasts'&&r.request().method()==='POST');
  await page.getByRole('button',{name:'Save future forecast'}).click();
  const forecastResponse=await forecastPending;expect(forecastResponse.ok()).toBe(true);const forecast=await forecastResponse.json();
  await expect(page.getByText('Future forecast saved.',{exact:false})).toBeVisible();
  const forecastReadback=await request.get(api+'/v1/forecasts/'+forecast.id);expect(forecastReadback.ok()).toBe(true);
  await page.screenshot({path:'test-results/live/forecast.png'});
  for(const route of ['statement','allocation','anomalies','portfolio']){await page.goto(route==='statement'?site:site+route+'/');await expect(page.locator('h1')).toBeVisible();await page.screenshot({path:'test-results/live/'+route+'.png'});}
  const samples=[];
  for(let i=0;i<20;i++){const t=performance.now();const h=await request.get(api+'/health');expect(h.ok()).toBe(true);samples.push({ms:performance.now()-t,...await h.json()});}
  const ordered=samples.map(r=>r.ms).sort((a,b)=>a-b);
  expect(errors).toEqual([]);
  await writeFile('test-results/live/evidence.json',JSON.stringify({checked_at:new Date().toISOString(),site,api,browser:await page.evaluate(()=>navigator.userAgent),source_digest:manifest.source_digest,estimate_id:result.id,forecast_id:forecast.id,forecast:{period,cutoff,team:'trajectory-ci-known-subtotal',point_usd:25,lower_usd:10,upper_usd:50,method:'User-authorized demonstration scenario, not a statistically calibrated live forecast',status:'pending_actuals'},request_headers:response.headers(),request_meter_usd:meter,options:result.options.map((r:{option:string})=>r.option),idle:{seconds:idleSeconds,before_instance:before.health.instance_id,after_instance:first.instance_id,after_uptime:first.process_uptime_seconds,first_response_ms:firstMs,new_process_observed:first.instance_id!==before.health.instance_id&&first.process_uptime_seconds<10,limit:'Other public callers cannot be excluded; a new instance and short uptime are evidence, idle time alone is not.'},warm:{samples,p50_ms:ordered[9],p99_ms:ordered[19],method:'Nearest rank, 20 sequential health requests, includes network and database time'},checks:['published source matches','real cross-origin browser POST','all hosting families','independent estimate and forecast readback','meter response header','20-minute no-probe interval','no page errors'],status:'passed'},null,2));
});

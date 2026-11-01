import {test,expect} from '@playwright/test';
const api='https://mlspend-mekala27-45s-projects.vercel.app';

test('all static routes expose results and the disclosure at desktop and mobile sizes',async({page})=>{
  const failures:string[]=[];
  page.on('pageerror',error=>failures.push(error.message));
  for(const width of [1280,390]) {
    await page.setViewportSize({width,height:900});
    for(const route of ['', 'allocation/', 'unit/', 'anomalies/', 'forecast/', 'recommendations/', 'commitments/', 'portfolio/', 'estimate/', 'data/', 'report/']) {
      await page.goto(route);
      await expect(page.locator('h1')).toBeVisible();
      await expect(page.locator('footer')).toContainText('platform costs are simulated');
      expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBe(true);
    }
  }
  await page.goto('');
  await page.screenshot({path:'test-results/statement-mobile.png',fullPage:true});
  await page.getByRole('button',{name:'Use carbon copy'}).click();
  await expect(page.locator('html')).toHaveClass('dark');
  await page.screenshot({path:'test-results/statement-carbon.png',fullPage:true});
  expect(failures).toEqual([]);
});

test('first-503 health recovery uses GET and submits one fixture estimate',async({page})=>{
  let gets=0,posts=0;
  await page.route(api+'/**',async route=>{
    if(route.request().url().endsWith('/health')) {
      expect(route.request().method()).toBe('GET');gets++;
      await route.fulfill({status:gets===1?503:200,json:{status:'ready'}});
    }else{posts++;await route.fulfill({json:{id:'browser-test-fixture',shadow_cost_usd:'378.720',replicas:1,days:30},headers:{'x-shadow-cost-usd':'0.000001'}});}
  });
  await page.goto('estimate/');
  await page.getByRole('button',{name:'Calculate workload cost'}).click();
  await expect(page.getByText('Saved reference: browser-test-fixture')).toBeVisible();
  expect(gets).toBe(2);expect(posts).toBe(1);
});

test('an uncertain write is not repeated or mislabeled as an unsaved local result',async({page})=>{
  let posts=0;
  await page.route(api+'/**',async route=>{
    if(route.request().method()==='POST'){posts++;await route.abort();}
    else await route.fulfill({json:{status:'ready'}});
  });
  await page.goto('estimate/');
  await page.getByRole('button',{name:'Calculate workload cost'}).click();
  await expect(page.getByText(/save status is unknown/)).toBeVisible();
  expect(posts).toBe(1);await expect(page.getByText('Local calculation only.',{exact:false})).toHaveCount(0);
});

test('the browser SQL engine queries the complete shipped monthly table',async({page})=>{
  await page.goto('data/');
  await page.getByLabel('SQL',{exact:true}).fill('SELECT COUNT(*) AS months FROM monthly');
  await page.getByRole('button',{name:'Run SQL locally'}).click();
  await expect(page.locator('pre[aria-live]')).toContainText('"months": "12"',{timeout:45000});
});

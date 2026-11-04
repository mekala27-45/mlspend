import {test,expect} from '@playwright/test';
const api='https://mlspend.vercel.app';

test('training admission recovers an uncertain request with the same identity',async({page})=>{
  const identities:string[]=[];
  await page.route(api+'/v1/simulation/**',async route=>{
    if(route.request().url().endsWith('/budgets')){await route.fulfill({json:{id:'fixture-budget'}});return;}
    identities.push(route.request().postDataJSON().request_id);
    if(identities.length===1){await route.abort();return;}
    await route.fulfill({json:{accepted:true,reason:'Within remaining forecast budget',remaining_after_micro:99000000,forecast_micro:1000000,replayed:true}});
  });
  await page.goto('extensions/');
  await page.getByRole('button',{name:'Create simulation budget'}).click();
  await page.getByRole('button',{name:'Check and reserve forecast cost'}).click();
  await expect(page.getByText(/Admission status is unknown/)).toBeVisible();
  await page.getByRole('button',{name:'Recover admission decision'}).click();
  await expect(page.getByText('Accepted for simulation')).toBeVisible();
  expect(identities.length).toBe(2);expect(identities[0]).toBe(identities[1]);
});

test('all static routes expose results and the disclosure at desktop and mobile sizes',async({page})=>{
  const failures:string[]=[];
  page.on('pageerror',error=>failures.push(page.url()+": "+error.message));
  for(const width of [1280,390]) {
    await page.setViewportSize({width,height:900});
    for(const route of ['', 'allocation/', 'unit/', 'anomalies/', 'forecast/', 'recommendations/', 'commitments/', 'portfolio/', 'estimate/', 'data/', 'report/', 'playbook/', 'extensions/', 'price-history/']) {
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


test('offline health attempts remain GET and never claim a save',async({page})=>{
  let gets=0;
  await page.route(api+'/**',async route=>{expect(route.request().method()).toBe('GET');gets++;await route.fulfill({status:503,json:{status:'configuration_required'},headers:{'Retry-After':'5'}});});
  await page.goto('estimate/');
  await page.getByRole('button',{name:'Calculate workload cost'}).click();
  await expect(page.getByText(/Local calculation only/)).toBeVisible({timeout:15000});
  expect(gets).toBe(2);
  await expect(page.getByText(/Saved reference:/)).toHaveCount(0);
});

for(const dark of [false,true]){
  for(const route of ['', 'allocation/', 'unit/', 'anomalies/', 'forecast/', 'recommendations/', 'commitments/', 'portfolio/', 'estimate/', 'data/', 'report/', 'playbook/', 'extensions/', 'price-history/']){
    test(`keyboard and contrast: ${route||'home'} in ${dark?'dark':'light'} theme`,async({page})=>{
      await page.goto(route);
      await expect(page.locator('html')).toHaveAttribute('data-theme-ready','true');
      if(dark && !(await page.locator('html').getAttribute('class')||'').includes('dark'))await page.getByRole('button',{name:'Use carbon copy'}).click();
      await page.keyboard.press('Control+Home');
      await page.locator('.skip').focus();await page.keyboard.press('Enter');
      await expect(page.locator('#main')).toBeFocused();
      expect(await page.locator('nav a').count()).toBe(14);
      const contrast=await page.locator('main').evaluate(el=>{
        const style=getComputedStyle(el),root=getComputedStyle(document.documentElement);
        const luminance=(color:string)=>{const c=color.match(/[\d.]+/g)!.slice(0,3).map(Number).map(v=>{v/=255;return v<=.04045?v/12.92:((v+.055)/1.055)**2.4});return .2126*c[0]+.7152*c[1]+.0722*c[2]};
        const probe=document.createElement('span');probe.style.color=root.getPropertyValue('--paper');document.body.appendChild(probe);const bg=getComputedStyle(probe).color;probe.remove();
        const a=luminance(style.color),b=luminance(bg);return (Math.max(a,b)+.05)/(Math.min(a,b)+.05);
      });
      expect(contrast).toBeGreaterThanOrEqual(4.5);
    });
  }
}

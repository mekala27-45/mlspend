'use client';
import {useState,type FormEvent} from 'react';
import m from '../data.json';
type Estimate = {id?:string;shadow_cost_usd:string;replicas:number;days:number;meter?:string|null};
export default function EstimateForm() {
  const [busy,setBusy]=useState(false),[result,setResult]=useState<Estimate|null>(null),[notice,setNotice]=useState('');
  async function submit(event:FormEvent<HTMLFormElement>) {
    event.preventDefault();setBusy(true);setResult(null);setNotice('Checking the live API...');
    const form=new FormData(event.currentTarget);
    const payload={price_id:String(form.get('price_id')),requests_per_day:Number(form.get('requests_per_day')),seconds_per_request:String(form.get('seconds_per_request')),capacity_per_replica:Number(form.get('capacity_per_replica')),minimum_replicas:Number(form.get('minimum_replicas')),days:Number(form.get('days'))};
    const base=process.env.NEXT_PUBLIC_API_URL||'';
    let ready=false;
    for(let attempt=0;base&&attempt<2&&!ready;attempt++) {
      try {const health=await fetch(base+'/health',{signal:AbortSignal.timeout(12000)});ready=health.ok&&(await health.json()).status==='ready';}catch{}
    }
    if(!ready) {
      const price=m.prices.find(p=>p.id===payload.price_id)!;
      const replicas=Math.max(payload.minimum_replicas,Math.ceil(payload.requests_per_day*Number(payload.seconds_per_request)/(86400*payload.capacity_per_replica)));
      setResult({shadow_cost_usd:String(Number(price.usd)*replicas*24*payload.days),replicas,days:payload.days});
      setNotice('Local calculation only. The API is unavailable or requires sign-in. This estimate has not been saved.');setBusy(false);return;
    }
    try {
      const response=await fetch(base+'/v1/estimate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload),signal:AbortSignal.timeout(20000)});
      const body=await response.json();
      if(!response.ok){setNotice(typeof body.detail==='string'?body.detail:'The API rejected the estimate.');return;}
      if(typeof body.id!=='string')throw Error('The response did not confirm a saved reference');
      setResult({...body,meter:response.headers.get('X-Shadow-Cost-USD')});setNotice('Saved to the database before the response.');
    }catch(error){setNotice((error instanceof Error?error.message:'Request failed')+'. The save status is unknown. The request was not automatically repeated.');}
    finally{setBusy(false);}
  }
  return <section className="panel"><form className="form" onSubmit={submit}><label>Hosting price<select name="price_id">{m.prices.filter(p=>p.unit==='hour'&&p.term==='on_demand').map(p=><option key={p.id} value={p.id}>{p.sku} / ${p.usd} per hour</option>)}</select></label><label>Requests per day<input name="requests_per_day" type="number" min="0" max="100000000" defaultValue="100000" required/></label><label>Seconds per request<input name="seconds_per_request" type="number" step="0.001" min="0.001" max="3600" defaultValue="0.1" required/></label><label>Capacity per replica<input name="capacity_per_replica" type="number" min="1" max="1000000" defaultValue="1" required/></label><label>Minimum replicas<input name="minimum_replicas" type="number" min="0" max="10000" defaultValue="1" required/></label><label>Days<input name="days" type="number" min="1" max="366" defaultValue="30" required/></label><button disabled={busy} type="submit">{busy?'Checking and calculating...':'Calculate workload cost'}</button></form><div aria-live="polite"><p className="notice mt-6">{notice||'Estimates use documented list prices and caller-supplied throughput.'}</p>{result&&<><div className="metrics"><div className="metric"><div className="label">Shadow estimate</div><strong>${Number(result.shadow_cost_usd).toFixed(2)}</strong><small>{result.days} days</small></div><div className="metric"><div className="label">Replicas</div><strong>{result.replicas}</strong></div><div className="metric"><div className="label">Measured request shadow cost</div><strong>{result.meter?'$'+result.meter:'Not measured'}</strong></div></div>{result.id&&<p className="small">Saved reference: {result.id}</p>}</>}</div></section>;
}

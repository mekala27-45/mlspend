'use client';
import {useState,type FormEvent} from 'react';
import m from '../expanded.json';
type Estimate = {id?:string;shadow_cost_usd:string;replicas:number;days:number;meter?:string|null;options?:{option:string;cost_usd:string;components_usd?:Record<string,string>}[]};
export default function EstimateForm() {
  const [busy,setBusy]=useState(false),[result,setResult]=useState<Estimate|null>(null),[notice,setNotice]=useState('');
  async function submit(event:FormEvent<HTMLFormElement>) {
    event.preventDefault();setBusy(true);setResult(null);setNotice('Checking the live API...');
    const form=new FormData(event.currentTarget);
    const payload={price_id:String(form.get('price_id')),requests_per_day:Number(form.get('requests_per_day')),seconds_per_request:String(form.get('seconds_per_request')),capacity_per_replica:Number(form.get('capacity_per_replica')),minimum_replicas:Number(form.get('minimum_replicas')),days:Number(form.get('days')),model_size_class:String(form.get('model_size_class')),hosting_option:String(form.get('hosting_option')),tokens_in_per_request:Number(form.get('tokens_in_per_request')),tokens_out_per_request:Number(form.get('tokens_out_per_request')),cached_input_fraction:String(form.get('cached_input_fraction'))};
    const base=process.env.NEXT_PUBLIC_API_URL||'';
    let ready=false;
    for(let attempt=0;base&&attempt<2&&!ready;attempt++) {
      try {const health=await fetch(base+'/health',{signal:AbortSignal.timeout(12000)});ready=health.ok&&(await health.json()).status==='ready';}catch{}
    }
    if(!ready) {
      const price=m.prices.find(p=>p.id===payload.price_id)!;
      const replicas=Math.max(payload.minimum_replicas,Math.ceil(payload.requests_per_day*Number(payload.seconds_per_request)/(86400*payload.capacity_per_replica)));
      setResult({shadow_cost_usd:String(Number(price.usd)*replicas*24*payload.days),replicas,days:payload.days});
      setNotice('Local calculation only. The API is unavailable or requires sign-in. This estimate has not been saved. Local fallback covers only the selected instance; token and hosting comparisons require the live API.');setBusy(false);return;
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
  return <section className="panel"><form className="form" onSubmit={submit}><label>Hosting price<select name="price_id">{m.prices.filter(p=>p.unit==='hour'&&p.term==='on_demand'&&p.id.startsWith('azure-')).map(p=><option key={p.id} value={p.id}>{p.sku} / ${p.usd} per hour</option>)}</select></label><label>Model size class<select name="model_size_class"><option value="small">Small</option><option value="medium">Medium</option><option value="large">Large</option></select></label><label>Compare hosting<select name="hosting_option"><option value="all">All options</option><option value="azure">Azure</option><option value="aws">AWS</option><option value="model_api">Model APIs</option></select></label><label>Input tokens per request<input name="tokens_in_per_request" type="number" min="0" max="1000000" defaultValue="1000" required/></label><label>Output tokens per request<input name="tokens_out_per_request" type="number" min="0" max="1000000" defaultValue="250" required/></label><label>Cached input fraction<input name="cached_input_fraction" type="number" min="0" max="1" step="0.01" defaultValue="0" required/></label><label>Requests per day<input name="requests_per_day" type="number" min="0" max="100000000" defaultValue="100000" required/></label><label>Seconds per request<input name="seconds_per_request" type="number" step="0.001" min="0.001" max="3600" defaultValue="0.1" required/></label><label>Capacity per replica<input name="capacity_per_replica" type="number" min="1" max="1000000" defaultValue="1" required/></label><label>Minimum replicas<input name="minimum_replicas" type="number" min="0" max="10000" defaultValue="1" required/></label><label>Days<input name="days" type="number" min="1" max="366" defaultValue="30" required/></label><button disabled={busy} type="submit">{busy?'Checking and calculating...':'Calculate workload cost'}</button></form><div aria-live="polite"><p className="notice mt-6">{notice||'Estimates use documented list prices and caller-supplied throughput.'}</p>{result&&<><div className="metrics"><div className="metric"><div className="label">Shadow estimate</div><strong>${Number(result.shadow_cost_usd).toFixed(2)}</strong><small>{result.days} {result.days===1?'day':'days'}</small></div><div className="metric"><div className="label">Replicas</div><strong>{result.replicas}</strong></div><div className="metric"><div className="label">Measured request shadow cost</div><strong>{result.meter?'$'+result.meter:'Not measured'}</strong></div></div>{result.options&&result.options.length>0&&<div className="table-wrap"><table><caption>Hosting comparison at the locked snapshot</caption><thead><tr><th scope="col">Option</th><th scope="col">Cost USD</th><th scope="col">Token components USD</th></tr></thead><tbody>{result.options.map(option=><tr key={option.option}><td>{option.option}</td><td>${Number(option.cost_usd).toFixed(2)}</td><td>{option.components_usd?Object.entries(option.components_usd).map(([key,value])=>key+": $"+Number(value).toFixed(4)).join("; "):"Instance only"}</td></tr>)}</tbody></table></div>}{result.id&&<p className="small">Saved reference: {result.id}</p>}</>}</div></section>;
}

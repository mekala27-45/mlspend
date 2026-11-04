'use client';
import {useRef,useState,type FormEvent} from 'react';

const api=process.env.NEXT_PUBLIC_API_URL??'https://mlspend.vercel.app';
type Decision={accepted:boolean;reason:string;remaining_after_micro:number;forecast_micro:number;replayed:boolean};

export default function GuardrailForm(){
  const [budget,setBudget]=useState<string|null>(null),[busy,setBusy]=useState(false),[message,setMessage]=useState(''),[decision,setDecision]=useState<Decision|null>(null);
  const pending=useRef<{request_id:string;price_id:string;gpu_count:number;hours:string;attempts:number}|null>(null);
  async function start(){
    setBusy(true);setMessage('');
    try{
      const response=await fetch(api+'/v1/simulation/budgets',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({limit_usd:'100'}),signal:AbortSignal.timeout(20000)});
      const data=await response.json();if(!response.ok)throw new Error(typeof data.detail==='string'?data.detail:'The budget service is unavailable.');
      setBudget(data.id);setDecision(null);pending.current=null;
    }catch(error){setMessage(error instanceof Error?error.message:'The budget service is unavailable.');}
    finally{setBusy(false);}
  }
  async function submit(event:FormEvent<HTMLFormElement>){
    event.preventDefault();if(!budget)return;
    const form=new FormData(event.currentTarget);
    if(!pending.current)pending.current={request_id:crypto.randomUUID(),price_id:String(form.get('price')),gpu_count:Number(form.get('gpus')),hours:String(form.get('hours')),attempts:Number(form.get('attempts'))};
    setBusy(true);setMessage('');
    try{
      const response=await fetch(api+'/v1/simulation/budgets/'+budget+'/admissions',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(pending.current),signal:AbortSignal.timeout(20000)});
      const data=await response.json();
      if(typeof data.accepted!=='boolean')throw new Error(typeof data.detail==='string'?data.detail:'Admission status is unknown. Retry the same request.');
      setDecision(data);pending.current=null;
    }catch{setMessage('Admission status is unknown. Retry to recover the same request without reserving twice.');}
    finally{setBusy(false);}
  }
  return <section aria-labelledby="guardrail-heading"><h2 id="guardrail-heading">Try the training budget guardrail</h2><p>This creates an isolated $100 simulation budget. Accepted requests reserve their forecast cost. No job is launched and no money is charged.</p>{!budget?<button disabled={busy} onClick={start}>{busy?'Creating budget...':'Create simulation budget'}</button>:<form onSubmit={submit}><fieldset disabled={busy||pending.current!==null}><legend>Training request</legend><label>GPU price<select name="price" defaultValue="azure-t4"><option value="azure-t4">T4</option><option value="azure-a100">A100</option><option value="azure-v100">V100</option></select></label><label>GPUs<input name="gpus" type="number" min="1" max="128" defaultValue="1" required/></label><label>Hours per attempt<input name="hours" type="number" min="0.000001" max="720" step="0.000001" defaultValue="1" required/></label><label>Attempts including retries<input name="attempts" type="number" min="1" max="100" defaultValue="1" required/></label></fieldset><button disabled={busy} type="submit">{busy?'Checking request...':pending.current?'Recover admission decision':'Check and reserve forecast cost'}</button></form>}<p role="status" aria-live="polite">{message}</p>{decision&&<div role="status"><strong>{decision.accepted?'Accepted for simulation':'Refused'}</strong><p>{decision.reason}. Forecast ${(decision.forecast_micro/1e6).toFixed(2)}. Remaining ${(decision.remaining_after_micro/1e6).toFixed(2)}.</p></div>}<p className="small">The forecast uses the locked hourly rate, requested GPUs, hours and all attempts. It excludes storage, network and runtime overruns.</p></section>;
}

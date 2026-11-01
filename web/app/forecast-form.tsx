'use client';
import {useState,type FormEvent} from 'react';
export default function ForecastForm(){
  const [notice,setNotice]=useState('A forecast must target a future month. It cannot be scored until actual usage is complete.'),[busy,setBusy]=useState(false);
  async function submit(event:FormEvent<HTMLFormElement>){
    event.preventDefault();setBusy(true);const values=new FormData(event.currentTarget);
    const payload=Object.fromEntries(values.entries());
    try{
      const response=await fetch((process.env.NEXT_PUBLIC_API_URL||'')+'/v1/forecasts',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload),signal:AbortSignal.timeout(20000)});
      const body=await response.json();
      if(!response.ok)throw Error(typeof body.detail==='string'?body.detail:'The forecast was rejected');
      if(typeof body.id!=='string')throw Error('No saved reference was returned');
      setNotice('Future forecast saved. Reference: '+body.id+'. Scoring remains pending until the period closes and actuals are available.');
    }catch(error){setNotice((error instanceof Error?error.message:'Request failed')+'. A timed-out save has an unknown status and is not repeated automatically.');}
    finally{setBusy(false);}
  }
  return <section className="panel"><h2>Log a future forecast</h2><p>These records are separate from the historical synthetic backtest.</p><form className="form" onSubmit={submit}><label>Book<select name="book"><option value="portfolio">Public portfolio</option><option value="platform">Simulated platform scenario</option></select></label><label>Team or project<input name="team" defaultValue="mlspend" maxLength={80} required/></label><label>Future month<input name="period" type="month" required/></label><label>Data cutoff<input name="data_cutoff" type="date" required/></label><label>Point USD<input name="point_usd" type="number" min="0" step="0.01" required/></label><label>Lower USD<input name="lower_usd" type="number" min="0" step="0.01" required/></label><label>Upper USD<input name="upper_usd" type="number" min="0" step="0.01" required/></label><button type="submit" disabled={busy}>{busy?'Saving...':'Save future forecast'}</button></form><p className="notice" aria-live="polite">{notice}</p></section>;
}

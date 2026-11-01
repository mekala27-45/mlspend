'use client';
import Link from 'next/link';
import {useEffect,useState,type ReactNode} from 'react';
import source from '../expanded.json';
import {routes} from './routes';
import EstimateForm from './estimate';
import Query from './query';
import ForecastForm from './forecast-form';

type Section={title:string;note:string;headers:string[];rows:(string|number|boolean|null)[][]};
type Page={title:string;intro:string;limit:string;sections:Section[]};
const pages:Record<string,Page>=source.pages;
function Table({section}:{section:Section}){
  return <section><div className="section-head"><div><h2>{section.title}</h2>{section.note&&<p>{section.note}</p>}</div></div><div className="table-wrap" tabIndex={0} role="region" aria-label={section.title+' table; scroll horizontally if needed'}><table><thead><tr>{section.headers.map(h=><th key={h} scope="col">{h}</th>)}</tr></thead><tbody>{section.rows.map((row,i)=><tr key={i}>{row.map((cell,j)=><td key={j}>{cell===null?'Not measured':String(cell)}</td>)}</tr>)}</tbody></table></div></section>;
}
function Metric({label,value,children}:{label:string;value:string;children?:ReactNode}){return <div className="metric"><div className="label">{label}</div><strong>{value}</strong><small>{children}</small></div>;}
function StatementChart(){
  const rows=source.allocations.filter(r=>r.month===source.latest_month),max=Math.max(...rows.map(r=>r.methods.usage));
  return <div className="chart"><svg role="img" aria-label="Direct and allocated costs by team; exact values follow in the table" viewBox={`0 0 900 ${rows.length*40+20}`}><defs><pattern id="shared" width="6" height="6" patternUnits="userSpaceOnUse"><path d="M0 6 L6 0" stroke="var(--control)" strokeWidth="2"/></pattern></defs>{rows.map((r,i)=><g key={r.team}><text x="0" y={i*40+24}>{r.team}</text><rect x="130" y={i*40+10} width={r.direct_micro/max*650} height="18" fill="var(--blue)"/><rect x={130+r.direct_micro/max*650} y={i*40+10} width={(r.methods.usage-r.direct_micro)/max*650} height="18" fill="url(#shared)"/><text x="900" y={i*40+24} textAnchor="end">${(r.methods.usage/1e6).toFixed(2)}</text></g>)}</svg></div>;
}
export default function Ledger({route}:{route:string}){
  const [dark,setDark]=useState(false);
  useEffect(()=>{try{setDark(localStorage.getItem('mlspend-theme')==='dark');}catch{}},[]);
  useEffect(()=>{document.documentElement.classList.toggle('dark',dark);},[dark]);
  function toggle(){setDark(!dark);try{localStorage.setItem('mlspend-theme',!dark?'dark':'light');}catch{}}
  const page=pages[route]??pages.statement;
  return <><a href="#main" className="skip">Skip to content</a><div className="shell"><aside><Link prefetch={false} href="/" className="brand">mlspend<span>THE COST LEDGER</span></Link><div className="edition">PORTFOLIO DEMONSTRATION<br/>EXPANDED STUDY</div><nav aria-label="Main navigation">{routes.map(([id,label],i)=><Link key={id} prefetch={false} href={id==='statement'?'/':'/'+id+'/'} aria-current={id===route?'page':undefined}><span>{String(i+1).padStart(2,'0')}</span>{label}</Link>)}</nav><div className="aside-bottom"><p>Data stays inspectable</p><button onClick={toggle}>{dark?'Use paper copy':'Use carbon copy'}</button></div></aside><div className="paper"><header><span>ML PLATFORM / FINOPS</span><span>SIMULATED STATEMENT · {source.latest_month}</span></header><main id="main" tabIndex={-1}><div className="kicker">{routes.find(r=>r[0]===route)?.[1]??'Statement'}</div><h1>{page.title}</h1><p className="intro">{page.intro}</p>{route==='statement'&&<><span className="status">Simulated costs / public list-price snapshot</span><div className="metrics"><Metric label="Monthly effective cost" value={source.metrics.effective}>{source.latest_month}</Metric><Metric label="Idle capacity" value={source.metrics.idle}>Visible before allocation</Metric><Metric label="Portfolio CI subtotal" value={source.metrics.portfolio}>Known priced components only</Metric></div><StatementChart/></>}{route==='estimate'&&<EstimateForm/>}{route==='forecast'&&<ForecastForm/>}{page.sections.map(s=><Table key={s.title} section={s}/>)}{route==='data'&&<><Query/><details><summary>Provider source URLs</summary>{source.sources.map(url=><p key={url} className="small source-link"><a href={url} rel="noreferrer" target="_blank">{url}</a></p>)}</details></>}{route==='playbook'&&source.guides.map(guide=><details key={guide.path}><summary>{guide.path}</summary><pre>{guide.content}</pre></details>)}{route==='report'&&<button onClick={()=>window.print()}>Print the briefing</button>}<div className="pushback"><strong>Limits and the question to ask</strong><p>{page.limit}</p></div></main><footer>{source.statement}<div className="page-links"><a href="https://github.com/mekala27-45/mlspend">Source repository</a><a href="https://github.com/mekala27-45/mlspend/blob/main/RESULTS.md">Verification and limits</a></div></footer></div></div></>;
}

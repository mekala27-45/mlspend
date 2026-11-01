'use client';
import source from '../expanded.json';
const colors=['var(--ochre)','var(--red)','var(--blue)','var(--control)','var(--purple)'];
export function AllocationChart(){
 const rows=source.allocations.filter(r=>r.month===source.latest_month),methods=['even','direct','usage','custom','shapley'] as const;
 const maximum=Math.max(...rows.flatMap(r=>methods.map(k=>r.methods[k])));
 return <section><h2>One bill, five positions</h2><p className="small">Each point is a policy; the hollow point is the capacity Shapley reference. Exact values follow.</p><div className="chart"><svg role="img" aria-label="Allocation policies by team; exact values in the following table" viewBox={`0 0 900 ${rows.length*48+55}`}>{rows.map((r,i)=><g key={r.team}><text x="0" y={i*48+24}>{r.team}</text><line x1="135" x2="885" y1={i*48+20} y2={i*48+20} stroke="var(--rules)"/>{methods.map((k,j)=><circle key={k} cx={135+r.methods[k]/maximum*740} cy={i*48+20} r={k==='usage'?7:5} fill={k==='shapley'?'var(--card)':colors[j]} stroke={colors[j]} strokeWidth="2"><title>{`${k}: $${(r.methods[k]/1e6).toFixed(2)}`}</title></circle>)}</g>)}{methods.map((k,j)=><g key={k}><circle cx={140+j*145} cy={rows.length*48+20} r="5" fill={k==='shapley'?'var(--card)':colors[j]} stroke={colors[j]} strokeWidth="2"/><text x={152+j*145} y={rows.length*48+24}>{k}</text></g>)}</svg></div></section>;
}
export function IncidentChart(){
 const events=source.charts.incidents,first=Date.parse(source.charts.holdout_start),last=Date.parse(source.charts.holdout_end);
 const x=(value:string)=>190+(Date.parse(value)-first)/(last-first)*680;
 return <section><h2>The held-out incident calendar</h2><p className="small">Bars show incident windows; circles mark the first alert. A coincident start and alert is a synthetic boundary result.</p><div className="chart"><svg role="img" aria-label="Incident windows and first alert timestamps; details follow in the table" viewBox={`0 0 900 ${events.length*42+45}`}>{events.map((r,i)=><g key={r.id}><text x="0" y={i*42+24}>{r.id}</text><line x1="190" x2="880" y1={i*42+20} y2={i*42+20} stroke="var(--rules)"/><rect x={x(r.start)} y={i*42+13} width={Math.max(3,x(r.end)-x(r.start))} height="14" fill="var(--red)"/>{r.first_alert&&<circle cx={x(r.first_alert)} cy={i*42+20} r="5" fill="var(--card)" stroke="var(--blue)" strokeWidth="3"/>}</g>)}<text x="190" y={events.length*42+22}>Holdout begins</text><text x="880" y={events.length*42+22} textAnchor="end">Holdout ends</text></svg></div></section>;
}
export function ForecastChart(){
 const f=source.charts.forecast,rows=f.rows,max=Math.max(...rows.flatMap(r=>[r.actual,r.upper]));
 const point=(i:number,value:number)=>`${45+i/(rows.length-1)*820},${240-value/max*210}`;
 const band=[...rows.map((r,i)=>point(i,r.upper)),...rows.map((_,j)=>{const i=rows.length-1-j;return point(i,rows[i].lower);})].join(' ');
 return <section><h2>{f.key} / direct daily spend</h2><p className="small">Solid: actual. Dashed: forecast. Shading: nominal interval. USD; all dates are in the synthetic held-out calendar.</p><div className="chart"><svg role="img" aria-label="Daily actual spend, forecast and uncertainty band" viewBox="0 0 900 285"><polygon points={band} fill="var(--blue)" opacity=".13"/><polyline points={rows.map((r,i)=>point(i,r.actual)).join(' ')} fill="none" stroke="var(--blue)" strokeWidth="2"/><polyline points={rows.map((r,i)=>point(i,r.point)).join(' ')} fill="none" stroke="var(--red)" strokeWidth="2" strokeDasharray="6 4"/><text x="0" y="30">${max.toFixed(0)}</text><text x="0" y="242">$0</text><text x="45" y="270">{rows[0].date}</text><text x="865" y="270" textAnchor="end">{rows[rows.length-1].date}</text></svg></div></section>;
}

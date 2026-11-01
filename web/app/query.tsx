'use client';
import { useState } from 'react';
import m from '../data.json';
export default function Query() {
  const [query,setQuery]=useState("SELECT month, SUM(effective_micro) / 1000000.0 AS simulated_usd FROM monthly GROUP BY month ORDER BY month");
  const [output,setOutput]=useState('');
  const [busy,setBusy]=useState(false);
  async function run() {
    setBusy(true);setOutput('Loading the local query engine...');
    let db: import('@duckdb/duckdb-wasm').AsyncDuckDB | undefined;
    let connection: import('@duckdb/duckdb-wasm').AsyncDuckDBConnection | undefined;
    try {
      const duckdb=await import('@duckdb/duckdb-wasm');
      const base=(process.env.NEXT_PUBLIC_BASE_PATH||'')+'/duckdb/';
      const bundle=await duckdb.selectBundle({mvp:{mainModule:base+'duckdb-mvp.wasm',mainWorker:base+'duckdb-browser-mvp.worker.js'},eh:{mainModule:base+'duckdb-eh.wasm',mainWorker:base+'duckdb-browser-eh.worker.js'}});
      if(!bundle.mainWorker)throw Error('No compatible query worker');
      db=new duckdb.AsyncDuckDB(new duckdb.VoidLogger(),new Worker(bundle.mainWorker));
      await db.instantiate(bundle.mainModule,bundle.pthreadWorker);
      await db.registerFileText('monthly.json',JSON.stringify(m.monthly));
      await db.registerFileText('allocation.json',JSON.stringify(m.allocation));
      connection=await db.connect();
      await connection.query("CREATE TABLE monthly AS SELECT * FROM read_json_auto('monthly.json'); CREATE TABLE allocation AS SELECT * FROM read_json_auto('allocation.json')");
      const result=await connection.query(query);
      setOutput(JSON.stringify(result.toArray().map(row=>row.toJSON()),(_,value)=>typeof value==='bigint'?value.toString():value,2));
    } catch(error) {setOutput(error instanceof Error?error.message:'Query failed');}
    finally {await connection?.close();await db?.terminate();setBusy(false);}
  }
  return <section><h2>Query the shipped results</h2><p className="small">DuckDB runs in your browser. Tables: monthly and allocation. The platform figures are simulated.</p><label htmlFor="local-sql">SQL</label><textarea id="local-sql" className="query" value={query} onChange={e=>setQuery(e.target.value)}/><button disabled={busy} onClick={run}>Run SQL locally</button><pre aria-live="polite">{output}</pre></section>;
}

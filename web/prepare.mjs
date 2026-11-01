import { copyFile, mkdir } from 'node:fs/promises';
import { resolve } from 'node:path';
await mkdir('public/duckdb', { recursive: true });
for (const name of ['duckdb-mvp.wasm', 'duckdb-eh.wasm', 'duckdb-browser-mvp.worker.js', 'duckdb-browser-eh.worker.js']) {
  await copyFile(resolve('node_modules/@duckdb/duckdb-wasm/dist', name), resolve('public/duckdb', name));
}
await copyFile('data.json', 'public/data.json');

await copyFile("expanded.json", "public/expanded.json");

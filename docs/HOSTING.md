# Hosting and verification

The [dashboard](https://mekala27-45.github.io/mlspend/) is a Next.js static export on GitHub Pages. The [API](https://mlspend.vercel.app/health) runs the port-80 Dockerfile.vercel container. The earlier FastAPI-specific deployment is historical evidence, not the current hosting architecture.

## Production

Version 0.1.0 was deployed as `dpl_4Xxg36XfTUx5JVyjhwpGC8nEcKp1` from tested commit `de15f32947ea2d389a63e9b5123bff36c61fc829`. Its health response reports the expanded price digest and generated-observation digest. The runtime login `mlspend_api` can read and append application logs and update the request budget. It cannot migrate the schema. Alembic runs separately with the migration credential. Existing legacy rows were copied without deleting their source tables.

The [hosted check](https://github.com/mekala27-45/mlspend/actions/runs/41265362664) passed against the expanded API. It checks health, showback, unit costs, anomalies, an estimate POST and an independent HTTP readback. Core CI also starts the actual container and reads its saved row through an independent PostgreSQL connection. Independent Neon SQL readback of the latest browser estimate and forecast is preserved in `results/live/independent-readback.json`. That read used the scoped close role through a separate client; the API continues using its restricted runtime role.

The request header prices serialized process CPU time and the maximum of start/end RSS multiplied by request wall time. It includes process baseline memory during the request and excludes process startup and idle lifetime. It is a shadow meter, not provider billing. Health records an instance identifier and process uptime so a first observation is not automatically called a cold start.

## Browser checks

[Pages publication](https://github.com/mekala27-45/mlspend/actions/runs/41739841264) passed static build, strict TypeScript and all route/recovery tests. Checks include desktop and 390-pixel layouts, keyboard access in both themes, required disclosure, a real DuckDB-WASM query, GET readiness retry, offline fallback and uncertain write handling.

The published browser workflow uses Chrome on Windows. [Run 41740056384](https://github.com/mekala27-45/mlspend/actions/runs/41740056384) passed on November 3, 2026, including the real cross-origin POST, persisted forecast, HTTP readback and screen recording. `docs/demo.gif` contains ten seconds of the actual statement, allocation, anomaly and portfolio screens. Earlier measurements remain under `results/live/archive/`; the earlier recovery run 41326226000 is retained as historical evidence.

The recorded no-probe interval was 1208.362 seconds. The first response took 3774.87 ms and reported a new instance with 0.966 seconds of process uptime. Nineteen of the next twenty requests reached previously observed instances: their nearest-rank p50 was 100.41 ms and p99 was 217.43 ms. One first observation of another instance is excluded and remains visible in `results/live/latency-summary.json`. Raw measurements are unchanged in `results/live/browser.json`; its historical `warm` field contains the entire sequence. Network time, database time and uncontrolled public callers remain limitations.

The estimate request exposed a shadow cost of USD 0.000000390839, with the locked CPU and memory price IDs. Both saved IDs were subsequently read from Neon using an independent SQL connection on November 4, 2026. The future December 2026 forecast is an explicitly labeled scenario with an interval, not a statistically calibrated live prediction, and remains pending actuals.

The statement, theme switch and incident chart were also inspected in Ajay's laptop Chrome on October 31, 2026, New York time. The twenty-minute idle measurement and automated route checks were performed in the separate Windows runner.

## Scheduled close

`.github/workflows/close-period.yml` fetches public usage after a completed month and scores matching forecasts atomically. The `mlspend_close` role is restricted to SELECT and UPDATE of `actual_micro` and `scored_at` on the application log. It cannot rewrite forecast payloads or delete rows. The role has been created and its permissions verified. GitHub Actions secrets `MLSPEND_CLOSE_DATABASE_URL` and `MLSPEND_CLOSE_SALT` were configured on November 1, 2026 after specific authorization. They use the scoped close role and a separate random salt; no credential is stored in source. The scheduled job runs at 06:17 UTC on the second of each month. Use a direct, unpooled Neon connection because the storage client sets its schema through the startup `search_path` option. The initial [October close attempt](https://github.com/mekala27-45/mlspend/actions/runs/41328206111) fetched all public usage before the pooler rejected that option. The configured endpoint was corrected without expanding the role permissions; attempts and exact outcomes remain in that run. See the [Neon connection guidance](https://neon.com/docs/connect/connection-errors#unsupported-startup-parameter). The December 2026 scenario remains unscored until complete December actuals can be fetched in January 2027. Never paste either value into a chat, issue or source file.

## Recheck

Run `uv run python -m scripts.check_hosted --url https://mlspend.vercel.app` from an environment with outbound HTTPS. Run Build and verify for real PostgreSQL, container persistence, notebook execution, strict typing, lint and coverage. Run the full expanded study for two independent hash seeds and LibreOffice formula recalculation. See RESULTS.md for the release boundary and unresolved source gaps.

## Prospective simulation

[Run 41475604592](https://github.com/mekala27-45/mlspend/actions/runs/41475604592) passed issuance, independent SQL readback, outcome generation, close, HTTP score readback and idempotency. The exact artifacts are in `results/prospective/`; their numeric results are rendered in RESULTS.md and the forecast page. The API stores these as `simulation_forecast` records with a registered plan digest and simulation ID. The real calendar close never selects them. See [the sequence and limitations](PROSPECTIVE.md).

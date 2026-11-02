# Hosting and verification

The [dashboard](https://mekala27-45.github.io/mlspend/) is a Next.js static export on GitHub Pages. The [API](https://mlspend.vercel.app/health) runs the port-80 Dockerfile.vercel container. The earlier FastAPI-specific deployment is historical evidence, not the current hosting architecture.

## Production

The explicit simulation clock was deployed as `dpl_CEx77f8Mjnp1w1VXZJD9kiqh1jEN` from tested commit `f32fb3af116057ef2fb7be33d9c6937eb3267a63`. Its health response reports the expanded price digest and generated-observation digest. The runtime login `mlspend_api` can read and append application logs and update the request budget. It cannot migrate the schema. Alembic runs separately with the migration credential. Existing legacy rows were copied without deleting their source tables.

The [hosted check](https://github.com/mekala27-45/mlspend/actions/runs/41265362664) passed against the expanded API. It checks health, showback, unit costs, anomalies, an estimate POST and an independent HTTP readback. Core CI also starts the actual container and reads its saved row through an independent PostgreSQL connection. Independent Neon SQL readback of the latest browser estimate and forecast is preserved in `results/live/independent-readback.json`. That read used the owner connection through a separate client; the API continues using its restricted runtime role.

The request header prices serialized process CPU time and the maximum of start/end RSS multiplied by request wall time. It includes process baseline memory during the request and excludes process startup and idle lifetime. It is a shadow meter, not provider billing. Health records an instance identifier and process uptime so a first observation is not automatically called a cold start.

## Browser checks

[Pages publication](https://github.com/mekala27-45/mlspend/actions/runs/41267291250) passed static build, strict TypeScript and all route/recovery tests. Checks include desktop and 390-pixel layouts, keyboard access in both themes, required disclosure, a real DuckDB-WASM query, GET readiness retry, offline fallback and uncertain write handling.

The published browser workflow uses Chrome on Windows. The test in [run 41267361547](https://github.com/mekala27-45/mlspend/actions/runs/41267361547) passed; its final evidence-branch push failed because main had advanced its workflow files. [Recovery run 41326226000](https://github.com/mekala27-45/mlspend/actions/runs/41326226000) preserved the exact uploaded artifact against current main without rerunning or inventing a test. `docs/demo.gif` contains ten seconds of the actual statement, allocation, anomaly and portfolio screens.

The recorded no-probe interval was 1215.795 seconds. The first response took 7389.90 ms and reported a new instance with 1.288 seconds of process uptime. The next twenty requests reached five instances, so calling all twenty warm would be inaccurate. Sixteen reached previously observed instances: their nearest-rank p50 was 119.42 ms and p99 was 251.03 ms. Four first observations are excluded and remain visible in `results/live/latency-summary.json`. Raw measurements are unchanged in `results/live/browser.json`; its historical `warm` field contains the entire sequence. Network time, database time and uncontrolled public callers remain limitations.

The estimate request exposed a shadow cost of USD 0.000000507492, with the locked CPU and memory price IDs. Both saved IDs were subsequently read from Neon using an independent SQL connection. The future December 2026 forecast is an explicitly labeled scenario with an interval, not a statistically calibrated live prediction, and remains pending actuals.

The statement, theme switch and incident chart were also inspected in Ajay's laptop Chrome on October 31, 2026, New York time. The twenty-minute idle measurement and automated route checks were performed in the separate Windows runner.

## Scheduled close

`.github/workflows/close-period.yml` fetches public usage after a completed month and scores matching forecasts atomically. The `mlspend_close` role is restricted to SELECT and UPDATE of `actual_micro` and `scored_at` on the application log. It cannot rewrite forecast payloads or delete rows. The role has been created and its permissions verified. GitHub Actions secrets `MLSPEND_CLOSE_DATABASE_URL` and `MLSPEND_CLOSE_SALT` were configured on November 1, 2026 after specific authorization. They use the scoped close role and a separate random salt; no credential is stored in source. The scheduled job runs at 06:17 UTC on the second of each month. Use a direct, unpooled Neon connection because the storage client sets its schema through the startup `search_path` option. The initial [October close attempt](https://github.com/mekala27-45/mlspend/actions/runs/41328206111) fetched all public usage before the pooler rejected that option. The configured endpoint was corrected without expanding the role permissions; attempts and exact outcomes remain in that run. See the [Neon connection guidance](https://neon.com/docs/connect/connection-errors#unsupported-startup-parameter). The December 2026 scenario remains unscored until complete December actuals can be fetched in January 2027. Never paste either value into a chat, issue or source file.

## Recheck

Run `uv run python -m scripts.check_hosted --url https://mlspend.vercel.app` from an environment with outbound HTTPS. Run Build and verify for real PostgreSQL, container persistence, notebook execution, strict typing, lint and coverage. Run the full expanded study for two independent hash seeds and LibreOffice formula recalculation. See RESULTS.md for the release boundary and unresolved source gaps.

## Prospective simulation

[Run 41475604592](https://github.com/mekala27-45/mlspend/actions/runs/41475604592) passed issuance, independent SQL readback, outcome generation, close, HTTP score readback and idempotency. The exact artifacts are in `results/prospective/`; their numeric results are rendered in RESULTS.md and the forecast page. The API stores these as `simulation_forecast` records with a registered plan digest and simulation ID. The real calendar close never selects them. See [the sequence and limitations](PROSPECTIVE.md).

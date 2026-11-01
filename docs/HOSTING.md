# Hosting and verification

The [dashboard](https://mekala27-45.github.io/mlspend/) is a Next.js static export on GitHub Pages. The [API](https://mlspend.vercel.app/health) runs the port-80 Dockerfile.vercel container. The earlier FastAPI-specific deployment is historical evidence, not the current hosting architecture.

## Production

Production deployment `dpl_C7BmktvDnWUgmdRLWbZXgtZtzPWm` was built from `913fd26c9ebd30c168b44038557c674317f5635d`. Its health response reports the expanded price digest and generated-observation digest. The runtime login `mlspend_api` can read and append application logs and update the request budget. It cannot migrate the schema. Alembic runs separately with the migration credential. Existing legacy rows were copied without deleting their source tables.

The [hosted check](https://github.com/mekala27-45/mlspend/actions/runs/41265362664) passed against the expanded API. It checks health, showback, unit costs, anomalies, an estimate POST and an independent HTTP readback. Core CI also starts the actual container and reads its saved row through an independent PostgreSQL connection. Independent Neon SQL readback of the latest browser estimate and forecast is preserved in `results/live/independent-readback.json`. That read used the owner connection through a separate client; the API continues using its restricted runtime role.

The request header prices serialized process CPU time and the maximum of start/end RSS multiplied by request wall time. It includes process baseline memory during the request and excludes process startup and idle lifetime. It is a shadow meter, not provider billing. Health records an instance identifier and process uptime so a first observation is not automatically called a cold start.

## Browser checks

[Pages publication](https://github.com/mekala27-45/mlspend/actions/runs/41267291250) passed static build, strict TypeScript and all route/recovery tests. Checks include desktop and 390-pixel layouts, keyboard access in both themes, required disclosure, a real DuckDB-WASM query, GET readiness retry, offline fallback and uncertain write handling.

The published browser workflow uses Chrome on Windows. The test in [run 41267361547](https://github.com/mekala27-45/mlspend/actions/runs/41267361547) passed; its final evidence-branch push failed because main had advanced its workflow files. [Recovery run 41326226000](https://github.com/mekala27-45/mlspend/actions/runs/41326226000) preserved the exact uploaded artifact against current main without rerunning or inventing a test. `docs/demo.gif` contains ten seconds of the actual statement, allocation, anomaly and portfolio screens.

The recorded no-probe interval was 1215.795 seconds. The first response took 7389.90 ms and reported a new instance with 1.288 seconds of process uptime. The next twenty requests reached five instances, so calling all twenty warm would be inaccurate. Sixteen reached previously observed instances: their nearest-rank p50 was 119.42 ms and p99 was 251.03 ms. Four first observations are excluded and remain visible in `results/live/latency-summary.json`. Raw measurements are unchanged in `results/live/browser.json`; its historical `warm` field contains the entire sequence. Network time, database time and uncontrolled public callers remain limitations.

The estimate request exposed a shadow cost of USD 0.000000507492, with the locked CPU and memory price IDs. Both saved IDs were subsequently read from Neon using an independent SQL connection. The future December 2026 forecast is an explicitly labeled scenario with an interval, not a statistically calibrated live prediction, and remains pending actuals.

The statement, theme switch and incident chart were also inspected in Ajay's laptop Chrome on October 31, 2026, New York time. The twenty-minute idle measurement and automated route checks were performed in the separate Windows runner.

## Scheduled close

`.github/workflows/close-period.yml` fetches public usage after a completed month and scores matching forecasts atomically. The `mlspend_close` role is restricted to SELECT and UPDATE of `actual_micro` and `scored_at` on the application log. It cannot rewrite forecast payloads or delete rows. The role has been created and its permissions verified. Credential transfer to an external secret store was blocked by automatic approval review and remains pending specific authorization. GitHub Actions secrets `MLSPEND_CLOSE_DATABASE_URL` and `MLSPEND_CLOSE_SALT` still require configuration; until then the workflow fails clearly without scoring anything. Never paste either value into a chat, issue or source file.

## Recheck

Run `uv run python -m scripts.check_hosted --url https://mlspend.vercel.app` from an environment with outbound HTTPS. Run Build and verify for real PostgreSQL, container persistence, notebook execution, strict typing, lint and coverage. Run the full expanded study for two independent hash seeds and LibreOffice formula recalculation. See RESULTS.md for the release boundary and unresolved source gaps.

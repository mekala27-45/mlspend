# Decisions

## 2026-11-01: promote observed source evidence

Promoted the Azure Retail Prices API responses from Actions run 41258072383 through scripts/promote_prices.py. Version 2 retains the original book and lock in data/prices/history, verifies each normalized row against its cached response, and records the artifact digest. Consumption rates used by the simulator are unchanged. Reservation totals are normalized over their stated terms and are separate from on-demand estimator choices. GitHub and Vercel remain explicitly labeled public excerpts. This does not establish coverage for AWS, storage, network or model tokens. Source: https://prices.azure.com/api/retail/prices, fetched 2026-11-01 UTC.

Promoted the October public Actions usage from run 41258444649 through scripts/promote_portfolio.py. Repository summaries reconcile to individual jobs and unpriced jobs remain visible. Creation-time filtering and per-job minute rounding are explicit. Current artifact and repository sizes are inventory observations, not storage-month usage. GPU and token ledgers remain separate requirements. Source: https://docs.github.com/en/rest/actions/workflow-jobs, retrieved 2026-11-01 UTC.

## 2026-11-01: static frontend and live API

GitHub Pages hosts the Next.js static export; FastAPI on Vercel persists estimates in Neon. Browser SQL uses self-hosted DuckDB-WASM assets and committed result tables. The npm dependency lock came from the successful Pages build and subsequent builds use npm ci. The reference API keeps its companion static dashboard for direct request verification. An uncertain POST response is reported as unknown and is never automatically retried.

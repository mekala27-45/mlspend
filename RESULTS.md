# Results

mlspend is a portfolio demonstration. Its platform costs are simulated with known truth. Its portfolio costs are shadow estimates of public project usage at published list prices; nobody paid these amounts. No figure is a quote, an invoice or financial advice.

Status: deployed working demonstration; mandatory analytical requirements remain.

## Required checklist

| Requirement | Status | Evidence |
|---|---|---|
| Price book fetched in Actions and locked | Partial | Azure provider responses were fetched in Actions and promoted to version 2 with raw response digests and preserved history. GitHub and Vercel retain labeled excerpts; full provider coverage remains. |
| FOCUS simulator and Foundation validation | Not done | 140160 candidate charge rows exist; official conformance and the full commitment schema remain. |
| Usage from every public build | Partial | CI usage measured; build-ledger coverage reported separately. Repository summaries reconcile to the recorded workflow jobs; GPU, token and API components remain incomplete. |
| Plan registered before held-out scoring | Done | evaluation/registration.json, plan digest ab7b94fbe50dedf382af98d5a433fa87fae4cf86c3887552b7aa04ddcb02e3e4. |
| Warehouse and reconciliation at four grains | Partial | All 140160 source rows reconcile exactly; dbt models and tests pass in Actions. Full FOCUS contracts remain. |
| Allocation alternatives and owner inference | Partial | Four conserved totals and owner scores exist; the fourth is Shapley-weighted overhead. |
| Average and marginal unit costs | Partial | 72 endpoint-month rows; token and experiment components remain. |
| Live Vercel API with logs and meter | Partial | Hosted endpoints and Neon estimate readback pass; see results/hosted-validation.json and docs/HOSTING.md. Full meter calibration remains. |
| Forecasts, budgets and scored log | Partial | 6 team backtests exist; live period close and budget alerts remain. |
| Incident detection and postmortem | Partial | Held-out event recall 100.0%; full incident narrative remains. |
| Counterfactual recommendation scoring | Partial | Commitment curve is measured; recommendation cash savings are intentionally not asserted. |
| Persistence and cold-start measurements | Partial | Hosted estimate persistence and PostgreSQL tests pass. Cold-start distribution measurements remain. |
| Portfolio shadow estimates by output | Not done | No usage was invented. |
| Finance exports and showback | Partial | Statements rendered; export validation is separate. |
| All methods scored with uncertainty | Partial | Statistics utilities exist; full registered hypothesis report remains. |
| Live Pages site and estimator | Partial | Next.js static export is live on GitHub Pages. All routes, mobile widths, themes, recovery and DuckDB queries passed browser tests. Hosted estimator persistence is verified; the forecast-log interface remains. |
| Documentation and repository workflows | Partial | Source brief, runbook and generated documents exist; full notebook and ADR requirements remain. |
| Quality gates, reproducibility and release | Partial | Full CI and repeat-build checks pass at the commit recorded in docs/HOSTING.md. No release tag has been created. |

## Latest statement: 2025-12

| Team | Even | Direct cost | Usage | Shapley-weighted overhead |
|---|---:|---:|---:|---:|
| ads | $1,696.66 | $1,707.35 | $1,589.20 | $1,665.15 |
| assistant | $1,811.82 | $1,850.74 | $1,740.93 | $1,747.59 |
| forecasting | $865.57 | $672.59 | $960.88 | $1,005.03 |
| fraud | $2,336.18 | $2,503.60 | $2,331.44 | $2,456.63 |
| research | $2,482.04 | $2,685.20 | $2,525.94 | $2,567.03 |
| search | $726.02 | $498.83 | $769.91 | $476.88 |
| unallocated | $576.06 | $576.06 | $576.06 | $576.06 |


## Limitations

The Azure compute book is backed by raw API responses fetched in Actions. GitHub and Vercel prices retain explicitly labeled transcribed excerpts. The prior price book is preserved in data/prices/history. AWS, model API, storage and network price coverage remains absent. Every simulation amount is a counterfactual at the recorded price snapshot.

The simulator includes compute incidents only. It does not yet include the brief's storage duplication, network export, actual spot interruption mechanism or midyear provider price changes. Billed and effective costs currently coincide because purchases and amortized commitments are not yet emitted into billing rows. Commitment optimization uses a stated simulated discount, not a purchasable provider offer.

Owner inference requires matching namespace and network metadata. Uncertain resources remain unallocated. Forecasts cover direct team cost, not fully loaded showback. Two forecast candidates are implemented. The detector is a seasonal robust residual detector, without a separate changepoint test. Its development budget limits total alert frequency, not a truth-labeled false positive rate.

Recommendation capacity values must not be presented as actual savings. Counterfactual costs are stored independently, but complete estimated-versus-true recommendation scoring remains. The allocation method comparison uses a capacity model, so it is a sensitivity analysis rather than an objective fairness judgment.

The deployed API serves the static HTML, CSS and JavaScript dashboard. Frontend framework and browser SQL checks are tracked separately from the API deployment. The DuckDB warehouse and dbt models have run in Actions; that does not establish full FOCUS conformance.

## Stretch

Second monthly price fetch, fractional GPUs, carbon estimates, budget guardrail and readback integration: not done.

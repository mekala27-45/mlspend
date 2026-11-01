# MLSpend

Release remains incomplete: Live container API and metering; Forecasts and budgets; Persistence and cold/warm latency; Finance exports; Pages routes and estimator; Quality gates and release. See RESULTS.md for the exact checks and limits.

[Live dashboard](https://mekala27-45.github.io/mlspend/) · [API health](https://mlspend.vercel.app/health) · [Verification and limits](RESULTS.md)

mlspend is a portfolio demonstration. Its platform costs are simulated with known truth. Its portfolio costs are shadow estimates of public project usage at published list prices; nobody paid these amounts. No figure is a quote, an invoice or financial advice.

A cost observability project with a simulated platform book and a measured public-portfolio book. It compares ownership policies, unit economics, forecasts, anomaly detection and whole-platform counterfactuals.


## Study dimensions



| Charges | Hours | Effective cost | Quarantined producer defects |
| --- | --- | --- | --- |
| 589850 | 8760 | $348,535.01 | 10 |

## Run

```sh
uv sync --group dev
uv run python -m scripts.build
uv run python -m scripts.build_expanded
uv run pytest --cov=packages
uv run python -m scripts.check
uv run python -m scripts.serve_local
```

For the Next.js site, run `npm ci` and `npm run dev` inside `web`. Hosted persistence needs the scoped DATABASE_URL and MLSPEND_SALT. Run Alembic with a separate migration credential before serving. No credentials belong in source control.


## Skills and evidence



| Skill | Inspectable evidence |
| --- | --- |
| Deterministic simulation and counterfactuals | packages/simulator; packages/evaluation; evaluation/v2 |
| FOCUS and exact reconciliation | packages/focus; packages/warehouse; warehouse-expanded |
| Allocation and Shapley capacity | packages/allocation; packages/expansion |
| Unit economics and commitments | packages/optimize; exports/expanded |
| Forecasting and detection | packages/forecast; packages/detect |
| Public-source measurement | scripts/fetch_committed_ledgers.py; results/committed-ledgers.json |
| API, migrations and persistence | packages/api; migrations; Dockerfile.vercel |
| Reproducible reporting and browser UI | packages/render; web/app; .github/workflows |

## Interpretation

This independent replication was registered after earlier version results were already known. The added long-term contract is a documented completeness correction. Simulated effects are not production savings. Created for Ajay Mekala with AI assistance.

These are measured public records at shadow prices. Runner-contained work is not charged twice. Missing GPU ledgers, unknown NIM token rates and unmatched Databricks SKUs prevent a complete total. Undated answer evaluations are excluded from the window. No per-refresh or per-answer total is invented from unrelated CI jobs.

See RESULTS.md for validation status, source gaps and release gates. The public price snapshot is a scenario input, not a historical invoice.

## License

Apache-2.0 for project code. Public price and usage records retain their original provider terms; see DATA_SOURCES.md.

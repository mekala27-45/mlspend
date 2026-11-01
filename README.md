# MLSpend

Release remains incomplete: Forecasts and budgets; Quality gates and release. See RESULTS.md for the exact checks and limits.

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
| Cost allocation and showback | packages/allocation; report/statements |
| Kubernetes-style workload, idle and shared cost | warehouse-expanded/models; packages/expansion/analysis.py |
| Fairness in shared cost | packages/allocation/shapley.py; docs/methods/allocation.md |
| Inference, answer and training unit economics | packages/unit; packages/optimize; web/app/charts.tsx |
| FOCUS billing and allocated exports | packages/focus; scripts/validate_full_focus.py |
| Public price data engineering | packages/prices; data/prices/expanded/lock.json |
| dbt and DuckDB warehousing | warehouse-expanded; packages/warehouse |
| Contracts, quarantine and reconciliation | packages/warehouse/expanded.py; tests/test_expanded_pipeline.py |
| Forecasting with intervals | packages/forecast; evaluation/v2/plan.json |
| Budgets and burn alerts | packages/expansion/analysis.py; web/app/forecast-form.tsx |
| Anomaly detection and incident response | packages/detect; docs/incidents/weekend-sweep.md |
| Rightsizing and commitments | packages/optimize; docs/methods/commitments.md |
| Evaluation against sealed truth | packages/evaluation; packages/truth |
| Clustered bootstrap and multiple testing | packages/evaluation/expanded.py; report/briefing.md |
| APIs, migrations and persistent logs | packages/api; migrations; tests/test_api.py |
| BI and finance exports | packages/expansion/exports.py; scripts/verify_workbook.py |
| GitHub API and CI analytics | scripts/fetch_portfolio_usage.py; packages/portfolio |
| Agent-assisted engineering | AGENTS.md; .claude/skills; docs/SPEC.md |
| Technical communication | report/briefing.md; docs/methods; docs/DECISIONS.md |

## Interpretation

This independent replication was registered after earlier version results were already known. The added long-term contract is a documented completeness correction. Simulated effects are not production savings. Created for Ajay Mekala with AI assistance.

These are measured public records at shadow prices. Runner-contained work is not charged twice. Missing GPU ledgers, unknown NIM token rates and unmatched Databricks SKUs prevent a complete total. Undated answer evaluations are excluded from the window. No per-refresh or per-answer total is invented from unrelated CI jobs.

See RESULTS.md for validation status, source gaps and release gates. The public price snapshot is a scenario input, not a historical invoice.

## License

Apache-2.0 for project code. Public price and usage records retain their original provider terms; see DATA_SOURCES.md.

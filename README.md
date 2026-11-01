# mlspend

This build is incomplete against the original brief. Live GitHub Pages, Vercel and Neon deployment, the Actions price and portfolio fetch, Foundation FOCUS validation, the complete recommendation evaluation, Next.js and dbt execution, and the final release checks remain outstanding. RESULTS.md records each requirement separately.

mlspend is a portfolio demonstration. Its platform costs are simulated with known truth. Its portfolio costs are shadow estimates of public project usage at published list prices; nobody paid these amounts. No figure is a quote, an invoice or financial advice.

The local application builds a simulated calendar into hourly source charges, reconciles the warehouse, compares allocation policies and serves the results through a dashboard and FastAPI. The registered plan and the source prices are committed separately from the derived results.

## Measured locally

The simulation generated 140160 charges across 8760 hours. Its recorded total is $124,169.64. The calendar is simulated; the public price snapshot was read later and is applied as a scenario, not a historical invoice.

The largest method change is $471.88 for ads in 2025-10. The detector selected a threshold of 3 and its held-out event recall is 100.0%. These values are rendered from results/manifest.json.

## Run

```sh
uv sync --group dev
uv run python -m scripts.register_plan
uv run python -m scripts.initialize_prices
uv run python -m scripts.build
uv run pytest --cov=packages
uv run python -m scripts.serve_local
```

Open the address printed by the local launcher. The dashboard works from committed results. The local estimator writes to a local SQLite log; hosted use requires DATABASE_URL and MLSPEND_SALT. No cloud credentials belong in source control.

## Evidence map

| Skill | Evidence |
|---|---|
| Allocation and exact Shapley calculation | packages/allocation |
| Average and marginal unit economics | packages/unit |
| Price normalization and provenance | packages/prices, data/prices |
| Deterministic hourly simulation | packages/simulator |
| Warehouse and independent reconciliation | packages/warehouse, warehouse/models |
| Forecasting with empirical intervals | packages/forecast |
| Seasonal residual detection | packages/detect |
| Commitment optimization | packages/optimize |
| Evaluation and multiple comparisons | packages/evaluation |
| API and committed persistence | packages/api |
| Reproducible reporting | packages/render, report/templates |

## Limits

The allocation column named shapley distributes overhead in proportion to exact coalition values. It is not the Shapley allocation of a complete provider invoice. Current recommendations estimate released capacity value, not demonstrated cash savings. Forecast intervals are empirical and may miss their nominal coverage under serial dependence. The API meter allocates request CPU and configured memory; it excludes cold starts and instance lifetime outside a request. The complete limits and pending checks are in RESULTS.md.

## How this was built

This implementation was created for Ajay Mekala with AI assistance. The repository retains its evaluation plan, source evidence, tests, failed checks and measured limitations. No employment system or private employer data was used.

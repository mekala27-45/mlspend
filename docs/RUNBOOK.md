# Running mlspend

The project is a working hosted prototype. See RESULTS.md for incomplete requirements and HOSTING.md for deployment evidence tied to a specific commit. A successful build alone does not establish working persistence.

## Local build

Use Python 3.12 and uv. From the repository root:

```sh
uv sync --group dev
uv run python -m scripts.build
uv run pytest --cov=packages
uv run ruff check packages scripts tests
uv run mypy packages
uv run python -m scripts.check
uv run python -m scripts.serve_local
```

The launcher serves the dashboard at http://127.0.0.1:4173 and the API at http://127.0.0.1:8000. The development database is data/generated/local-api.sqlite. Stop the launcher with Ctrl+C. It creates a new client-hashing salt each launch, so its rate limits are development-only; a hosted installation must keep a stable secret salt.

Do not initialize or edit the registered plan or price lock to make a failed check pass. The build verifies the existing registration. Source fetches write reviewable evidence separately from locked prices.

## Hosted configuration

Vercel uses the FastAPI entry point in index.py, which also serves the dashboard. Configure DATABASE_URL, MLSPEND_SALT and MLSPEND_CORS_ORIGINS on the intended host. The live project uses Neon. Use a separate test database for MLSPEND_TEST_DATABASE_URL. Never commit a database connection string or salt.

The static dashboard uses the local API during development and the same origin on Vercel. A separately hosted dashboard must set its API URL explicitly. The estimator checks readiness, submits once, and reports uncertain persistence if the response is lost. Run the Verify hosted persistence workflow after a deployment; it saves one test estimate and reads it back through an independent HTTP request.

## Data and persistence checks

The simulator produces 16 charge rows per hour. The warehouse compares raw-source billed and effective totals at team, model, month and day grains. All grouping uses UTC. Quarantined rows fail the build instead of being silently dropped.

Run `uv run python -m scripts.check_persistence` to exercise a real local HTTP server and read the committed forecast from a separate Python process. This requires local socket access. A sandbox that blocks sockets cannot run this check. The database-only test in tests/test_sources.py separately proves cross-process SQLite visibility, but does not replace the HTTP or hosted PostgreSQL checks.

Use `uv run python -m scripts.close_period --help` for period closing. Closing requires actuals for every unscored forecast in that period and is atomic. It refuses periods that have not ended. Historical simulation backtests remain separate from future forecast logs.

## Release policy

GitHub Actions has run the full suite with an ephemeral PostgreSQL service and preserved test evidence. A separate workflow fetches Azure price evidence for review without promoting or changing the price lock. Production deployment is an explicit action; passing CI does not create a release tag.

Run the complete suite in an environment with network and local socket access, including the PostgreSQL integration check. Validate the requested external data sources, full analytical requirements and all user-facing flows. Compare full build digests across independent runs. Do not publish a v0.1.0 release until the mandatory checklist is complete.

## Execution constraints recorded during development

The managed laptop session denied outbound DNS and local socket connections. Python's Windows asyncio runner stalled while creating its socket pair, so HTTP transport tests could not complete there. Those tests pass in GitHub Actions, including PostgreSQL request-budget and persistence checks. The connected GitHub, Neon and Vercel tools now provide the deployment access used in HOSTING.md.

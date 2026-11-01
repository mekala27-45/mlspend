# Running mlspend

The project is a working local prototype. See RESULTS.md for requirements that still need implementation or external verification. A successful local build does not establish a successful deployment.

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

The repository includes a container definition for the API. It has not been deployed or verified. Configure DATABASE_URL, MLSPEND_SALT and MLSPEND_CORS_ORIGINS on the intended host. Use a separate test database for MLSPEND_TEST_DATABASE_URL. Never commit a database connection string or salt.

The static dashboard currently uses its local API when served on localhost. Hosted estimator wiring, the requested Next.js implementation, database migrations and deployment automation still need completion before public release.

## Data and persistence checks

The simulator produces 16 charge rows per hour. The warehouse compares raw-source billed and effective totals at team, model, month and day grains. All grouping uses UTC. Quarantined rows fail the build instead of being silently dropped.

Run `uv run python -m scripts.check_persistence` to exercise a real local HTTP server and read the committed forecast from a separate Python process. This requires local socket access. A sandbox that blocks sockets cannot run this check. The database-only test in tests/test_sources.py separately proves cross-process SQLite visibility, but does not replace the HTTP or hosted PostgreSQL checks.

Use `uv run python -m scripts.close_period --help` for period closing. Closing requires actuals for every unscored forecast in that period and is atomic. It refuses periods that have not ended. Historical simulation backtests remain separate from future forecast logs.

## Release policy

The prepared GitHub Actions workflows run the full suite with an ephemeral PostgreSQL service and preserve test evidence. A separate manual workflow fetches Azure price evidence for review without promoting or changing the price lock. These workflows have not run. There is no automatic production deployment or release step.

Run the complete suite in an environment with network and local socket access, including the PostgreSQL integration check. Validate the requested external data sources, full analytical requirements and all user-facing flows. Compare full build digests across independent runs. Do not publish a v0.1.0 release until the mandatory checklist is complete.

## Execution constraints recorded during development

The managed laptop session denied outbound DNS and local socket connections. Python's Windows asyncio runner also stalled while creating its socket pair, so HTTP transport tests could not complete there. The API tests remain in the suite with a timeout; they were not converted to passing stubs. Neon and Vercel plugins were enabled, but authenticated account tools were not exposed. The intended GitHub repository returned 404 and the browser was still on GitHub's sign-in page.

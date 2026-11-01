# Working on mlspend

Use Python 3.12 and the dependencies in pyproject.toml. Run `uv sync --group dev`, `uv run pytest --cov=packages`, `uv run ruff check .`, and `uv run mypy packages`. If the environment blocks local sockets, record that limitation and select the core, method, pipeline, source and direct storage tests explicitly. Do not report that subset as a complete suite pass.

Keep money in Decimal at boundaries and integer microdollars in stored telemetry. Never claim observed usage or current prices from a fixture. Preserve the distinction between simulated cost, shadow cost and actual charges.

Do not edit locked prices, source locks, evaluation registration or generated results by hand. The first initialization uses the registration and fetch commands. Later changes use an explicit new version and explain the reason. Render documents from the manifest. A missing source is a missing source, never zero usage.

The simulator writes truth separately. Only evaluation may load truth. Method modules must use observed telemetry only. Run the import boundary test after changing methods.

Before release, run the local build twice and compare digests, then run the external checks. A skipped check is not a pass. Do not tag a complete release while any mandatory requirement in RESULTS.md is not done.

The expanded implementation is registered in evaluation/v2/plan.json. Run `uv run python -m scripts.build_expanded` for the contracted full-year study and `uv run python -m packages.render.expanded` for its public claims. Run `uv run python -m scripts.check_expanded_reproducibility` for independent process rebuilds with different hash seeds. The earlier study remains preserved for provenance.

Use `.claude/skills/add-a-price-source`, `add-a-cost-rule` and `explain-a-bill` for their named tasks. Validate all three with skills-ref. Run notebooks with `uv run pytest --nbmake notebooks`. The playbook renders these repository instructions.

Protect uv.lock, web/package-lock.json, all source locks and price books, evaluation registrations, sealed truth and results promoted from Actions. Use dependency tooling, explicit source promotion or deterministic rendering to change them. Never silently alter a source artifact or a threshold after looking at holdout results.

Run `uv run python -m scripts.check_diff` on staged or committed changes before publication. It checks added text for credentials and private identifiers. The pre-push hook runs the same check. Review the full renderer, registration, statement, price-lock, vocabulary, palette and method-boundary gates in CI. Missing input to a gate fails closed.

Use the migration credential for `uv run alembic upgrade head`; the runtime role must not create tables. Period-close needs explicit complete actuals and a separate writer credential. Never log or commit database URLs with passwords. An unavailable future actual remains pending rather than becoming zero.

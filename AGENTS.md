# Working on mlspend

Use Python 3.12 and the dependencies in pyproject.toml. Run `uv sync --group dev`, `uv run pytest --cov=packages`, `uv run ruff check .`, and `uv run mypy packages`. If the environment blocks local sockets, record that limitation and select the core, method, pipeline, source and direct storage tests explicitly. Do not report that subset as a complete suite pass.

Keep money in Decimal at boundaries and integer microdollars in stored telemetry. Never claim observed usage or current prices from a fixture. Preserve the distinction between simulated cost, shadow cost and actual charges.

Do not edit locked prices, source locks, evaluation registration or generated results by hand. The first initialization uses the registration and fetch commands. Later changes use an explicit new version and explain the reason. Render documents from the manifest. A missing source is a missing source, never zero usage.

The simulator writes truth separately. Only evaluation may load truth. Method modules must use observed telemetry only. Run the import boundary test after changing methods.

Before release, run the local build twice and compare digests, then run the external checks. A skipped check is not a pass. Do not tag a complete release while any mandatory requirement in RESULTS.md is not done.

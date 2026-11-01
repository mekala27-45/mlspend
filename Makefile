setup:
	uv sync --group dev

build:
	uv run python -m scripts.build
	uv run python -m scripts.build_expanded
	uv run python -m packages.render.expanded

check:
	uv run ruff check packages scripts tests
	uv run mypy packages
	uv run pytest --cov=packages
	uv run python -m scripts.check

rederive:
	uv run python -m scripts.check_expanded_reproducibility

serve:
	uv run python -m scripts.serve_local

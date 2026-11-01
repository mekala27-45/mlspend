# Delivered file inventory

Base source snapshot: `98fda8a2c2211412c13354685773ac7ab789266d`, plus the full FOCUS evidence promoted from run 41327002636 in this documentation update. Large datasets and finance binaries remain reproducible Actions artifacts. Working environments and caches are excluded.

## .claude

| File |
| --- |
| `.claude/skills/add-a-cost-rule/SKILL.md` |
| `.claude/skills/add-a-price-source/SKILL.md` |
| `.claude/skills/explain-a-bill/SKILL.md` |

## Root files

| File |
| --- |
| `.dockerignore` |
| `.env.example` |
| `.gitignore` |
| `.vercelignore` |
| `AGENTS.md` |
| `ARCHITECTURE.md` |
| `CLAUDE.md` |
| `CONTRIBUTING.md` |
| `DATA_SOURCES.md` |
| `DECISIONS.md` |
| `Dockerfile.vercel` |
| `LICENSE` |
| `Makefile` |
| `README.md` |
| `RESULTS.md` |
| `alembic.ini` |
| `index.py` |
| `pyproject.toml` |
| `requirements-expanded.txt` |
| `requirements.txt` |
| `uv.lock` |
| `vercel.json` |

## .githooks

| File |
| --- |
| `.githooks/pre-push` |

## .github

| File |
| --- |
| `.github/copilot-instructions.md` |
| `.github/workflows/checks.yml` |
| `.github/workflows/close-period.yml` |
| `.github/workflows/expanded-build.yml` |
| `.github/workflows/expanded-checks.yml` |
| `.github/workflows/expanded-prices.yml` |
| `.github/workflows/fetch-ledgers.yml` |
| `.github/workflows/fetch-portfolio.yml` |
| `.github/workflows/fetch-prices.yml` |
| `.github/workflows/focus-full.yml` |
| `.github/workflows/focus-validation.yml` |
| `.github/workflows/lock-dependencies.yml` |
| `.github/workflows/pages.yml` |
| `.github/workflows/preserve-browser-evidence.yml` |
| `.github/workflows/verify-hosted.yml` |
| `.github/workflows/verify-live-pages.yml` |
| `.github/workflows/web-checks.yml` |

## config

| File |
| --- |
| `config/completion.json` |
| `config/expanded-incidents.json` |
| `config/focus/1.4-columns.json` |
| `config/incidents.json` |
| `config/method-notes.json` |
| `config/palette.json` |
| `config/simulator.json` |

## data

| File |
| --- |
| `data/portfolio/ledgers/goodhart-manifest.json` |
| `data/portfolio/ledgers/lock.json` |
| `data/portfolio/lock.json` |
| `data/prices/book.json` |
| `data/prices/evidence/v2/results/fetched-prices.json` |
| `data/prices/evidence/v2/tmp/http-cache/251c8617f3d567d3fde9d15733b899921a9bf8a04f03b1e0725f302b7c2b393c.json` |
| `data/prices/evidence/v2/tmp/http-cache/98488aa54078db85c9724588b317d0b989df85245a061232a5c5c16d419ff37a.json` |
| `data/prices/evidence/v2/tmp/http-cache/ee32b5b524e23efa9c4540c29fa9af45cb5e01cf02f0e9fd6210cf75d7b11056.json` |
| `data/prices/expanded/book.json` |
| `data/prices/expanded/candidate.json` |
| `data/prices/expanded/lock.json` |
| `data/prices/history/v1-book.json` |
| `data/prices/history/v1-lock.json` |
| `data/prices/lock.json` |
| `data/prices/manual.yaml` |
| `data/prices/observed.json` |

## docs

| File |
| --- |
| `docs/BUILD_BRIEF.md` |
| `docs/DECISIONS.md` |
| `docs/FILE_TREE.md` |
| `docs/FOCUS.md` |
| `docs/HOSTING.md` |
| `docs/RUNBOOK.md` |
| `docs/SPEC.md` |
| `docs/adr/001-focus-schema.md` |
| `docs/adr/002-larger-of-request-and-usage.md` |
| `docs/adr/003-idle-before-allocation.md` |
| `docs/adr/004-shapley-reference.md` |
| `docs/adr/005-shadow-list-prices.md` |
| `docs/adr/006-sealed-truth.md` |
| `docs/adr/007-actions-fetches.md` |
| `docs/demo.gif` |
| `docs/incidents/weekend-sweep.md` |
| `docs/methods/allocation.md` |
| `docs/methods/anomalies.md` |
| `docs/methods/commitments.md` |
| `docs/methods/data.md` |
| `docs/methods/detection.md` |
| `docs/methods/estimate.md` |
| `docs/methods/forecast.md` |
| `docs/methods/playbook.md` |
| `docs/methods/portfolio.md` |
| `docs/methods/recommendations.md` |
| `docs/methods/statement.md` |
| `docs/methods/unit.md` |

## evaluation

| File |
| --- |
| `evaluation/plan.json` |
| `evaluation/registration.json` |
| `evaluation/v2/plan.json` |
| `evaluation/v2/registration.json` |

## migrations

| File |
| --- |
| `migrations/bootstrap.sql` |
| `migrations/env.py` |
| `migrations/versions/0001_scoped_logs.py` |

## notebooks

| File |
| --- |
| `notebooks/01_the_even_split.ipynb` |
| `notebooks/02_the_monday_detector.ipynb` |
| `notebooks/03_the_wrong_gpu.ipynb` |

## packages

| File |
| --- |
| `packages/__init__.py` |
| `packages/allocation/__init__.py` |
| `packages/allocation/engine.py` |
| `packages/allocation/shapley.py` |
| `packages/api/__init__.py` |
| `packages/api/app.py` |
| `packages/api/sizing.py` |
| `packages/api/storage.py` |
| `packages/core/__init__.py` |
| `packages/core/contracts.py` |
| `packages/core/gates.py` |
| `packages/core/io.py` |
| `packages/core/money.py` |
| `packages/detect/__init__.py` |
| `packages/detect/detector.py` |
| `packages/detect/expanded.py` |
| `packages/evaluation/__init__.py` |
| `packages/evaluation/counterfactual.py` |
| `packages/evaluation/expanded.py` |
| `packages/evaluation/latency.py` |
| `packages/evaluation/ownership.py` |
| `packages/evaluation/score.py` |
| `packages/evaluation/statistics.py` |
| `packages/expansion/__init__.py` |
| `packages/expansion/analysis.py` |
| `packages/expansion/exports.py` |
| `packages/focus/__init__.py` |
| `packages/focus/export.py` |
| `packages/forecast/__init__.py` |
| `packages/forecast/expanded.py` |
| `packages/forecast/models.py` |
| `packages/optimize/__init__.py` |
| `packages/optimize/commitments.py` |
| `packages/optimize/expanded.py` |
| `packages/optimize/recommendations.py` |
| `packages/portfolio/__init__.py` |
| `packages/portfolio/usage.py` |
| `packages/prices/__init__.py` |
| `packages/prices/book.py` |
| `packages/prices/client.py` |
| `packages/render/__init__.py` |
| `packages/render/documents.py` |
| `packages/render/expanded.py` |
| `packages/simulator/__init__.py` |
| `packages/simulator/expanded.py` |
| `packages/simulator/generate.py` |
| `packages/truth/__init__.py` |
| `packages/truth/access.py` |
| `packages/unit/__init__.py` |
| `packages/unit/economics.py` |
| `packages/warehouse/__init__.py` |
| `packages/warehouse/build.py` |
| `packages/warehouse/expanded.py` |

## report

| File |
| --- |
| `report/briefing.md` |
| `report/statements/2025-01-ads.md` |
| `report/statements/2025-01-assistant.md` |
| `report/statements/2025-01-forecasting.md` |
| `report/statements/2025-01-fraud.md` |
| `report/statements/2025-01-research.md` |
| `report/statements/2025-01-search.md` |
| `report/statements/2025-01-unallocated.md` |
| `report/statements/2025-02-ads.md` |
| `report/statements/2025-02-assistant.md` |
| `report/statements/2025-02-forecasting.md` |
| `report/statements/2025-02-fraud.md` |
| `report/statements/2025-02-research.md` |
| `report/statements/2025-02-search.md` |
| `report/statements/2025-02-unallocated.md` |
| `report/statements/2025-03-ads.md` |
| `report/statements/2025-03-assistant.md` |
| `report/statements/2025-03-forecasting.md` |
| `report/statements/2025-03-fraud.md` |
| `report/statements/2025-03-research.md` |
| `report/statements/2025-03-search.md` |
| `report/statements/2025-03-unallocated.md` |
| `report/statements/2025-04-ads.md` |
| `report/statements/2025-04-assistant.md` |
| `report/statements/2025-04-forecasting.md` |
| `report/statements/2025-04-fraud.md` |
| `report/statements/2025-04-research.md` |
| `report/statements/2025-04-search.md` |
| `report/statements/2025-04-unallocated.md` |
| `report/statements/2025-05-ads.md` |
| `report/statements/2025-05-assistant.md` |
| `report/statements/2025-05-forecasting.md` |
| `report/statements/2025-05-fraud.md` |
| `report/statements/2025-05-research.md` |
| `report/statements/2025-05-search.md` |
| `report/statements/2025-05-unallocated.md` |
| `report/statements/2025-06-ads.md` |
| `report/statements/2025-06-assistant.md` |
| `report/statements/2025-06-forecasting.md` |
| `report/statements/2025-06-fraud.md` |
| `report/statements/2025-06-research.md` |
| `report/statements/2025-06-search.md` |
| `report/statements/2025-06-unallocated.md` |
| `report/statements/2025-07-ads.md` |
| `report/statements/2025-07-assistant.md` |
| `report/statements/2025-07-forecasting.md` |
| `report/statements/2025-07-fraud.md` |
| `report/statements/2025-07-research.md` |
| `report/statements/2025-07-search.md` |
| `report/statements/2025-07-unallocated.md` |
| `report/statements/2025-08-ads.md` |
| `report/statements/2025-08-assistant.md` |
| `report/statements/2025-08-forecasting.md` |
| `report/statements/2025-08-fraud.md` |
| `report/statements/2025-08-research.md` |
| `report/statements/2025-08-search.md` |
| `report/statements/2025-08-unallocated.md` |
| `report/statements/2025-09-ads.md` |
| `report/statements/2025-09-assistant.md` |
| `report/statements/2025-09-forecasting.md` |
| `report/statements/2025-09-fraud.md` |
| `report/statements/2025-09-research.md` |
| `report/statements/2025-09-search.md` |
| `report/statements/2025-09-unallocated.md` |
| `report/statements/2025-10-ads.md` |
| `report/statements/2025-10-assistant.md` |
| `report/statements/2025-10-forecasting.md` |
| `report/statements/2025-10-fraud.md` |
| `report/statements/2025-10-research.md` |
| `report/statements/2025-10-search.md` |
| `report/statements/2025-10-unallocated.md` |
| `report/statements/2025-11-ads.md` |
| `report/statements/2025-11-assistant.md` |
| `report/statements/2025-11-forecasting.md` |
| `report/statements/2025-11-fraud.md` |
| `report/statements/2025-11-research.md` |
| `report/statements/2025-11-search.md` |
| `report/statements/2025-11-unallocated.md` |
| `report/statements/2025-12-ads.md` |
| `report/statements/2025-12-assistant.md` |
| `report/statements/2025-12-forecasting.md` |
| `report/statements/2025-12-fraud.md` |
| `report/statements/2025-12-research.md` |
| `report/statements/2025-12-search.md` |
| `report/statements/2025-12-unallocated.md` |
| `report/templates/briefing.md.j2` |
| `report/templates/method.md.j2` |
| `report/templates/readme.md.j2` |
| `report/templates/results.md.j2` |
| `report/templates/statement.md.j2` |

## requests

| File |
| --- |
| `requests/portfolio.json` |
| `requests/prices.json` |

## results

| File |
| --- |
| `results/committed-ledgers.json` |
| `results/coverage.json` |
| `results/expanded/manifest.json` |
| `results/expanded/rebuild-17.json` |
| `results/expanded/rebuild-7919.json` |
| `results/expanded/reproducibility.json` |
| `results/expanded/summary.json` |
| `results/expanded/workbook-verification.json` |
| `results/full-focus/AllocatedCostAndUsage/ContractCommitment.log` |
| `results/full-focus/AllocatedCostAndUsage/ContractCommitment.xml` |
| `results/full-focus/AllocatedCostAndUsage/CostAndUsage.log` |
| `results/full-focus/AllocatedCostAndUsage/CostAndUsage.xml` |
| `results/full-focus/AllocatedCostAndUsage/summary.json` |
| `results/full-focus/CostAndUsage/ContractCommitment.log` |
| `results/full-focus/CostAndUsage/ContractCommitment.xml` |
| `results/full-focus/CostAndUsage/CostAndUsage.log` |
| `results/full-focus/CostAndUsage/CostAndUsage.xml` |
| `results/full-focus/CostAndUsage/summary.json` |
| `results/full-focus/conservation.json` |
| `results/full-focus/summary.json` |
| `results/hosted-validation.json` |
| `results/live/archive/browser-first.json` |
| `results/live/artifact-provenance.json` |
| `results/live/browser.json` |
| `results/live/independent-readback.json` |
| `results/live/latency-summary.json` |
| `results/live_check.json` |
| `results/manifest.json` |
| `results/portfolio-usage.json` |
| `results/provenance.json` |
| `results/reconcile.json` |
| `results/reproducibility.json` |
| `results/validation.json` |
| `results/verification.json` |

## scripts

| File |
| --- |
| `scripts/audit_focus.py` |
| `scripts/build.py` |
| `scripts/build_expanded.py` |
| `scripts/check.py` |
| `scripts/check_container.py` |
| `scripts/check_diff.py` |
| `scripts/check_expanded_reproducibility.py` |
| `scripts/check_hosted.py` |
| `scripts/check_persistence.py` |
| `scripts/check_reproducibility.py` |
| `scripts/close_period.py` |
| `scripts/fetch_committed_ledgers.py` |
| `scripts/fetch_expanded_prices.py` |
| `scripts/fetch_portfolio_usage.py` |
| `scripts/fetch_prices.py` |
| `scripts/focus_fixture.py` |
| `scripts/initialize_prices.py` |
| `scripts/make_demo.py` |
| `scripts/promote_expanded_prices.py` |
| `scripts/promote_portfolio.py` |
| `scripts/promote_prices.py` |
| `scripts/promote_verification.py` |
| `scripts/record_local_validation.py` |
| `scripts/register_expansion.py` |
| `scripts/register_plan.py` |
| `scripts/scheduled_close.py` |
| `scripts/serve_frontend_test.py` |
| `scripts/serve_local.py` |
| `scripts/validate_full_focus.py` |
| `scripts/validate_palette.js` |
| `scripts/verify_workbook.py` |

## tests

| File |
| --- |
| `tests/test_api.py` |
| `tests/test_core.py` |
| `tests/test_expanded_detector.py` |
| `tests/test_expanded_forecast.py` |
| `tests/test_expanded_integration.py` |
| `tests/test_expanded_pipeline.py` |
| `tests/test_focus.py` |
| `tests/test_gates_expanded.py` |
| `tests/test_hosting.py` |
| `tests/test_latency.py` |
| `tests/test_methods.py` |
| `tests/test_pipeline.py` |
| `tests/test_portfolio.py` |
| `tests/test_postgres_routes.py` |
| `tests/test_render_expanded.py` |
| `tests/test_sizing.py` |
| `tests/test_sources.py` |
| `tests/web-client.test.cjs` |

## warehouse-expanded

| File |
| --- |
| `warehouse-expanded/dbt_project.yml` |
| `warehouse-expanded/models/mart_cost_daily.sql` |
| `warehouse-expanded/models/schema.yml` |
| `warehouse-expanded/models/stg_observed.sql` |
| `warehouse-expanded/profiles.yml` |
| `warehouse-expanded/tests/source_reconciliation.sql` |

## warehouse

| File |
| --- |
| `warehouse/dbt_project.yml` |
| `warehouse/models/mart_monthly.sql` |
| `warehouse/models/schema.yml` |
| `warehouse/models/stg_charges.sql` |
| `warehouse/profiles.yml` |

## web

| File |
| --- |
| `web/api.js` |
| `web/app.js` |
| `web/app/[route]/page.tsx` |
| `web/app/charts.tsx` |
| `web/app/estimate.tsx` |
| `web/app/forecast-form.tsx` |
| `web/app/globals.css` |
| `web/app/layout.tsx` |
| `web/app/ledger.tsx` |
| `web/app/page.tsx` |
| `web/app/query.tsx` |
| `web/app/routes.ts` |
| `web/config.js` |
| `web/data.json` |
| `web/expanded.json` |
| `web/index.html` |
| `web/live.playwright.config.ts` |
| `web/next.config.ts` |
| `web/package-lock.json` |
| `web/package.json` |
| `web/playwright.config.ts` |
| `web/postcss.config.mjs` |
| `web/prepare.mjs` |
| `web/style.css` |
| `web/tests/ledger.spec.ts` |
| `web/tests/live.spec.ts` |
| `web/tsconfig.json` |

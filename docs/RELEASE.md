# MLSpend v0.1.0

MLSpend provides cost allocation, unit economics, forecasts, incident analysis and finance exports for ML workloads. The [dashboard](https://mekala27-45.github.io/mlspend/) runs on GitHub Pages; the [metered API](https://mlspend.vercel.app/health) runs in a port-80 container on Vercel with PostgreSQL persistence.

The [required checklist and all numeric tables](https://github.com/mekala27-45/mlspend/blob/v0.1.0/RESULTS.md), [file inventory](https://github.com/mekala27-45/mlspend/blob/v0.1.0/docs/FILE_TREE.md) and [recorded demo](https://github.com/mekala27-45/mlspend/blob/v0.1.0/docs/demo.gif) are included. The six stretch items are listed separately and remain outside this release.

The runtime and study source is `de15f32947ea2d389a63e9b5123bff36c61fc829`. Its [core checks](https://github.com/mekala27-45/mlspend/actions/runs/41739841297) passed 87 tests with 89.77 percent package coverage, strict mypy, ruff, palette and repository-skill validation, executed notebooks, container persistence and dbt checks. The release commit adds evidence, documentation and four release-integrity tests. Publication waits for that commit's full CI and verifies that the runtime and study code have not changed.

The [full-year rebuild](https://github.com/mekala27-45/mlspend/actions/runs/41477467691) reproduced the same canonical manifest in the primary checkout and a detached worktree under different hash seeds, then recalculated the finance workbook. [Full FOCUS checks](https://github.com/mekala27-45/mlspend/actions/runs/41480417577) cover every source and allocated row. [Pages checks](https://github.com/mekala27-45/mlspend/actions/runs/41739841264) and the [published Windows Chrome flow](https://github.com/mekala27-45/mlspend/actions/runs/41740056384) passed. A separate SQL client confirmed both saved browser records.

The [registered prospective simulation](https://github.com/mekala27-45/mlspend/actions/runs/41475604592) saved six forecasts before generating the next simulated month's outcomes, scored all six and confirmed idempotent close. Only two intervals covered their outcome. That unfavorable result is preserved. Real December 2026 forecasts retain their calendar clock and remain pending actuals.

Platform costs and counterfactual savings are simulated. Public portfolio figures are shadow estimates at source prices; missing GPU telemetry and unmatched paid SKUs remain unpriced. Neither primary statistical comparison was significant. The official validator's supported prior rules and the supplemental FOCUS 1.4 contracts are reported separately; official 1.4 certification is not claimed. This is a portfolio demonstration, not measured production savings.

Code is Apache-2.0. Provider data retains its original terms in [DATA_SOURCES.md](https://github.com/mekala27-45/mlspend/blob/v0.1.0/DATA_SOURCES.md). Created for Ajay Mekala with AI assistance.

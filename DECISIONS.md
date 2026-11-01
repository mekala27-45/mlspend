# Implementation decisions

These are decisions and corrections made during the build. Dates are the actual implementation date; no history is backdated. The authoritative prompt is docs/SPEC.md.

## 2026-11-01: Integer money

Keep money as integer microdollars internally and Decimal at price boundaries. Stable largest remainders conserve every statement. Model support is allocated once within each owner, including unallocated.

## 2026-11-01: UTC periods

DuckDB inherited the laptop time zone in an early reconciliation. Set UTC explicitly before grouping timestamps; independent Python aggregates retain UTC period boundaries.

## 2026-11-01: Freeze external evidence

Fetch source records in Actions, preserve raw response hashes and repository commit IDs, and promote exact blobs. Never serialize an already-promoted scientific manifest through another language merely to copy it.

## 2026-11-01: Independent replication

Version-one results were already known. Register an expanded independent replication with a new seed and preserve the older evidence instead of claiming a blind first study.

## 2026-11-01: Reversal: capacity value is not cash

The initial recommendation report valued released reservations. Whole-platform reruns showed that minimum shared capacity can retain the bill or make a spot move cost more. Replace cash claims with measured counterfactual differences; preserve the quiet-hour dead end in a notebook.

## 2026-11-01: Reversal: monthly interval construction

A daily interval cannot simply be reused for a monthly sum. Calibrate monthly-horizon residuals using complete earlier horizons and abstain when there are too few origins. Do not tune on held-out coverage.

## 2026-11-01: Shapley comparison population

An early allocation comparison mixed standalone capacity value with a fully loaded statement. Compare method allocations against the normalized Shapley allocation of the same shared bill. Document that this remains a model-based fairness reference.

## 2026-11-01: Contract completeness correction

After the first expanded run, the exporter was found to include only the shorter commitment. Add a separate longer-term unused commitment, full upfront billed cost and only the in-calendar amortization. This is a late completeness correction, not a claim that the initial implementation already contained it. The registered selection rules remain unchanged.

## 2026-11-01: Official validator failures

Keep the unmodified official XML. The newest rules contain an active dependency cycle; older status predicates and JSON null tests contradict their prose. Bound reviewed exceptions by exact rule IDs, reject new failures and enforce the normative constraints independently. Do not claim official certification.

## 2026-11-01: Container entrypoint reversal

The first container entrypoint imported a companion static app whose web assets were excluded. Point the container directly at packages.api.app:app. The Pages site is deployed independently.

## 2026-11-01: Scoped database role

A role created through the provider convenience API inherited elevated membership. Create a plain SQL login with explicit grants instead. Move application tables into their own schema; do not run schema creation from the request process. Retain old tables during migration for a non-destructive cutover.

## 2026-11-01: Honest API failure states

A missing database returns HTTP 503 with Retry-After. Browser readiness uses GET twice. An uncertain POST is never retried automatically or called unsaved; a confirmed local fallback is visibly not persisted.

## 2026-11-01: No invented portfolio units

Committed model tokens and output counts are measured. Unknown exact paid endpoints and absent GPU ledgers remain unknown; unrelated CI jobs are not divided into a claimed per-refresh or per-answer total.

## 2026-11-01: Canonical reporting

Generate the dashboard, team statements and public numeric claims from the same expanded manifest. Preserve the exact underlying integers in the browser SQL tables instead of parsing rounded display money.

## 2026-11-01: Release boundary

A future forecast can be logged now but cannot truthfully have an observed future-period score. Keep period-close pending until actuals are complete. Do not tag a complete release while a mandatory check is unresolved.


## 2026-11-01: Stable database reductions

The first two full hash-seed runs exposed export-directory state and then floating-point aggregation order as drift sources. Use an explicit delivered-file inventory and ordered reductions over timestamp/id. No analytical threshold changed. Source: scripts/check_expanded_reproducibility.py and Actions runs 41263501602 and 41264845248, inspected 2026-11-01.

## 2026-11-01: Complete mart lineage

Recommendation estimates now stream the validated contracted observation mart, with a hard failure when the full build lacks that mart. The smoke test may use its reconciled priced table. Source: warehouse-expanded/models/stg_observed.sql and packages/warehouse/expanded.py, inspected 2026-11-01.

## 2026-11-01: Allocated metadata in the integration fixture

The full-year validator found an underscore in the original usage-share label. Omitting the optional unit then exposed an upstream conditional-presence issue. Use the documented dimensionless component name `Usage Share`, which follows the official format. Add split-charge rows to the quick official fixture so this metadata is exercised before a full rebuild. Do not expand the exception list to suppress the allocation failure.

## 2026-11-01: Classify instances before reporting warm latency

The second live run reached five API instances during its twenty follow-up requests. Preserve all raw samples and exclude first observations of additional instances from reused-process quantiles. A sequence after an idle test is not automatically warm. The deterministic report uses instance IDs, retains all exclusions and keeps network and database costs in the timing scope.

## 2026-11-01: Recover evidence without rerunning a passed test

The Windows browser test and demo capture passed, but its evidence-branch push referred to older workflow files after main advanced. Recover the exact uploaded artifact, verify the source test step passed and base the evidence-only commit on current main. Preserve the source run ID and retain the failed publication history.

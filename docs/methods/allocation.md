# The method changes the statement.

mlspend is a portfolio demonstration. Its platform costs are simulated with known truth. Its portfolio costs are shadow estimates of public project usage at published list prices; nobody paid these amounts. No figure is a quote, an invoice or financial advice.

## Purpose

The same source total supports five policies. The capacity Shapley calculation enumerates every coalition; its normalized shares allocate the recorded shared bill.

## Inputs

Contracted observed charges, owner evidence from namespace/network, requested and used capacity, locked pool rates and registered team weights.

## Assumptions

The larger of request and usage defines capacity responsibility. Idle is explicit before the shared bill is distributed. Coalitions use a simulated capacity quantile; Shapley is a modeled reference, not observed moral fairness.

## Score on the truth and observed results

All numeric tables below are rendered from results/expanded/manifest.json. Unit-economics arithmetic is checked on known fixtures; it is not an empirical model-quality result.


## One total, five policies



| Team | even | direct | usage | custom | shapley |
| --- | --- | --- | --- | --- | --- |
| ads | $2,216.11 | $1,208.91 | $1,943.20 | $1,777.56 | $1,112.03 |
| assistant | $5,434.85 | $5,530.29 | $5,233.49 | $5,873.40 | $5,350.08 |
| forecasting | $5,823.47 | $6,052.05 | $5,828.02 | $5,384.92 | $5,984.88 |
| fraud | $2,405.71 | $1,463.47 | $2,366.35 | $2,844.27 | $1,386.27 |
| research | $8,266.62 | $9,332.13 | $8,657.01 | $7,828.06 | $9,905.91 |
| search | $6,790.70 | $7,350.61 | $6,909.39 | $7,229.25 | $7,198.29 |
| unallocated | $232.70 | $232.70 | $232.70 | $232.70 | $232.70 |


## Idle before allocation



| Pool | Asset cost | Idle cost | Idle share |
| --- | --- | --- | --- |
| azure-t4 | $1,782.61 | $387.26 | 21.7% |
| azure-v100 | $14,625.53 | $1,290.35 | 8.8% |
| azure-a100 | $11,408.34 | $4,686.48 | 41.1% |
| reserved-t4 | $230.08 | $230.08 | 100.0% |
| reserved-a100-3y | $1,014.11 | $1,014.11 | 100.0% |


## Ownership inference



| Population | Correct | Wrong | Unresolved | Precision | Recall |
| --- | --- | --- | --- | --- | --- |
| originally untagged observed charge rows | 71002 | 0 | 4418 | 100.0% | 94.1% |


## Largest change across policies



| Team | Month | Range |
| --- | --- | --- |
| research | 2025-08 | $2,236.90 |


## Sensitivity and interior checks

The scorecard retains all policies on the same fixed total, the largest team-month movement and cluster uncertainty. A zero-total or nonconserving policy fails. The reference depends on the registered capacity quantile; no post-holdout tuning is performed.

## Limitations

Capacity contribution is a fairness reference under this coalition cost model. It is not an objective fairness label. Namespace and network must agree before an untagged charge is assigned.

## What a reviewer would push back on

A platform engineer can object that bursty workloads and fractional GPUs alter responsibility. A FinOps lead can reject the coalition model. Inspect the alternative bills and use the reference as a discussion input.

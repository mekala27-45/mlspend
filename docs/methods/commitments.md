# Buy the floor, measure the regret.

mlspend is a portfolio demonstration. Its platform costs are simulated with known truth. Its portfolio costs are shadow estimates of public project usage at published list prices; nobody paid these amounts. No figure is a quote, an invoice or financial advice.

## Purpose

Capacity is selected on development demand using actual locked public offer rates. Held-out regret is relative to the best registered capacity with hindsight.

## Inputs

Observed pool demand in development hours, locked real reservation or savings-plan offers, registered integer capacities and separately scored holdout demand.

## Assumptions

The commitment pays for its full capacity while excess demand uses on-demand rates. Unused committed capacity remains a cost. The scenario omits real procurement flexibility and negotiated terms.

## Score on the truth and observed results

All numeric tables below are rendered from results/expanded/manifest.json. Unit-economics arithmetic is checked on known fixtures; it is not an empirical model-quality result.


## Chosen capacity



| Pool | Offer | Units | Interior | Unused hours | Overflow hours |
| --- | --- | --- | --- | --- | --- |
| azure-t4 | azure-t4-reserved-1y | 3 | True | 674.71 | 4666.15 |
| azure-a100 | azure-a100-reserved-1y | 3 | True | 1550.57 | 1039.75 |
| azure-v100 | azure-v100-savings-1y | 3 | True | 80.05 | 7859.08 |


## Commitment sensitivity



| Pool | Multiplier | Capacity | Held-out USD/hour | Regret USD/hour |
| --- | --- | --- | --- | --- |
| azure-t4 | 0.8 | 2.4 | $1.81243 | $0.04644 |
| azure-t4 | 1.0 | 3.0 | $1.76599 | $0.00000 |
| azure-t4 | 1.2 | 3.6 | $1.76827 | $0.00228 |
| azure-a100 | 0.8 | 2.4 | $8.15307 | $0.01404 |
| azure-a100 | 1.0 | 3.0 | $8.50738 | $0.36835 |
| azure-a100 | 1.2 | 3.6 | $9.22250 | $1.08347 |
| azure-v100 | 0.8 | 2.4 | $15.35200 | $0.85561 |
| azure-v100 | 1.0 | 3.0 | $14.94232 | $0.44593 |
| azure-v100 | 1.2 | 3.6 | $14.62699 | $0.13060 |


## Development objective



| Pool | Candidate capacity | USD/hour |
| --- | --- | --- |
| azure-t4 | 0 | $1.74489 |
| azure-t4 | 1 | $1.52814 |
| azure-t4 | 2 | $1.33790 |
| azure-t4 | 3 | $1.29442 |
| azure-t4 | 4 | $1.40298 |
| azure-t4 | 6 | $1.89890 |
| azure-t4 | 8 | $2.48097 |
| azure-t4 | 12 | $3.71096 |
| azure-t4 | 16 | $4.94795 |
| azure-t4 | 24 | $7.42192 |
| azure-t4 | 32 | $9.89589 |
| azure-t4 | 48 | $14.84384 |
| azure-t4 | 64 | $19.79178 |
| azure-a100 | 0 | $13.39393 |
| azure-a100 | 1 | $12.12196 |
| azure-a100 | 2 | $10.95993 |
| azure-a100 | 3 | $10.52227 |
| azure-a100 | 4 | $11.22143 |
| azure-a100 | 6 | $14.48542 |
| azure-a100 | 8 | $19.21036 |
| azure-a100 | 12 | $28.81233 |
| azure-a100 | 16 | $38.41644 |
| azure-a100 | 24 | $57.62466 |
| azure-a100 | 32 | $76.83288 |
| azure-a100 | 48 | $115.24932 |
| azure-a100 | 64 | $153.66575 |
| azure-v100 | 0 | $12.28213 |
| azure-v100 | 1 | $11.46511 |
| azure-v100 | 2 | $10.71279 |
| azure-v100 | 3 | $10.46878 |
| azure-v100 | 4 | $11.00397 |
| azure-v100 | 6 | $13.86895 |
| azure-v100 | 8 | $17.96977 |
| azure-v100 | 12 | $26.91576 |
| azure-v100 | 16 | $35.88768 |
| azure-v100 | 24 | $53.83152 |
| azure-v100 | 32 | $71.77536 |
| azure-v100 | 48 | $107.66304 |
| azure-v100 | 64 | $143.55072 |


## Sensitivity and interior checks

The chosen integer level must be interior to the registered candidate set. The scorecard reports held-out regret at the chosen level and 20 percent less or more; fractional sensitivity levels are not claimed to be purchasable.

## Limitations

Fractional perturbations are analytical sensitivity points, not necessarily purchasable units. No commitment was purchased. Future demand and provider offer availability can change.

## What a reviewer would push back on

The future demand distribution can shift after procurement. Compare the held-out regret and unused capacity, then model the actual contract terms before making a financial commitment.

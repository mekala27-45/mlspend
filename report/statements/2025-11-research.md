# research · 2025-11

mlspend is a portfolio demonstration. Its platform costs are simulated with known truth. Its portfolio costs are shadow estimates of public project usage at published list prices; nobody paid these amounts. No figure is a quote, an invoice or financial advice.

Method of record: usage. Direct cost $7,012.86; idle and shared allocation $1,686.09.


## Allocation policy



| Method | Statement |
| --- | --- |
| custom | $7,838.19 |
| direct | $9,388.25 |
| even | $8,250.86 |
| shapley | $9,793.37 |
| usage | $8,698.96 |


## Workloads



| Model | Service | Outputs | Fully loaded | Cost / output |
| --- | --- | --- | --- | --- |
| research-inference-v2 | inference | 9631104 | $5,594.72 | $0.00 |
| research-llm-v2 | llm | 127708 | $234.79 | $0.00 |
| research-notebook-v2 | notebook | 0 | $1,638.72 | Not measured |
| research-training-v2 | training | 715 | $1,230.73 | $1.72 |


## Direct-spend forecast



| Period | Point | Lower | Upper | Actual |
| --- | --- | --- | --- | --- |
| 2025-11 | $6,379.18 | $3,691.12 | $9,067.24 | $7,012.86 |


## Incidents starting this month



| Incident | First alert | Avoidable counterfactual |
| --- | --- | --- |
| idle-notebook | 2025-11-02T00:00:00+00:00 | $62.44 |

Review docs/methods/recommendations.md before changing capacity. Forecasts use direct spend and are not directly comparable to fully loaded statements. Source: results/expanded/manifest.json; allocation conserves integer microdollars.

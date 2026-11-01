# Free capacity is not cash saved.

mlspend is a portfolio demonstration. Its platform costs are simulated with known truth. Its portfolio costs are shadow estimates of public project usage at published list prices; nobody paid these amounts. No figure is a quote, an invoice or financial advice.

Each action is estimated from observed telemetry, then independently rerun against the whole simulated platform. Shared-capacity effects can reduce savings or increase cost.

## Whole-platform counterfactuals



| Action | Estimated annual | True annual change | Estimation error |
| --- | --- | --- | --- |
| rightsize | $55,907.74 | $33,395.00 | $22,512.74 |
| spot | $35,226.40 | $21,302.52 | $13,923.89 |
| remove_floor | $1,925.55 | $1,700.56 | $225.00 |
| tier_storage | $217.06 | $217.06 | $0.00 |
| deduplicate | $61.94 | $61.94 | $0.00 |
| stop_notebook | $786.02 | $172.63 | $613.39 |
| switch_model | $9,692.02 | $9,692.02 | $0.00 |


## Resource estimates and uncertainty



| Resource | Action | Monthly estimate | 90% lower | 90% upper | Resource truth covered |
| --- | --- | --- | --- | --- | --- |
| fraud-dataset-copy | deduplicate | $5.16 | $4.56 | $5.83 | True |
| ads-endpoint | remove_floor | $160.46 | $114.90 | $206.89 | True |
| ads-endpoint | rightsize | $114.31 | $110.56 | $117.96 | True |
| assistant-endpoint | rightsize | $895.75 | $879.25 | $911.58 | True |
| forecasting-endpoint | rightsize | $911.82 | $893.39 | $930.18 | True |
| fraud-endpoint | rightsize | $173.80 | $170.54 | $177.36 | True |
| research-endpoint | rightsize | $1,339.50 | $1,315.45 | $1,362.31 | True |
| search-endpoint | rightsize | $1,223.81 | $1,202.33 | $1,244.28 | True |
| ads-training | spot | $87.72 | $86.09 | $89.23 | True |
| assistant-training | spot | $679.63 | $667.75 | $690.23 | True |
| forecasting-training | spot | $615.77 | $603.95 | $627.27 | True |
| fraud-training | spot | $93.20 | $86.54 | $104.42 | True |
| research-training | spot | $837.14 | $781.03 | $901.17 | True |
| search-training | spot | $622.06 | $611.21 | $633.16 | True |
| research-notebook | stop_notebook | $65.50 | $29.38 | $102.23 | True |
| ads-answers-cached | switch_model | $1.47 | $1.45 | $1.50 | True |
| ads-answers-input | switch_model | $77.28 | $75.93 | $78.65 | True |
| ads-answers-output | switch_model | $82.80 | $81.32 | $84.31 | True |
| assistant-answers-cached | switch_model | $1.47 | $1.44 | $1.50 | True |
| assistant-answers-input | switch_model | $77.21 | $75.82 | $78.74 | True |
| assistant-answers-output | switch_model | $82.73 | $81.20 | $84.11 | True |
| forecasting-answers-cached | switch_model | $1.47 | $1.45 | $1.50 | True |
| forecasting-answers-input | switch_model | $77.29 | $75.97 | $78.58 | True |
| forecasting-answers-output | switch_model | $82.81 | $81.28 | $84.19 | True |
| research-answers-cached | switch_model | $1.47 | $1.45 | $1.50 | True |
| research-answers-input | switch_model | $77.28 | $75.91 | $78.57 | True |
| research-answers-output | switch_model | $82.80 | $81.43 | $84.21 | True |
| search-answers-cached | switch_model | $1.47 | $1.45 | $1.50 | True |
| search-answers-input | switch_model | $77.29 | $75.95 | $78.67 | True |
| search-answers-output | switch_model | $82.81 | $81.43 | $84.27 | True |
| ads-dataset | tier_storage | $2.24 | $2.16 | $2.32 | True |
| assistant-dataset | tier_storage | $2.55 | $2.47 | $2.63 | True |
| forecasting-dataset | tier_storage | $2.86 | $2.77 | $2.95 | True |
| fraud-dataset | tier_storage | $3.17 | $3.07 | $3.27 | True |
| research-dataset | tier_storage | $3.48 | $3.37 | $3.58 | True |
| search-dataset | tier_storage | $3.79 | $3.67 | $3.90 | True |


## Combined rerun



| Joint saving | Share of baseline | Share of registered avoidable reference |
| --- | --- | --- |
| $51,316.71 | 14.7% | 94.0% |

## Limits and pushback

Joint saving comes from one combined rerun. Incident-removal effects and standalone action savings are not additive; no summed savings claim. The avoidable reference combines registered actions and incident removal; it is not a proof of the global optimum. Resampled estimate intervals are not guaranteed cash-saving intervals. Model switching requires the registered quality floor.

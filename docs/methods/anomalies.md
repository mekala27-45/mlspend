# Find the sweep before the invoice.

mlspend is a portfolio demonstration. Its platform costs are simulated with known truth. Its portfolio costs are shadow estimates of public project usage at published list prices; nobody paid these amounts. No figure is a quote, an invoice or financial advice.

Seasonal MAD and positive CUSUM are calibrated on development data with a false-alarm budget. Hourly and daily team, service and SKU series are scored on held-out months.

## Held-out detection



| Event recall | Alert precision | Point recall | Burn before detection |
| --- | --- | --- | --- |
| 100.0% | 41.7% | 25.6% | $0.00 |


## Incident record



| Incident | Team | Start | First alert | Delay hours | Avoidable cost |
| --- | --- | --- | --- | --- | --- |
| weekend-sweep | research | 2025-09-12T18:00:00+00:00 | 2025-09-12T18:00:00+00:00 | 0.0 | $297.51 |
| replica-floor | ads | 2025-10-03T00:00:00+00:00 | 2025-10-03T00:00:00+00:00 | 0.0 | $1,152.99 |
| idle-notebook | research | 2025-11-02T00:00:00+00:00 | 2025-11-02T00:00:00+00:00 | 0.0 | $62.44 |
| spot-interruptions | forecasting | 2025-12-09T00:00:00+00:00 | 2025-12-09T01:00:00+00:00 | 1.0 | $4.85 |
| export-egress | search | 2025-10-18T00:00:00+00:00 | 2025-10-18T00:00:00+00:00 | 0.0 | $2,923.20 |
| duplicate-storage | fraud | 2025-09-01T00:00:00+00:00 | 2025-09-01T00:00:00+00:00 | 0.0 | $61.94 |
| untagged-batch | fraud | 2025-09-22T00:00:00+00:00 | 2025-09-22T00:00:00+00:00 | 0.0 | $96.26 |


## Calibration and boundaries



| Grain | Team | Service | SKU | Method | Threshold | Dev false alarms | Interior |
| --- | --- | --- | --- | --- | --- | --- | --- |
| hour | ads | cpu | Standard_D4s_v5 | seasonal_mad | 5 | 1.0% | True |
| day | ads | cpu | Standard_D4s_v5 | seasonal_mad | 3 | 0.0% | False |
| hour | ads | inference | Standard_NC4as_T4_v3 | seasonal_mad | 12 | 3.2% | False |
| day | ads | inference | Standard_NC4as_T4_v3 | seasonal_mad | 3 | 0.5% | False |
| hour | ads | llm | gpt-6.1-terra cached | seasonal_mad | 5 | 1.0% | True |
| day | ads | llm | gpt-6.1-terra cached | seasonal_mad | 3 | 0.0% | False |
| hour | ads | llm | gpt-6.1-terra input | seasonal_mad | 5 | 1.0% | True |
| day | ads | llm | gpt-6.1-terra input | seasonal_mad | 3 | 0.5% | False |
| hour | ads | llm | gpt-6.1-terra output | seasonal_mad | 5 | 1.0% | True |
| day | ads | llm | gpt-6.1-terra output | seasonal_mad | 3 | 0.5% | False |
| hour | ads | network | Standard Data Transfer Out | seasonal_mad | 5 | 1.0% | True |
| day | ads | network | Standard Data Transfer Out | seasonal_mad | 3 | 0.0% | False |
| hour | ads | storage | Hot LRS Data Stored | seasonal_mad | 5 | 0.0% | True |
| day | ads | storage | Hot LRS Data Stored | seasonal_mad | 9 | 0.9% | True |
| hour | ads | training | Standard_NC4as_T4_v3 | seasonal_mad | 5 | 1.0% | True |
| day | ads | training | Standard_NC4as_T4_v3 | seasonal_mad | 3 | 0.0% | False |
| hour | ads | vector | Standard_D4s_v5 | seasonal_mad | 5 | 1.0% | True |
| day | ads | vector | Standard_D4s_v5 | seasonal_mad | 3 | 0.0% | False |
| hour | ads | warehouse | Standard_D4s_v5 | seasonal_mad | 5 | 1.0% | True |
| day | ads | warehouse | Standard_D4s_v5 | seasonal_mad | 3 | 0.5% | False |
| hour | assistant | cpu | Standard_D4s_v5 | seasonal_mad | 5 | 0.9% | True |
| day | assistant | cpu | Standard_D4s_v5 | seasonal_mad | 3 | 0.0% | False |
| hour | assistant | inference | Standard_NC24ads_A100_v4 | seasonal_mad | 12 | 2.7% | False |
| day | assistant | inference | Standard_NC24ads_A100_v4 | seasonal_mad | 3 | 0.0% | False |
| hour | assistant | inference | Standard_NC6s_v3 | Unscored: no development history | Not measured | Not measured | False |
| day | assistant | inference | Standard_NC6s_v3 | Unscored: no development history | Not measured | Not measured | False |
| hour | assistant | llm | gpt-6.1-terra cached | seasonal_mad | 5 | 1.0% | True |
| day | assistant | llm | gpt-6.1-terra cached | seasonal_mad | 3 | 0.0% | False |
| hour | assistant | llm | gpt-6.1-terra input | seasonal_mad | 5 | 1.0% | True |
| day | assistant | llm | gpt-6.1-terra input | seasonal_mad | 3 | 0.0% | False |
| hour | assistant | llm | gpt-6.1-terra output | seasonal_mad | 5 | 0.9% | True |
| day | assistant | llm | gpt-6.1-terra output | seasonal_mad | 3 | 0.0% | False |
| hour | assistant | network | Standard Data Transfer Out | seasonal_mad | 5 | 0.9% | True |
| day | assistant | network | Standard Data Transfer Out | seasonal_mad | 3 | 0.9% | False |
| hour | assistant | storage | Hot LRS Data Stored | seasonal_mad | 5 | 0.0% | True |
| day | assistant | storage | Hot LRS Data Stored | seasonal_mad | 9 | 1.4% | True |
| hour | assistant | training | Standard_NC24ads_A100_v4 | seasonal_mad | 5 | 0.8% | True |
| day | assistant | training | Standard_NC24ads_A100_v4 | seasonal_mad | 3 | 0.0% | False |
| hour | assistant | training | Standard_NC6s_v3 | seasonal_mad | 5 | 1.5% | True |
| day | assistant | training | Standard_NC6s_v3 | seasonal_mad | 3 | 0.0% | False |
| hour | assistant | vector | Standard_D4s_v5 | seasonal_mad | 5 | 0.9% | True |
| day | assistant | vector | Standard_D4s_v5 | seasonal_mad | 3 | 0.0% | False |
| hour | assistant | warehouse | Standard_D4s_v5 | seasonal_mad | 5 | 0.9% | True |
| day | assistant | warehouse | Standard_D4s_v5 | seasonal_mad | 3 | 0.5% | False |
| hour | forecasting | cpu | Standard_D4s_v5 | seasonal_mad | 5 | 0.9% | True |
| day | forecasting | cpu | Standard_D4s_v5 | seasonal_mad | 3 | 1.4% | False |
| hour | forecasting | inference | Standard_NC6s_v3 | seasonal_mad | 12 | 2.5% | False |
| day | forecasting | inference | Standard_NC6s_v3 | seasonal_mad | 3 | 0.0% | False |
| hour | forecasting | llm | gpt-6.1-terra cached | seasonal_mad | 5 | 0.9% | True |
| day | forecasting | llm | gpt-6.1-terra cached | seasonal_mad | 3 | 1.9% | False |
| hour | forecasting | llm | gpt-6.1-terra input | seasonal_mad | 5 | 0.9% | True |
| day | forecasting | llm | gpt-6.1-terra input | seasonal_mad | 3 | 0.5% | False |
| hour | forecasting | llm | gpt-6.1-terra output | seasonal_mad | 5 | 0.9% | True |
| day | forecasting | llm | gpt-6.1-terra output | seasonal_mad | 3 | 0.0% | False |
| hour | forecasting | network | Standard Data Transfer Out | seasonal_mad | 5 | 0.9% | True |
| day | forecasting | network | Standard Data Transfer Out | seasonal_mad | 3 | 0.5% | False |
| hour | forecasting | storage | Hot LRS Data Stored | seasonal_mad | 5 | 0.0% | True |
| day | forecasting | storage | Hot LRS Data Stored | seasonal_mad | 7 | 0.9% | True |
| hour | forecasting | training | Standard_NC6s_v3 | seasonal_mad | 5 | 0.9% | True |
| day | forecasting | training | Standard_NC6s_v3 | seasonal_mad | 3 | 0.0% | False |
| hour | forecasting | vector | Standard_D4s_v5 | seasonal_mad | 5 | 0.9% | True |
| day | forecasting | vector | Standard_D4s_v5 | seasonal_mad | 3 | 0.0% | False |
| hour | forecasting | warehouse | Standard_D4s_v5 | seasonal_mad | 5 | 0.9% | True |
| day | forecasting | warehouse | Standard_D4s_v5 | seasonal_mad | 3 | 0.0% | False |
| hour | fraud | cpu | Standard_D4s_v5 | seasonal_mad | 5 | 0.9% | True |
| day | fraud | cpu | Standard_D4s_v5 | seasonal_mad | 3 | 0.0% | False |
| hour | fraud | inference | Standard_NC4as_T4_v3 | seasonal_mad | 12 | 2.7% | False |
| day | fraud | inference | Standard_NC4as_T4_v3 | seasonal_mad | 3 | 0.5% | False |
| hour | fraud | llm | gpt-6.1-terra cached | seasonal_mad | 5 | 0.9% | True |
| day | fraud | llm | gpt-6.1-terra cached | seasonal_mad | 3 | 0.0% | False |
| hour | fraud | llm | gpt-6.1-terra input | seasonal_mad | 5 | 0.9% | True |
| day | fraud | llm | gpt-6.1-terra input | seasonal_mad | 3 | 0.0% | False |
| hour | fraud | llm | gpt-6.1-terra output | seasonal_mad | 5 | 1.0% | True |
| day | fraud | llm | gpt-6.1-terra output | seasonal_mad | 3 | 0.9% | False |
| hour | fraud | network | Standard Data Transfer Out | seasonal_mad | 5 | 0.9% | True |
| day | fraud | network | Standard Data Transfer Out | seasonal_mad | 3 | 0.0% | False |
| hour | fraud | storage | Hot LRS Data Stored | seasonal_mad | 7 | 0.0% | True |
| day | fraud | storage | Hot LRS Data Stored | seasonal_mad | 7 | 1.9% | True |
| hour | fraud | training | Standard_NC4as_T4_v3 | seasonal_mad | 5 | 0.9% | True |
| day | fraud | training | Standard_NC4as_T4_v3 | seasonal_mad | 3 | 0.5% | False |
| hour | fraud | vector | Standard_D4s_v5 | seasonal_mad | 5 | 0.9% | True |
| day | fraud | vector | Standard_D4s_v5 | seasonal_mad | 3 | 0.0% | False |
| hour | fraud | warehouse | Standard_D4s_v5 | seasonal_mad | 5 | 0.8% | True |
| day | fraud | warehouse | Standard_D4s_v5 | seasonal_mad | 3 | 0.9% | False |
| hour | research | cpu | Standard_D4s_v5 | seasonal_mad | 5 | 0.7% | True |
| day | research | cpu | Standard_D4s_v5 | seasonal_mad | 3 | 0.0% | False |
| hour | research | inference | Standard_NC24ads_A100_v4 | seasonal_mad | 12 | 1.6% | False |
| day | research | inference | Standard_NC24ads_A100_v4 | seasonal_mad | 3 | 0.0% | False |
| hour | research | llm | gpt-6.1-terra cached | seasonal_mad | 5 | 0.9% | True |
| day | research | llm | gpt-6.1-terra cached | seasonal_mad | 3 | 0.9% | False |
| hour | research | llm | gpt-6.1-terra input | seasonal_mad | 5 | 0.9% | True |
| day | research | llm | gpt-6.1-terra input | seasonal_mad | 3 | 0.0% | False |
| hour | research | llm | gpt-6.1-terra output | seasonal_mad | 5 | 0.9% | True |
| day | research | llm | gpt-6.1-terra output | seasonal_mad | 3 | 0.0% | False |
| hour | research | network | Standard Data Transfer Out | seasonal_mad | 5 | 0.8% | True |
| day | research | network | Standard Data Transfer Out | seasonal_mad | 3 | 0.0% | False |
| hour | research | notebook | Standard_NC24ads_A100_v4 | seasonal_mad | 3 | 0.0% | False |
| day | research | notebook | Standard_NC24ads_A100_v4 | seasonal_mad | 3 | 0.0% | False |
| hour | research | storage | Hot LRS Data Stored | seasonal_mad | 7 | 0.0% | True |
| day | research | storage | Hot LRS Data Stored | seasonal_mad | 7 | 0.9% | True |
| hour | research | training | Standard_NC24ads_A100_v4 | seasonal_mad | 5 | 0.6% | True |
| day | research | training | Standard_NC24ads_A100_v4 | seasonal_mad | 3 | 0.0% | False |
| hour | research | vector | Standard_D4s_v5 | seasonal_mad | 5 | 0.8% | True |
| day | research | vector | Standard_D4s_v5 | seasonal_mad | 3 | 0.0% | False |
| hour | research | warehouse | Standard_D4s_v5 | seasonal_mad | 5 | 0.8% | True |
| day | research | warehouse | Standard_D4s_v5 | seasonal_mad | 3 | 0.0% | False |
| hour | search | cpu | Standard_D4s_v5 | seasonal_mad | 5 | 0.9% | True |
| day | search | cpu | Standard_D4s_v5 | seasonal_mad | 3 | 0.5% | False |
| hour | search | inference | Standard_NC6s_v3 | seasonal_mad | 12 | 1.5% | False |
| day | search | inference | Standard_NC6s_v3 | seasonal_mad | 3 | 0.0% | False |
| hour | search | llm | gpt-6.1-terra cached | seasonal_mad | 5 | 1.0% | True |
| day | search | llm | gpt-6.1-terra cached | seasonal_mad | 3 | 0.0% | False |
| hour | search | llm | gpt-6.1-terra input | seasonal_mad | 5 | 1.0% | True |
| day | search | llm | gpt-6.1-terra input | seasonal_mad | 3 | 0.0% | False |
| hour | search | llm | gpt-6.1-terra output | seasonal_mad | 5 | 1.0% | True |
| day | search | llm | gpt-6.1-terra output | seasonal_mad | 3 | 0.0% | False |
| hour | search | network | Standard Data Transfer Out | seasonal_mad | 5 | 0.9% | True |
| day | search | network | Standard Data Transfer Out | seasonal_mad | 3 | 0.0% | False |
| hour | search | storage | Hot LRS Data Stored | seasonal_mad | 7 | 0.1% | True |
| day | search | storage | Hot LRS Data Stored | seasonal_mad | 7 | 0.0% | True |
| hour | search | training | Standard_NC6s_v3 | seasonal_mad | 5 | 0.9% | True |
| day | search | training | Standard_NC6s_v3 | seasonal_mad | 3 | 0.5% | False |
| hour | search | vector | Standard_D4s_v5 | seasonal_mad | 5 | 1.0% | True |
| day | search | vector | Standard_D4s_v5 | seasonal_mad | 3 | 0.9% | False |
| hour | search | warehouse | Standard_D4s_v5 | seasonal_mad | 5 | 0.9% | True |
| day | search | warehouse | Standard_D4s_v5 | seasonal_mad | 3 | 0.0% | False |

## Limits and pushback

Zero-hour detections are boundary results from timestamped synthetic incidents, not evidence of zero production latency. Event recall and point precision answer different questions. Post-development SKUs with no calibration history are unscored.

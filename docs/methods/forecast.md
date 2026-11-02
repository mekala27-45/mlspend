# A forecast earns its interval.

mlspend is a portfolio demonstration. Its platform costs are simulated with known truth. Its portfolio costs are shadow estimates of public project usage at published list prices; nobody paid these amounts. No figure is a quote, an invoice or financial advice.

## Purpose

Seasonal naive, trend-seasonal and gradient boosting compete only on development history. Daily and monthly rolling-origin predictions are evaluated separately; intervals use earlier residuals.

## Inputs

UTC daily direct spend and workload from the observed mart, development-only model selection, earlier calibration residuals and rolling cutoff dates.

## Assumptions

Historical simulated patterns are relevant to the next horizon. Serial dependence weakens exchangeability; nominal coverage is a target rather than a guarantee. Monthly records abstain when calibration is insufficient.

## Score on the truth and observed results

All numeric tables below are rendered from results/expanded/manifest.json. Unit-economics arithmetic is checked on known fixtures; it is not an empirical model-quality result.


## Daily held-out scorecard



| Grain | Series | Selected | MAE USD/day | 90% interval coverage |
| --- | --- | --- | --- | --- |
| team | ads | seasonal_naive | $7.50 | 90.2% |
| team | assistant | seasonal_naive | $2.11 | 91.0% |
| team | forecasting | gradient_boosting | $3.39 | 90.2% |
| team | fraud | seasonal_naive | $2.16 | 89.3% |
| team | research | seasonal_naive | $21.61 | 93.4% |
| team | search | seasonal_naive | $49.76 | 90.2% |
| service | capacity | seasonal_naive | $16.74 | 90.2% |
| service | cpu | trend_seasonal | $0.01 | 86.9% |
| service | inference | seasonal_naive | $9.56 | 91.8% |
| service | llm | trend_seasonal | $0.14 | 86.1% |
| service | network | trend_seasonal | $56.87 | 87.7% |
| service | notebook | seasonal_naive | $7.11 | 93.4% |
| service | platform | seasonal_naive | $0.00 | 100.0% |
| service | storage | trend_seasonal | $0.09 | 93.4% |
| service | training | seasonal_naive | $12.35 | 86.9% |
| service | vector | trend_seasonal | $0.01 | 86.9% |
| service | warehouse | trend_seasonal | $0.02 | 86.9% |


## Monthly forecasts



| Series | Period | Point | Lower | Upper | Actual | Covered |
| --- | --- | --- | --- | --- | --- | --- |
| team/ads | 2025-09 | $796.38 | $781.71 | $811.05 | $824.77 | False |
| team/ads | 2025-10 | $858.21 | $839.67 | $876.75 | $2,152.56 | False |
| team/ads | 2025-11 | $828.13 | $0.00 | $2,119.73 | $831.85 | True |
| team/ads | 2025-12 | $892.18 | $0.00 | $2,541.18 | $900.45 | True |
| team/assistant | 2025-09 | $3,744.11 | $3,159.56 | $4,328.67 | $3,806.14 | True |
| team/assistant | 2025-10 | $3,951.30 | $3,868.66 | $4,033.94 | $4,026.08 | True |
| team/assistant | 2025-11 | $3,818.73 | $3,735.95 | $3,901.52 | $3,815.01 | True |
| team/assistant | 2025-12 | $4,105.94 | $4,031.17 | $4,180.72 | $4,119.19 | True |
| team/forecasting | 2025-09 | $4,032.84 | $3,943.11 | $4,122.57 | $4,118.30 | True |
| team/forecasting | 2025-10 | $4,241.83 | $4,119.29 | $4,364.36 | $4,353.53 | True |
| team/forecasting | 2025-11 | $4,065.47 | $3,948.56 | $4,182.38 | $4,160.30 | True |
| team/forecasting | 2025-12 | $4,375.02 | $4,250.83 | $4,499.21 | $4,507.81 | False |
| team/fraud | 2025-09 | $980.89 | $962.04 | $999.74 | $1,102.88 | False |
| team/fraud | 2025-10 | $1,051.94 | $921.24 | $1,182.64 | $1,059.56 | True |
| team/fraud | 2025-11 | $1,000.65 | $630.73 | $1,370.58 | $1,012.00 | True |
| team/fraud | 2025-12 | $1,083.67 | $714.71 | $1,452.63 | $1,090.05 | True |
| team/research | 2025-09 | $6,402.90 | $6,267.98 | $6,537.82 | $7,092.67 | False |
| team/research | 2025-10 | $6,611.94 | $5,864.43 | $7,359.46 | $6,783.06 | True |
| team/research | 2025-11 | $6,379.18 | $3,691.12 | $9,067.24 | $7,012.86 | True |
| team/research | 2025-12 | $6,936.16 | $4,246.71 | $9,625.60 | $6,950.95 | True |
| team/search | 2025-09 | $5,005.70 | $4,902.02 | $5,109.38 | $5,053.58 | True |
| team/search | 2025-10 | $5,303.01 | $5,199.16 | $5,406.86 | $8,194.42 | False |
| team/search | 2025-11 | $5,040.10 | $2,106.53 | $7,973.67 | $5,097.52 | True |
| team/search | 2025-12 | $5,447.74 | $0.00 | $16,854.63 | $5,475.03 | True |
| service/capacity | 2025-09 | $7,736.61 | $6,391.44 | $9,081.78 | $7,198.27 | True |
| service/capacity | 2025-10 | $7,760.96 | $7,234.25 | $8,287.68 | $7,626.59 | True |
| service/capacity | 2025-11 | $7,750.49 | $6,322.55 | $9,178.43 | $7,151.47 | True |
| service/capacity | 2025-12 | $7,610.94 | $6,154.02 | $9,067.86 | $7,608.29 | True |
| service/cpu | 2025-09 | $110.20 | $109.81 | $110.58 | $110.50 | True |
| service/cpu | 2025-10 | $117.32 | $116.93 | $117.70 | $116.72 | False |
| service/cpu | 2025-11 | $111.06 | $110.62 | $111.50 | $111.16 | True |
| service/cpu | 2025-12 | $120.65 | $120.07 | $121.23 | $120.65 | True |
| service/inference | 2025-09 | $15,066.51 | $14,723.65 | $15,409.36 | $15,205.62 | True |
| service/inference | 2025-10 | $15,887.75 | $15,691.68 | $16,083.82 | $17,330.07 | False |
| service/inference | 2025-11 | $15,171.61 | $13,695.77 | $16,647.46 | $15,326.80 | True |
| service/inference | 2025-12 | $16,356.34 | $14,836.18 | $17,876.50 | $16,549.82 | True |
| service/llm | 2025-09 | $1,117.84 | $1,113.95 | $1,121.73 | $1,121.03 | True |
| service/llm | 2025-10 | $1,190.47 | $1,186.60 | $1,194.35 | $1,184.21 | False |
| service/llm | 2025-11 | $1,126.71 | $1,122.21 | $1,131.22 | $1,127.70 | True |
| service/llm | 2025-12 | $1,224.06 | $1,218.21 | $1,229.91 | $1,224.15 | True |
| service/network | 2025-09 | $138.71 | $138.22 | $139.19 | $139.08 | True |
| service/network | 2025-10 | $147.66 | $147.18 | $148.15 | $3,070.12 | False |
| service/network | 2025-11 | $54.19 | $0.00 | $2,977.72 | $139.91 | True |
| service/network | 2025-12 | $151.86 | $0.00 | $29,862.21 | $151.86 | True |
| service/notebook | 2025-09 | $808.06 | $808.06 | $808.06 | $808.06 | True |
| service/notebook | 2025-10 | $844.79 | $844.79 | $844.79 | $844.79 | True |
| service/notebook | 2025-11 | $734.60 | $734.60 | $734.60 | $1,307.59 | False |
| service/notebook | 2025-12 | $844.79 | $271.80 | $1,417.78 | $844.79 | True |
| service/platform | 2025-09 | $276.48 | $276.48 | $276.48 | $276.48 | True |
| service/platform | 2025-10 | $285.70 | $285.70 | $285.70 | $285.70 | True |
| service/platform | 2025-11 | $276.48 | $276.48 | $276.48 | $276.48 | True |
| service/platform | 2025-12 | $285.70 | $285.70 | $285.70 | $285.70 | True |
| service/storage | 2025-09 | $79.66 | $76.38 | $82.94 | $96.66 | False |
| service/storage | 2025-10 | $105.39 | $90.71 | $120.07 | $101.99 | True |
| service/storage | 2025-11 | $103.85 | $83.45 | $124.26 | $107.32 | True |
| service/storage | 2025-12 | $116.40 | $94.69 | $138.11 | $112.64 | True |
| service/training | 2025-09 | $3,661.28 | $3,565.81 | $3,756.75 | $4,509.23 | False |
| service/training | 2025-10 | $3,874.93 | $3,025.95 | $4,723.91 | $3,913.76 | True |
| service/training | 2025-11 | $3,690.55 | $1,016.94 | $6,364.16 | $3,726.06 | True |
| service/training | 2025-12 | $4,000.57 | $1,324.99 | $6,676.16 | $4,057.78 | True |
| service/vector | 2025-09 | $73.47 | $73.21 | $73.72 | $73.67 | True |
| service/vector | 2025-10 | $78.21 | $77.95 | $78.47 | $77.81 | False |
| service/vector | 2025-11 | $74.04 | $73.75 | $74.33 | $74.10 | True |
| service/vector | 2025-12 | $80.43 | $80.05 | $80.82 | $80.43 | True |
| service/warehouse | 2025-09 | $122.44 | $122.02 | $122.87 | $122.78 | True |
| service/warehouse | 2025-10 | $130.35 | $129.92 | $130.78 | $129.69 | False |
| service/warehouse | 2025-11 | $123.40 | $122.91 | $123.89 | $123.51 | True |
| service/warehouse | 2025-12 | $134.06 | $133.41 | $134.70 | $134.06 | True |


## Budget burn · latest observation



| Series | Date | Budget | Spent | Month-end projection | Exhaustion day | Severity |
| --- | --- | --- | --- | --- | --- | --- |
| team/ads | 2025-12-31 | $900.69 | $900.45 | $900.45 | 32 | warning |
| team/assistant | 2025-12-31 | $4,145.33 | $4,119.19 | $4,119.19 | 32 | warning |
| team/forecasting | 2025-12-31 | $4,488.94 | $4,507.81 | $4,507.81 | 31 | critical |
| team/fraud | 2025-12-31 | $1,079.56 | $1,090.05 | $1,090.05 | 31 | critical |
| team/research | 2025-12-31 | $7,012.36 | $6,950.95 | $6,950.95 | 32 | warning |
| team/search | 2025-12-31 | $5,518.14 | $5,475.03 | $5,475.03 | 32 | warning |
| service/capacity | 2025-12-31 | $9,033.82 | $7,608.29 | $7,608.29 | 37 | warning |
| service/cpu | 2025-12-31 | $120.36 | $120.65 | $120.65 | 31 | critical |
| service/inference | 2025-12-31 | $16,631.52 | $16,549.82 | $16,549.82 | 32 | warning |
| service/llm | 2025-12-31 | $1,220.90 | $1,224.15 | $1,224.15 | 31 | critical |
| service/network | 2025-12-31 | $151.49 | $151.86 | $151.86 | 31 | critical |
| service/notebook | 2025-12-31 | $848.46 | $844.79 | $844.79 | 32 | warning |
| service/platform | 2025-12-31 | $314.27 | $285.70 | $285.70 | 35 | warning |
| service/storage | 2025-12-31 | $85.52 | $112.64 | $112.64 | 24 | critical |
| service/training | 2025-12-31 | $4,034.88 | $4,057.78 | $4,057.78 | 31 | critical |
| service/vector | 2025-12-31 | $80.24 | $80.43 | $80.43 | 31 | critical |
| service/warehouse | 2025-12-31 | $133.73 | $134.06 | $134.06 | 31 | critical |


## Prospective simulated month: 2026-01

Separate registered simulation. Forecasts were saved before outcomes were generated. A single simulated month does not establish production accuracy. Source: results/prospective/close.json.

| Team | Forecast USD | Interval USD | Simulated actual USD | Absolute error USD | Covered |
| --- | --- | --- | --- | --- | --- |
| ads | 2754.37333 | 1390.635891 to 4118.110769 | 1782.500086 | 971.873244 | True |
| assistant | 5016.153943 | 4792.85427 to 5239.453616 | 6078.170624 | 1062.016681 | False |
| forecasting | 5488.253824 | 4983.7639 to 5992.743748 | 7169.045001 | 1680.791177 | False |
| fraud | 2233.508861 | 1962.006684 to 2505.011038 | 2793.00458 | 559.495719 | False |
| research | 8517.767993 | 7823.778914 to 9211.757072 | 8321.983586 | 195.784407 | True |
| search | 7582.090179 | 6594.64455 to 8569.535808 | 6203.944277 | 1378.145902 | False |


## Prospective close verification

Recording timestamps use actual UTC; the simulated calendar is separate. Real December forecasts remain pending.

| Check | Result |
| --- | --- |
| Forecasts independently read before outcomes | 6 |
| Records scored and independently verified | 6 |
| Observed interval coverage | 2/6 |
| Updates on a repeated close | 0 |
| Calendar forecasts preserved | 2 |
| Simulation ID | prospective-41475604592-1 |
| Workflow run | 41475604592 |


## Sensitivity and interior checks

The development scorecard compares every registered candidate. Held-out MAE, empirical coverage, team-cluster uncertainty and monthly interval status remain visible. Future-row mutation tests leave earlier forecasts unchanged.

## Limitations

Team forecasts use direct spend, while statements include shared allocation. Serial dependence can invalidate nominal conformal coverage. Inadequate monthly calibration produces an unavailable interval. Live future forecasts are kept separate from these synthetic backtests.

## What a reviewer would push back on

A finance lead should ask whether the horizon is direct or fully loaded spend, whether changes are structural and whether intervals are calibrated on completed horizons. Historical backtests and future real forecast logs remain separate.

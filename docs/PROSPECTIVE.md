# Prospective simulated-month verification

The original specification permits a future simulated month or a future real portfolio month. This supplemental check uses the simulation option. It does not accelerate the calendar clock or turn synthetic outcomes into observed usage.

The plan, observed monthly history and their digests were registered in commit `0308a7a07398b9b7f587d852b0e8ff8abf2df7b8` before generating this check's outcomes. The historical study was already known, so this is an additional persistence and scoring experiment rather than a new preregistered accuracy claim about that study.

## Sequence and evidence

The issue job computes forecasts from previously observed allocation costs, sends them to the deployed API and reads each unscored record through a separate database connection. It uploads that evidence before the close job can begin. Only the evaluation close job imports the new outcome generator. It advances the simulation clock, stores the actuals using the restricted close role, reads every score from both SQL and HTTP, and repeats the close to verify that no record is changed twice.

`created_at` and `scored_at` always use the actual recording time. `data_cutoff`, `period` and `simulated_close` describe the explicitly labeled simulated calendar. Every simulated request carries a simulation ID and the registered plan digest, and uses the `simulation_forecast` record kind. The calendar close selects only the original `forecast` kind. The simulation close selects only its own simulation ID. The verifier compares all calendar record scores before and after the experiment.

The workflow is `.github/workflows/prospective-close.yml`. Its issue and close stages are separate jobs, and the close depends on successful issuance. Successful evidence is published to an evidence branch and retained as an Actions artifact. The final verified artifact is promoted to `results/prospective/`; generated reports must read those exact bytes.

## Interpretation

The registered model uses a trailing monthly mean and an interval derived from prior residuals. A single new simulated month checks the complete forecast-to-score sequence. It is too small to establish production accuracy or calibrated coverage. The registered outcome distribution and known historical study limit generalization. The original daily and monthly backtests remain unchanged.

Real December portfolio forecasts remain pending until the calendar month ends and complete actual usage is fetched. A successful simulation is never reported as a completed real December close.

# Hosted verification

The working API and dashboard are available at https://mlspend.vercel.app. The application uses Vercel's FastAPI runtime and Neon Postgres. This is a working demonstration, not a completed release against the original brief.

## Verified deployment

Production deployment `dpl_F13z4sWWG1v3w64CDkrGWr1aS3EC` was built from commit `bfe65df8d48c6505d5c760e1e552eceef88ed256`. It passed a preview check before the production build. Both environments use the configured project database and hashing salt; neither credential is committed.

The [build and verification run](https://github.com/mekala27-45/mlspend/actions/runs/41258404682) passed all 47 Python tests, six browser-client tests, strict type checking, lint, the HTTP persistence check, two dbt models with five data tests, and repeated builds with different hash seeds. Its validation artifact contains the machine-readable results. These results apply to that commit.

The [hosted persistence run](https://github.com/mekala27-45/mlspend/actions/runs/41258269171) passed on its second attempt after the deployment fix. The first attempt correctly caught a server error. The successful check exercised database health, dashboard HTML, showback, unit costs, anomalies, one estimate POST, and a separate GET of the saved estimate. `results/hosted-validation.json` is the unmodified JSON emitted by that check. A direct Neon read independently found the same estimate ID, payload and result.

## Failure and regression coverage

PostgreSQL treats `window` as a reserved keyword. The original budget query left that column unquoted, so normal requests failed while the health query still passed. The corrected query quotes it in both the INSERT and conflict target. PostgreSQL regression tests now exercise concurrent budget updates and actual API requests, rather than only checking direct log storage.

If a POST response is lost, the client reports that persistence is unknown and does not automatically retry. It only reports an estimate as not submitted when the API readiness check failed before the POST. The submit button is disabled while a request is running.

## Running the checks again

Run `python -m scripts.check_hosted --url https://mlspend.vercel.app` from a checkout with outbound HTTPS access, or dispatch the Verify hosted persistence workflow. Each successful run creates one small test estimate and records its identifier. Do not delete unrelated request logs to clean up a test.

Run the Build and verify workflow to exercise ephemeral PostgreSQL, SQLite, dbt and deterministic builds. The managed Windows session can run the direct storage and JavaScript tests, but its socket restrictions prevent the complete HTTP suite from running locally.

## Remaining limits

These checks establish HTTP behavior and persistence. They do not establish browser rendering, measured cold-start distributions, actual provider billing, complete FOCUS conformance, full portfolio coverage or completion of the analytical requirements. No release tag is created by these workflows. Consult RESULTS.md before describing the project as complete.

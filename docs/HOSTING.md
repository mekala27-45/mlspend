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

## Pages and browser verification

The Next.js static export is published at https://mekala27-45.github.io/mlspend/. The Pages run https://github.com/mekala27-45/mlspend/actions/runs/41259117796 passed build, strict TypeScript, and four Chromium tests before publishing commit 0e86d616f1c6f538d0218bbf71ab6295456fe8d7. Tests cover every route at 1280 and 390 pixels, theme switching, the first-503 readiness retry, uncertain POST handling, and a real DuckDB-WASM query of the complete monthly table. Browser screenshots and the npm lockfile are preserved in that run. Later promoted data require a new run; these results remain scoped to the named commit.

An owner-browser check of the Vercel estimator submitted 19 requests per day for one day on the T4 rate. The page returned reference b17d05ff-5ab3-457a-a292-3e4a6395aa66 and a shadow estimate of USD 12.624. An independent Neon SELECT found the same identifier, payload and result. This establishes the browser-to-database path for that deployment, without changing authentication settings or creating a share link.

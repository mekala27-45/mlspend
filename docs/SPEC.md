Deviations from this specification are recorded in DECISIONS.md.

## 1. What we are building

mlspend is a cost observability platform for ML and AI workloads with two books. The platform book is a simulated ML platform with six teams, their models, experiments, training jobs, inference endpoints, a shared GPU cluster, LLM API usage, storage, network and commitments, emitted as FOCUS 1.4 datasets and workload telemetry, with the true consumption, waste, incidents and savings kept in truth tables no method can read. The portfolio book is the real usage of every public build of its author (CI minutes, GPU minutes, model tokens, API requests and compute), measured from the GitHub API and the committed ledgers of each build. Both are priced from a price book that Actions fetches from public sources and locks. A dbt warehouse over DuckDB stages, allocates and reconciles them. The allocation engine charges workloads the larger of request and usage, measures idle, distributes shared costs three ways and computes the Shapley value of the shared cluster as a fairness reference. Unit economics give average and marginal cost per prediction, per answer and per training run. Forecasts, budgets, an anomaly detector, rightsizing and model switch recommendations and a commitment optimizer are each graded against the simulator truth on held-out months registered before they were opened. An API on Vercel answers showback, unit cost and estimate requests, logs forecasts to be scored when the month closes, and meters its own cost in a header. The site shows the statement, allocation, unit economics, anomalies, forecasts, recommendations, commitments, the portfolio bill, a live estimator and the data.

The reader is a hiring manager for an ML platform or MLOps engineer, or a FinOps lead, deciding in ten minutes whether this person can own a bill, not just chart one.

## 2. Hard constraints

- **The eighteen mandatory steps in section 17 are the product.** The build is not done while any of them is missing, and the README first paragraph says which are missing until none are.
- **The API is deployed at step nine,** live on Vercel with the forecast log in Neon, verified from a separate client. The API container ships as a health stub in step one so the host import happens in the first hour.
- **Every price has a source.** The price book is fetched in Actions from the public sources in Part 2, normalized, digested and locked; a price transcribed from a page carries its URL, the date read and a digest of the page. A test fails on any price used anywhere that is not in the locked book.
- **Shadow prices are labeled everywhere.** Every portfolio figure says shadow cost at list price, read on a date; no page, document or response calls it a bill, a charge or a saving actually made.
- **The truth tables are sealed.** Simulator truth lives in packages/truth and the allocation, detection, forecasting and recommendation packages cannot import it; a test proves the import fails. Only packages/evaluation reads both.
- **The plan is registered first.** The development and held-out months, the allocation method of record and its reason, the detector thresholds, the forecast windows, the scoring rules for recommendations and commitments, the interior tests and the hypotheses are hashed and committed before the first held-out month is scored.
- **Every row in its window.** Every charge of the simulated bill, every workflow run and job of every public repository in the window, every row of every ledger read, every price in the book; nothing sampled. A test asserts the reconciled totals equal the source totals.
- **Actions holds every token.** The GitHub token Actions provides is enough for the public usage fetch; an optional read only Neon role for the API logs of earlier builds lives only in Actions secrets. A scan in CI and in a pre-push hook fails on anything that looks like a credential in any tracked file or commit diff.
- **Free tier only, no card.** Vercel Hobby, Neon, GitHub Pages, Actions and Releases. The probe runs before the first deploy and every deploy step reads it.
- **The statement on every surface**, gated: every page, every API response, every statement and export. **No em dashes anywhere.** The vocabulary gate.
- **Every number in a document is rendered from the manifest** by the Day 3 renderer, whole file diff in CI.
- **At least forty conventional commits,** made as the build proceeds, one module at a time, with the tag pushed after the commits. The count is a floor. Pushed history is never rewritten.

## 3. Stack

```
Core            Python 3.12, uv workspace, StrictModel ported from trajectory,
                Pydantic v2 for every contract, request and response; Decimal
                for money at the boundary, float only inside numerical work
Warehouse       DuckDB with dbt-duckdb; the quarantine contract and the metric
                layer from cityflow; reconcile at four grains
Billing schema  FOCUS 1.4 for the Cost and Usage and Contract Commitment
                datasets; the FinOps Foundation focus_validator (MIT) at the
                newest specification version it supports, recorded; if that is
                older than 1.4, the 1.4 column requirements the specification
                states become conformance tests of the build, noted in
                DECISIONS.md
Allocation      packages/allocation: OpenCost style asset, workload, idle and
                shared cost; exact Shapley for the shared cluster
Statistics      packages/forecast (rolling origin, seasonal models, conformal
                intervals), packages/detect (robust residual scores and
                changepoints), packages/optimize (commitment sizing, rightsizing),
                packages/evaluation (scores against truth, cluster bootstrap,
                Benjamini-Hochberg, interior tests, message rules)
Fetch           httpx in Actions for the price sources and the GitHub API, with
                ETag caching, rate limit handling and resume
API             FastAPI, async, deployed as a Vercel container (Dockerfile.vercel,
                port 80); SQLModel over Neon for the forecast log, the estimate
                log and the client budget; Alembic with the versioned table
                pattern from Day 13
Rendering       the Day 3 claim gate renderer, Jinja templates, the manifest
Exports         a FOCUS conformant parquet of allocated costs; Power BI and
                Tableau extracts with their measures; an Excel showback workbook
                with live formulas (openpyxl)
Web             Next.js 16, TypeScript strict, Tailwind v4, static export on GitHub
                Pages, DuckDB-WASM over the committed results, the series SVG chart
                library, link prefetch off
Quality         ruff, mypy strict, pytest, hypothesis, testcontainers for Postgres,
                nbmake, skills-ref, Playwright against a test server that refuses
                HEAD and answers a first 503, 80 percent coverage floor
Logging         structlog, JSON, ids and digests only, never a token
```

## 4. Architecture

```
  SOURCES     price book: Azure Retail Prices API, AWS Price List Bulk API,
              GitHub billing docs, provider and platform price pages
              portfolio usage: GitHub API (runs and jobs of every public repo),
              committed ledgers of friction, headroom, goodhart, trajectory,
              readback; optional API logs from Neon (read only role)
              simulator: six teams, twelve months of hourly workloads
        |
        v  fetch in Actions, digest, lock     data/sources.lock.json, PROVENANCE.md
        v  normalize                          price book (one schema, locked)
        v  simulate                           FOCUS 1.4 datasets, telemetry, and
                                              sealed truth tables
        v  validate                           focus_validator, quarantine rules
   +--------------------------------------------------------------------------+
   |  WAREHOUSE (dbt over DuckDB)                                             |
   |    staging   focus_cost_usage, focus_commitments, telemetry, usage       |
   |    prices    the locked book joined by SKU, unit and effective date      |
   |    alloc     asset, workload (max of request and usage), idle, shared    |
   |    unit      cost per 1,000 predictions, per answer, per run, marginal   |
   |    books     the platform book, the portfolio book                       |
   |    metrics   the metric layer, reconciled at four grains                 |
   +--------------------------------------------------------------------------+
        |
        v  forecast, detect, recommend, optimize   graded by packages/evaluation
        v  manifest.json > renderer > README, RESULTS, statements, method notes
        v
   VERCEL      /v1/showback  /v1/unit-costs  /v1/estimate  /v1/forecasts
               /v1/anomalies  /health; Neon: forecast log, estimate log, budget;
               every response carries its own shadow cost
   PAGES       statement, allocation, unit, anomalies, forecast,
               recommendations, commitments, portfolio, estimate, data, report
   EXPORTS     FOCUS allocated parquet, Power BI, Tableau, Excel showback
```

State in ARCHITECTURE.md, in plain sentences: why FOCUS and not a homemade schema; why the larger of request and usage and what it does to bursty workloads; why idle is shown as its own line before any distribution; why Shapley is a reference and not the method of record; why the portfolio book uses list prices and what negotiated rates, credits and free tiers change; why the truth is sealed; why Actions does every fetch.

## 5. The two books and the price book

**The price book.** scripts/fetch_prices.py runs in Actions from a committed request: the Azure Retail Prices API for the GPU and CPU virtual machine SKUs the simulator and the portfolio use (the T4 and A100 classes among them, listed by exact SKU in the request file), on demand, spot, reservation and savings plan, plus storage and egress; the AWS Price List Bulk API for the equivalent instance families (G4dn for T4, G6 for L4, P4d for A100), on demand and reserved; the GitHub billing page for the per minute runner rates; the pricing pages of every model provider and platform that appears in a ledger, transcribed into data/prices/manual.yaml with URL, date and page digest. Everything normalizes to one schema: provider, service, SKU, region, unit, list price, currency, term, effective date, source, digest. The book is locked by digest; a second fetch a month later is diffed, and the price changes are a page.

**The platform book, simulated with known truth.** packages/simulator generates twelve months of hourly workloads for six teams (search, ads, fraud, forecasting, assistant, research), each with models and versions, experiments, training jobs, inference endpoints and LLM API usage, on a shared GPU cluster with three node pools, CPU batch, a vector store, object storage in tiers, network egress, a data warehouse, notebooks and shared platform services (logging, monitoring, the feature store). It has commitments (a one year and a three year commitment at stated levels), spot capacity with interruptions and retries, and a stated share of untagged resources. Every workload records what it requested and what it used, per hour. The simulator writes FOCUS 1.4 Cost and Usage rows (charge period, service category and name, SKU, resource id and type, region, consumed and pricing quantity and unit, list, contracted, billed and effective cost, commitment discount columns, charge category, tags) and Contract Commitment rows, plus workload telemetry (pod requests and usage per hour, inference request logs with tokens and GPU milliseconds, training job records with experiment ids and status). Prices come from the locked book. Seeded, sorted before every sample, digested.

**The planted waste and incidents,** in config/incidents.yaml, each with its start, end and true cost, sealed in the truth tables: a hyperparameter sweep that retries itself over a weekend; an endpoint autoscaler with a minimum replica count three times what traffic needs; a notebook with a GPU left running for nine days; a retry storm on spot interruptions; a data export that spikes egress; a mid year price change on one SKU; duplicated training data in hot storage; an untagged batch job owned by one team. The truth also holds the counterfactual cost of every recommendation the build can make, computed by rerunning the simulator with the change applied.

**The portfolio book, real.** scripts/fetch_portfolio_usage.py runs in Actions over every public repository of the author: workflow runs and their jobs from the GitHub REST API (runner labels, started and completed times; minutes computed per job and rounded up to the whole minute as GitHub bills, never read from a usage endpoint), release asset and artifact sizes, repository sizes. Then the committed ledgers of the builds that have them on the day: friction (compute seconds per task and run), headroom and goodhart (GPU seconds by phase, tokens, peak memory), trajectory (the model panel runs, with token counts from the run records or, where a record has none, counted with each model tokenizer and labeled as counted), readback (provider calls and tokens from its runs and cassettes). With the optional read only Neon role, the API request logs of any earlier build that keeps them give request counts and latency percentiles per build per day; only those aggregates leave the database, never a row, an address or a hash, and the probe lists which builds have logs. Each usage row is priced at the list price of its closest paid equivalent in the book (a free T4 minute at the on demand price of a one T4 virtual machine, a public repository CI minute at the private rate, a free tier token at the paid price of the same model), and each mapping is a row in data/portfolio_mapping.yaml with its reason. A usage row with no paid equivalent is marked not priced, never guessed.

**The first look, before any method runs.** Profile both books at full size: rows, nulls, ranges, units, charge categories, the share of rows with each tag, the time span, and the ten strangest rows of each. The first ten real defects (in the simulated bill, in the GitHub data, in the ledgers) become quarantine rules, each with a test. The FOCUS validator runs on every simulated file, and its report is committed.

## 6. The warehouse and the allocation engine

**Staging.** dbt models stage FOCUS, telemetry, portfolio usage and the price book with contracts per table (columns, types, units, keys, classification), the quarantine contract from cityflow, and a test that the staged totals equal the source totals per billing period.

**Asset and workload cost, the OpenCost way.** Asset cost is what the cluster capacity cost per hour from the bill. Workload cost for an allocation priced resource (GPU, CPU, memory) is the larger of request and usage times the hourly rate, computed per container hour and aggregated up; usage priced resources (egress, tokens, storage bytes) are charged by use. Idle cost is asset cost minus workload cost, shown as its own line before any distribution, by pool and by hour.

**Shared and idle distribution, four ways.** Even split across teams; proportional to the direct cost of each team; by a custom metric (GPU hours for the cluster, requests for the platform services); and the Shapley value of the shared GPU cluster as a fairness reference, computed exactly over the six teams with a coalition cost function that prices the capacity each coalition would need at its own peak percentile. The method of record is registered with its reason; the page shows the bill of every team under all four and the largest move.

**Commitments.** Effective cost amortizes commitments over their term (the FOCUS effective cost against billed cost), with coverage (the share of eligible usage covered) and utilization (the share of commitment used) per hour.

**Untagged spend.** Coverage of the owner tag by spend, before and after inference: a classifier predicts the owner of untagged resources from their metadata (name pattern, network, schedule, the jobs that touch them), graded on the sealed truth with precision and recall; low confidence assignments stay unallocated and are counted.

**The metric layer.** Spend, effective spend, idle, waste, unit costs and coverage defined once with two expressions each (over the charge grain and over the shipped aggregates), reconciled at four grains (team, model, month, day) with a stated float tolerance and zero tolerance on counts.

## 7. Unit economics and the portfolio bill

**Cost per prediction, two ways.** For every endpoint and model version: fully loaded average cost per 1,000 predictions (direct, idle share and shared share under the method of record), and the marginal cost of the next 1,000 at the current utilization (near zero while idle capacity absorbs them, the cost of the next replica when it cannot). Cost per answer for LLM endpoints splits tokens, infrastructure and shared cost. Cost per training run and per experiment, with failed and retried runs counted where they belong.

**The portfolio bill.** For every public build: shadow cost by component (CI, GPU, tokens, API, storage) for the window, and the cost of its unit of output where the build has one: one cityflow monthly refresh, one readback answer, one trajectory panel run, one goodhart GRPO step, one doorstep API request, one friction pipeline run. Each with the usage source, the price source and the date read.

## 8. Forecasts, budgets and the forecast log

**Forecasts.** Monthly and daily spend per team and per service, from rolling origin backtests over the development months (seasonal naive, a trend and seasonality model, and gradient boosting on calendar and workload features), with conformal intervals at the registered level; the chosen model by rule on development, reported on the held-out months, with interval coverage.

**Budgets.** A budget per team per month in config/budgets.yaml, burn rate against budget per day, and the alert that fires when the forecast interval crosses the budget, with the day it would have fired.

**The forecast log.** POST /v1/forecasts writes a forecast for a future simulated month (or for the next real month of the portfolio CI minutes) with its interval, before the period closes; a scheduled workflow closes the period and scores every forecast logged for it. The log is the evidence that the forecasts were made before the answers existed.

## 9. Anomaly detection and the incident

**The detector.** Daily and hourly cost per team, service and SKU; residuals from the forecast; a robust score and a changepoint test; thresholds chosen on development months under a registered false alarm budget, reported on held-out months. Graded on the planted incidents: precision, recall, median detection delay in hours, and dollars burned before detection, with the interior test on the threshold.

**The incident.** The weekend sweep is written up as an incident: the timeline from the bill and the telemetry, when the detector fired and how many dollars had burned by then, what a budget alert alone would have caught and when, the root cause, and three actions, one of them a guardrail (a retry limit or a spend cap per job) with the dollars it would have saved on the truth. docs/incidents/<date>-weekend-sweep.md, blameless and specific.

## 10. Recommendations and the commitment optimizer

**Recommendations,** each with an estimated monthly saving and its interval, graded against the sealed counterfactual: rightsizing endpoints by utilization with a registered headroom; moving eligible training to spot with the retry cost included; removing the replica floor; tiering cold storage; deleting duplicated data; stopping idle notebooks after a registered timeout; and model switches where a cheaper model holds quality, using a quality metric the simulator records per model and, for the portfolio, quality figures the builds themselves measured and published, cited by file and never assumed (the goodhart methods table at one ceiling, if it exists on the day). Publish estimated against true savings per recommendation, the error, and the share of total waste the recommendations recover.

**The commitment optimizer.** Choose the commitment level per pool that minimizes expected cost under the usage distribution from the development months (a newsvendor style trade between unused commitment and on demand overflow), with the regret of buying 20 percent less or more, graded on the held-out months, with the interior test on the level.

## 11. Exports, statements and method notes

**Showback statements.** One statement per team per month, rendered by the claim gate like a bank statement: opening forecast, charges by category, idle and shared lines under the method of record, the other three methods in a footnote table, unit costs, anomalies, recommendations, and the statement.

**Exports.** A FOCUS conformant parquet of allocated costs with the allocation tags (FOCUS Allocated Tags), validated; Power BI and Tableau extracts of the metric marts with their measures; an Excel showback workbook with live formulas for the allocation methods, so a finance reader can change the method and watch the bills move.

**Method notes,** one per method (allocation, unit economics, forecasting, detection, recommendations, commitments): purpose, inputs, assumptions, the score on the truth, sensitivity from the interior tests, limitations, and the pushback paragraph. Rendered by the claim gate, refusing to render with a section missing.

## 12. Serving: the API that meters itself

**The API,** FastAPI in a Vercel container. GET /v1/showback (team, month, method), GET /v1/unit-costs (model version, month), POST /v1/estimate (a workload description: model size class, tokens in and out per request, requests per day, hosting option; returns the cost under each option with the assumptions and the price rows used), POST /v1/forecasts and GET /v1/forecasts/{id}, GET /v1/anomalies, GET /health (version, the price book digest, the data digests, the statement). Every estimate and forecast is written to Neon before the response. A client budget of 60 requests an hour per hashed client address.

**The meter.** Every response carries a header with the shadow cost of serving it: the measured CPU time and memory of the request, priced at the paid tier rates of the host from the price book, with the price row ids. The health page shows the median and p99 shadow cost per request.

**Persistence tests.** test_forecast_is_committed from an independent connection; test_estimate_logged_before_response; the CI out of process check that starts the container, posts a forecast and reads it back from a separate process.

**Latency.** A load test through the live API with the cold start measured separately, p50 and p99.

## 13. The repository surface for agents

AGENTS.md as the single source (setup, tests, gates, the files an agent must not edit: the lock files, the price book, the plan, the truth tables, the results promoted from Actions except through promotion); CLAUDE.md and .github/copilot-instructions.md as one paragraph each pointing at it; three skills in .claude/skills validated with skills-ref: add-a-price-source (the fetch, the schema, the digest, the lock), add-a-cost-rule (an allocation or waste rule with its three tests and its score on the truth), explain-a-bill (how to answer a question about a team bill from the marts, every number read back from the manifest). docs/SPEC.md holds sections 1 to 21 of this prompt as the specification, with a line at the top saying deviations are in DECISIONS.md; the opening paragraph of the prompt is not part of it. docs/adr/ holds one architecture decision record per choice named in section 4, each with the alternatives and why they lost. The playbook page renders AGENTS.md and the skills.

## 14. What the build must measure

At the end, the manifest holds at least: total simulated spend by month with effective against billed; idle share by pool; the largest bill move between allocation methods and the team it belongs to; Shapley against the method of record per team; tag coverage before and after inference with precision and recall; average and marginal cost per 1,000 predictions per model version; cost per answer split by component; forecast error and interval coverage on held-out months; detector precision, recall, median delay and dollars burned before detection; estimated against true savings per recommendation and the share of waste recovered; the commitment level chosen and its regret band; the portfolio bill by build and component, and the cost of each unit of output; the price changes between two fetches if a second fetch exists; and the API shadow cost per request.

## 15. The site and the visual system

Static export on GitHub Pages, DuckDB-WASM over the committed results, the live API for the estimator and the forecast log, and a recorded session so every page works when the API is asleep, labeled as recorded, with the site probing twice.

**Art direction.** The columnar pad. Light first: pale green paper, faint blue horizontal rules, red double vertical rules before the totals column, statement headings in Besley, every figure right aligned in Recursive Mono Linear with tabular numerals, negatives in parentheses, a single rule above each total and a double rule below it. Dark is the carbon copy: indigo carbon with pale violet impressions. Dense tables on the statement, allocation, unit and portfolio pages. Nothing decorative beyond the ruling.

**Surfaces and ink,** both validated:

```
Light surface   #EAF2E3    dark surface    #1A1B2E    card   #FBFDF9 light, #23243A dark
Primary ink     #1C2420    primary ink     #E6E4F2    rules  #B9CBE0 light (blue ruling),
Secondary ink   #4D5A52    secondary ink   #A9A7C2           #34355A dark
Control gray    #67736B    control gray    #8A88A6    total  #C9504D light, #8E5A78 dark
                                                      (rules and total rules are
                                                       decoration, never data)
```

**Categorical palette, fixed order.** Light: #24489E, #9C6A00, #A82235, #6B44C6, #3D7A2E, #A0367F, #7A4A26, #0E7C86. Dark: #8FA8F2, #E8C066, #EE6D7F, #C3ACF8, #6CC06E, #EE9ADB, #C99A66, #62D0D2. Measured on 31 October with the series validator (scripts/validate_palette.js from readback, config mode, both modes): zero failures; worst adjacent color vision deficiency separation 9.1 light and 12.5 dark against a target of 8; worst normal vision separation 16.5 and 17.6 against a floor of 12; every light slot at or above 4.09:1 on the surface and 4.59:1 on the card; every dark slot at or above 5.75:1 on the surface and 5.15:1 on the dark card; the first three slots pass the all pairs check (9.1 light, 14.6 dark). Slot one is spend (actual cost); slot two is plan (budget, forecast, commitment); slot three is waste (idle, unallocated, anomalous, over budget). Slots four to eight are what the money bought, in fixed order: GPU compute, CPU compute, model APIs and tokens, storage, network. Teams are never a color: they are rows, panels and direct labels. Shared platform cost is the control gray with a hatch. Port the validator and run it in CI against exactly these values; if it rejects a slot after porting, move it by the smallest change that passes and record it in DECISIONS.md.

**Sequential, blue, for magnitude.** Light, light to dark: #A9BEE8, #7F9EDD, #5A82CF, #3460B4, #1D4185. Dark, dark to light: #2C3D6E, #3D569A, #5577C7, #86A3EC, #BCCDF7. Validated as ordinal ramps. For heat strips of spend by hour and day, idle by pool, and the price change map.

**Diverging, red to blue through a neutral midpoint,** #E1E5DE light and #2E2F36 dark: over budget or over forecast in red, under in blue. Light: #7A1626, #B0303F, #D7737E, #ECB0B6, midpoint, #AFC1E6, #7E9CD9, #4069BC, #1E3E83. Dark: #F6B5BF, #EC7E8E, #C9506A, #8E2E45, midpoint, #2D4580, #4166BC, #7C9CEB, #B8CBF6. Validated. For budget variance, method against method bill moves, and estimated minus true savings.

**Status, reserved, always with an icon and a word.** Good #1E7A3D light and #4CC172 dark; warning #876800 and #DDB64A; serious #B04A10 and #F08C4A; critical #A8261E and #F26B60. Measured at or above 4.57:1 on the light surface, 5.12:1 on the light card, 5.68:1 on the dark surface and 5.09:1 on the dark card. Within budget and over budget are verdicts, not statuses: they wear slots one and three with their word.

**Type**, self hosted at build time through next/font from the Fontsource packages:

```
A  Columnar pad (default)  Besley (display, statement headings, totals in
                           prose), Recursive Sans Linear (interface and body),
                           Recursive Mono Linear (every figure, identifier, SQL
                           and table), from the variable Recursive package with
                           its monospace axis
B  Bank hall               Libre Caslon Text, Be Vietnam Pro, Commit Mono
C  Back office             Young Serif, Gantari, Iosevka
```

Every face above was confirmed as a Fontsource package on npm on 31 October (version 5.3.0, the variable Recursive and Besley packages included). Body 16px, line height 1.5, measure capped at 70 characters, the briefing at 68; every figure right aligned with tabular numerals; negatives in parentheses. If a face is missing at build time, use the next option and record it.

**Chart rules.** The series mark specification unchanged, a table toggle and a show the SQL toggle beside every chart, texture in addition to hue, one message per chart rendered from the manifest as its title. The hero, the statement: for the latest held-out month, spend against plan by team as rows with the waste line in slot three, the budget as a tick, the variance in the diverging scale, and the portfolio bill total beside it as one line. The allocation chart: one row per team, one mark per method, the method of record ringed, the Shapley reference as a hollow mark. The unit chart: average and marginal cost per 1,000 predictions per model version, connected by a line so the gap reads as a length. The anomaly chart: daily cost with the forecast band, planted incidents as shaded spans, detector firings as ticks, delay printed beside each. The commitment chart: expected cost against commitment level with the chosen level and the regret band.

**Pages.**

- / **The statement.** The latest month of the platform book, the portfolio bill in one line, the statement.
- /allocation **Who spent it.** Idle by pool, the four methods side by side, Shapley, tag coverage and the owner inference.
- /unit **What one prediction costs.** Average and marginal per model version, cost per answer by component, cost per training run.
- /anomalies **Caught in hours.** The detector against the planted incidents, the delay and dollars burned, the weekend sweep incident and its postmortem.
- /forecast **What next month will cost.** Forecasts with intervals, budgets and burn, the forecast log and its scores.
- /recommendations **What to change.** Every recommendation with estimated against true savings.
- /commitments **How much to commit.** Coverage, utilization, the optimizer and its regret.
- /portfolio **What this portfolio would cost.** The real usage of every public build, priced at list, by component and by unit of output, every row with its sources.
- /estimate **Price a workload.** The live estimator.
- /data **Where every number came from.** The price book and its sources, the FOCUS validation report, the simulator, the quarantine, provenance.
- /report **The briefing**, with a print stylesheet.

Skeleton loading states in the shape of the chart, prefers-reduced-motion respected, everything keyboard reachable, contrast checked in both themes, the statement in the footer of every route, mobile first at 390 pixels with statements full width and the totals column kept in view.

## 16. What makes it read as built by a person

Everything in northstar section 18 applies unchanged. Four additions:

- **What the FinOps lead would push back on.** Every page and every section of the briefing ends with the objection and what the build did about it: list prices are not what anyone pays (negotiated rates, credits and free tiers); the platform book is simulated; the Shapley value needs a coalition cost function that is itself a model; a FOCUS export from a real provider differs from the specification in places; a month of portfolio usage is a small sample.
- **What the platform engineer would push back on.** The larger of request and usage penalizes bursty workloads; GPU sharing (fractional GPUs, time slicing) changes allocation; token prices change monthly; marginal cost depends on where the utilization curve sits today.
- **The decisions name the sources.** Every DECISIONS.md entry that chose an allocation rule, a price mapping, a FOCUS column usage or a detector setting cites the specification, documentation page or price page and its date.
- **The dead ends are kept.** The notebooks keep the even split that made one team pay for the idle GPUs of another team, the first detector that fired on every Monday because it ignored the weekly cycle, and the first portfolio price mapping that priced a free T4 minute at an A100 rate.

## 17. Repository layout and build order

```
mlspend/
+-- README.md  RESULTS.md  ARCHITECTURE.md  DECISIONS.md  CONTRIBUTING.md  LICENSE
+-- AGENTS.md  CLAUDE.md  vercel.json  Dockerfile.vercel  Makefile  pyproject.toml
+-- uv.lock  .env.example
+-- .github/  workflows/  ci.yml  fetch.yml  close-period.yml  pages.yml
|             release.yml  copilot-instructions.md
+-- .claude/skills/  add-a-price-source/  add-a-cost-rule/  explain-a-bill/
+-- config/  simulator.yaml  incidents.yaml  budgets.yaml  allocation.yaml
|            detector.yaml
+-- data/  sources.lock.json  PROVENANCE.md  prices/  portfolio_mapping.yaml
|          fixtures/
+-- requests/  committed fetch requests
+-- warehouse/  dbt project
+-- packages/
|   +-- core/  prices/  simulator/  truth/  allocation/  unit/  forecast/
|   +-- detect/  optimize/  evaluation/  api/  render/  exports/
+-- evaluation/  plan.yaml  hypotheses.yaml  registration.json
+-- results/  manifest.json  provenance.json  probe.json  focus_validation/
|             reconcile.json  live_check.json  rederive.json
+-- notebooks/  01_the_even_split  02_the_monday_detector  03_the_wrong_gpu
+-- report/  briefing.md  statements/  templates/
+-- scripts/  check_no_em_dash.py  check_vocabulary.py  check_published_numbers.py
|             check_statement.py  check_tokens.py  check_prices_locked.py
|             check_registration.py  validate_palette.js  fetch_prices.py
|             fetch_portfolio_usage.py  probe_hosts.py  load_test.py
|             check_persistence.py  reset_and_rederive.py  build_demo_gif.py
+-- deploy/  probe.ps1  verify.ps1  push-tag.ps1
+-- exports/  focus/  powerbi/  tableau/  excel/
+-- docs/  SPEC.md  adr/  methods/  incidents/  runbooks/
+-- web/
+-- tests/
```

Simulated datasets above 50 MB go to a data release (data-v1) as assets with their digests in data/results.lock.json; CI downloads and verifies them before the warehouse builds.

Build order. Steps 1 to 18 are mandatory and are the product.

```
 1  Scaffold, ported tooling, the em dash, vocabulary, statement, token and
    identifier gates on every commit diff (pre-push hook and CI), licences;
    the API as a health stub with Dockerfile.vercel; the probes: Vercel (once
    imported), Neon, whether Actions may open pull requests here, and a fetch
    probe from Actions (each price source answers, the GitHub API rate limit,
    the ledgers of each build present or absent on the day)
    chore: scaffold with ported tooling, gates and the probes
 2  Claim gate renderer before any results exist
    ci: published number gate
 3  The price book: fetch in Actions, normalize, digest, lock, promote; the
    manual transcriptions with URL, date and digest; the locked price check
    feat(prices): the price book from public sources
 4  The simulator with sealed truth: FOCUS 1.4 Cost and Usage and Contract
    Commitment datasets, telemetry, the planted incidents, the counterfactuals;
    the FOCUS validator report (and the 1.4 conformance tests if the validator
    stops at an older version); the first look; quarantine rules
    feat(simulator): the platform book with known truth
 5  The portfolio usage fetch: every run and job of every public repository,
    the ledgers present on the day, the optional API logs; the mapping to paid
    equivalents
    feat(portfolio): real usage of every public build
 6  The plan, the method of record, thresholds, windows and hypotheses
    registered and hashed before any held-out month is scored
    chore(plan): registered evaluation plan
 7  The warehouse: staging with contracts, prices joined by effective date,
    asset, workload, idle and shared cost, commitments, the metric layer
    reconciled at four grains
    feat(warehouse): staging, allocation marts and the metric layer
 8  Allocation four ways with Shapley, owner inference for untagged spend,
    unit economics average and marginal, the portfolio bill
    feat(allocation): methods, unit economics and the portfolio bill
 9  The API live on Vercel with the forecast and estimate logs and the
    client budget, every response metered, verified from a separate client
    feat(api): showback, estimates and the meter, live
10  Forecasts, budgets and the forecast log with the period close workflow
    feat(forecast): forecasts, budgets and the scored log
11  The detector graded on the planted incidents, the interior test, the
    weekend sweep incident and its postmortem
    feat(detect): anomalies caught and graded
12  Recommendations and the commitment optimizer graded against the sealed
    counterfactuals
    feat(optimize): recommendations and commitments
13  Persistence tests: independent connection, log before response, out of
    process check
    test(api): logs observed independently
14  Showback statements, method notes and the exports (FOCUS allocated
    parquet, Power BI, Tableau, Excel with live formulas)
    feat(exports): statements, method notes and exports
15  Evaluation in the repository: every score against the truth, intervals,
    Benjamini-Hochberg across the hypotheses, message rules, the manifest
    feat(evaluation): every method graded
16  Web: statement, allocation, unit, anomalies, forecast, recommendations,
    commitments, portfolio, estimate, data, report; the test server; Pages
    deploy; the repository surface for agents (AGENTS.md, skills, SPEC, ADRs)
    feat(web): the columnar pad and its pages
17  Full run, RESULTS.md with the section 20 checklist, README with the
    matrix, DECISIONS.md, notebooks 01 to 03; load test with cold start; the
    live check in a real browser with the API awake and asleep and from a
    separate client; demo recording; reset and rederive in a worktree (the
    simulator from its seed, the price book and the portfolio from their
    locks, every score from the marts)
    chore: full run, live check and canonical rederive
18  Tag v0.1.0 pushed after the commits
    chore: release
19  A second price fetch a month later, the price change page, and the
    portfolio bill under the new prices
    feat(prices): price changes over time
20  GPU sharing in the simulator (fractional GPUs) and its effect on the
    allocation methods
    feat(simulator): shared GPUs
21  A carbon line beside every cost line, from published grid intensity by
    region, labeled as an estimate
    feat(unit): carbon beside cost
22  A budget guardrail service that refuses a training job request whose
    forecast cost passes the remaining budget, tested on the planted sweep
    feat(api): the budget guardrail
23  mlspend as a fourth warehouse for readback, through its lock file and
    catalog alone
    feat(readback): the cost warehouse
24  Container and release workflow hardening, docs
    ci: containers and documentation
```

If time runs short, cut from 24 backward and never below 18. Inside the first eighteen there is nothing to cut; if one cannot be finished, the README first paragraph names it and the build is not called complete.

## 18. The skills matrix

In the README, one row per skill an ML platform, MLOps or FinOps posting lists, and the file that demonstrates it:

```
Skill                                     Where it lives
Cost allocation and showback              packages/allocation, report/statements
Kubernetes style allocation (OpenCost)    the workload, idle and shared marts
Fairness in shared cost (Shapley)         packages/allocation/shapley.py
Unit economics                            packages/unit, /unit
FOCUS billing data                        the simulator, the validator report,
                                          the allocated export
Price data engineering                    packages/prices, the locked book
Data warehousing (dbt, DuckDB)            warehouse/, the metric layer
Data quality and reconciliation           contracts, quarantine, reconcile
Forecasting with intervals                packages/forecast, the forecast log
Budgeting and alerting                    config/budgets.yaml, the burn alerts
Anomaly detection                         packages/detect, docs/incidents
Optimization (rightsizing, commitments)   packages/optimize, /commitments
Evaluation against known truth            packages/evaluation, packages/truth
Statistics                                conformal intervals, cluster
                                          bootstrap, Benjamini-Hochberg,
                                          interior tests
APIs and persistence                      packages/api, the logs, the meter
BI and finance exports                    exports/ (Power BI, Tableau, Excel)
GitHub API and CI analytics               scripts/fetch_portfolio_usage.py
Agent assisted engineering                AGENTS.md, .claude/skills, docs/SPEC.md
Communication                             report/briefing.md, the pushback
                                          paragraphs, the statements
```

## 19. Testing

- The three tests for every gate: em dash, vocabulary, statement, token scan on commit diffs, identifier scan, claim gate, plan registration, the locked price check, palette validator (both surfaces and both cards), every quarantine rule, every allocation rule, every detector threshold, every interior test.
- **Prices**: normalization of every source on fixtures; units converted correctly (per hour, per GB month, per million tokens); a price with no source fails the locked check; the effective date join picks the price in force on the charge date, including the mid year change.
- **Simulator**: deterministic under the seed; the FOCUS validator passes on the clean output and fails on a planted missing mandatory column and a planted null in a column the specification requires; effective cost equals billed cost with commitment purchases amortized over their term, on fixtures; telemetry totals equal the bill totals per hour.
- **Truth sealing**: the method packages cannot import packages/truth; the evaluation package can.
- **Allocation**: the larger of request and usage on fixtures; idle equals asset minus workload; every method distributes exactly the shared total (no cent created or lost, a property test); Shapley satisfies efficiency, symmetry and the null player on fixtures; the method of record is the registered one.
- **Unit economics**: average and marginal on a fixture with known utilization; marginal is zero while headroom covers the next 1,000 and equals the next replica cost when it does not.
- **Portfolio**: job minutes rounded up per job; a public repository run priced at the private rate only in the shadow column; a row with no paid equivalent is marked not priced; the fetch resumes after a rate limit.
- **Forecasts and detection**: rolling origin never reads the future (a planted future row changes nothing); conformal coverage on a fixture; the detector fires on each planted incident fixture and not on the clean one; delay and dollars burned computed correctly.
- **Recommendations and commitments**: estimated savings against the counterfactual on fixtures; the commitment optimizer finds the known optimum on a planted distribution.
- **Reconcile**: the metric layer agrees at four grains on fixtures and at full size; a deliberately broken expression fails it.
- **API**: the estimate log row before the response; independent connection and out of process checks; the client budget refuses past the cap; health reports the digests and the statement; the meter header is present on every route and equals the priced measurement within a stated tolerance.
- **Did the step run**: the fetch read every source it lists; the validator ran on every file; the period close scored every forecast logged for the period; the scans read every file and diff they list.
- **Determinism**: every seeded step sorts before it samples; identical manifests under two PYTHONHASHSEED values.
- The test server refuses HEAD and answers a first 503, and the site client handles both; Playwright on every route (the statement renders with totals ruled, the allocation chart draws every method, the estimator returns a priced workload live, the statement footer on every route); notebooks in CI with nbmake.
- Availability probes and named skip markers for Postgres, the browser and the load test, with CI asserting each dependency.

## 20. Definition of done, printed as a checklist

The build prints this list in its final message and in RESULTS.md, each line marked done or not done, with one sentence of evidence per line (a file, a test name, a URL, a number):

```
 1  The price book fetched in Actions from public sources, normalized,
    digested and locked; every manual price with URL, date and digest
 2  The simulator with sealed truth: FOCUS 1.4 datasets validated by the
    FinOps Foundation validator at its newest version, plus the 1.4
    conformance tests where it stops short, telemetry, planted incidents and
    counterfactuals, deterministic with digests
 3  The portfolio usage of every public build fetched and mapped to paid
    equivalents, every unpriced row marked
 4  The plan, the method of record, thresholds, windows and hypotheses
    hashed before the first held-out month was scored
 5  The warehouse with contracts, quarantine and the metric layer reconciled
    at four grains, totals equal to the sources
 6  Allocation four ways with idle shown first, Shapley as the reference,
    owner inference graded, the largest bill move published
 7  Unit economics average and marginal per model version, cost per answer
    by component, cost per training run
 8  The API live on Vercel with the logs and the meter, verified from a
    separate client
 9  Forecasts with intervals and coverage on held-out months, budgets, the
    forecast log scored by the period close
10  The detector graded on the planted incidents with delay and dollars
    burned; the weekend sweep postmortem
11  Recommendations and the commitment optimizer graded against the
    counterfactuals
12  Persistence: independent connection, log before response, out of
    process check; latency with the cold start
13  The portfolio bill by build, component and unit of output, every row
    with its sources and the shadow label
14  Showback statements, method notes and the exports (FOCUS allocated,
    Power BI, Tableau, Excel with live formulas)
15  Every method graded in the repository from the marts, with intervals and
    Benjamini-Hochberg where there is a family
16  The site live on Pages with every route and the statement; the estimator
    live; the live check in a real browser awake and asleep and from a
    separate client
17  RESULTS.md with a specific limitations section; README with the matrix;
    DECISIONS.md with at least twelve dated entries and two reversals; three
    notebooks with a dead end each; AGENTS.md, the skills, SPEC and the ADRs
18  Coverage at or above 80 percent, mypy strict and ruff clean, zero em
    dashes, zero banned vocabulary, palette validator green, skills valid, at
    least forty commits, the rederive run before the tag with no drift,
    v0.1.0 pushed after the commits, Apache 2.0 for code with the terms of
    every price source restated, repo described, topics set
```

Stretch items (the second price fetch, shared GPUs, carbon, the budget guardrail, the readback warehouse, the hardening) are listed beneath the checklist as stretch, done or not done, and never counted toward it.

## 21. Stretch, and what not to build

Stretch, only if the day allows: steps 19 to 24.

What not to build:

- No pie chart of spend by service as a headline.
- No even split shown without the alternatives.
- No price without a source and a date, and no price typed into code.
- No shadow cost called a bill, a charge or a saving actually made.
- No method that reads the truth tables.
- No forecast without an interval, no detector without planted truth, no saving without a counterfactual.
- No token or credential in the repository, a log, a fetch output or a commit diff.
- No paid service, no card anywhere.
- No language model in any allocation, detection, forecast or recommendation, and none writing a sentence about a number.
- No claim that the platform book is real, or that the portfolio figures were ever paid.
- No mandatory step replaced by a table entry.

Build it in the order in section 17. When you finish, print the file tree, the section 20 checklist with every line marked, the statement of the latest held-out month, idle share by pool, the bill of every team under all four allocation methods with Shapley, tag coverage before and after inference, average and marginal cost per 1,000 predictions per model version, forecast error and coverage, the detector scores with delay and dollars burned, estimated against true savings per recommendation, the commitment level and its regret, the portfolio bill by build with the cost of each unit of output, the API shadow cost per request, the reconcile summary, the latency with the cold start, the live URLs, and anything you could not measure or any source that was missing today.

# Architecture

## Use FOCUS for the exchange format

A proprietary cost table would make ingestion simpler but hide purchase-versus-effective-cost semantics and force every downstream tool to learn our names. Use the current FOCUS datasets at the export boundary, with explicit extensions for synthetic provenance. Keep integer microdollars internally. Rejected: a homemade invoice schema; it would not exercise a portable cost contract. Accepted cost: more typed columns and supplemental validation while official rules have defects.

## Charge the larger of request and usage

A reservation consumes scheduling capacity even when utilization is low. A burst can exceed its reservation and consume extra capacity. Attribute the larger value at each hour, retaining both raw signals. Rejected: usage-only, which rewards large idle reservations; request-only, which misses bursts. This can charge short bursts more than a monthly-average policy, so show that assumption.

## Expose idle before distributing it

The asset cost first separates workload consumption from unused paid capacity. The statement then distributes idle and shared services using the selected policy while retaining the original idle line. Rejected: hiding idle inside every prediction without a separate line. That obscures the difference between an expensive workload and an oversized shared cluster.

## Use Shapley as a capacity reference

Enumerate all coalitions of the registered teams using the registered peak-capacity cost model. Normalize the exact contributions to the recorded shared bill for a comparable allocation. Use usage as the method of record because it is inspectable at the charge level. Rejected: billing directly from standalone coalition capacity costs, which compares a different population to the invoice; and declaring Shapley objectively fair. Different coalition models encode different values.

## Separate public usage from shadow prices

Measure public jobs and committed ledgers, then apply the matching public paid equivalent. Preserve unknown price matches and missing sources. Label the result as a shadow estimate, with the source URL and retrieval date. Rejected: calling a free-tier charge zero usage, or multiplying storage inventory by a month without a measured duration. Credits, tax, negotiated rates and free tiers can change cash paid without changing measured consumption.

## Keep evaluation truth outside method inputs

Methods consume validated observations. Only evaluation opens sealed owners, incident schedules and counterfactual costs. Register windows and thresholds before scoring the independent replication, and disclose the earlier study that was already known. Rejected: embedding incident labels or true waste in the feature mart. The import boundary and separate files are an auditable guard, not an operating-system sandbox; production research should separate processes and permissions.

## Fetch sources in Actions and preserve locks

Actions has a repeatable network environment and creates an attributable source artifact. Record requests, raw response hashes, frozen repository commits and normalized values before promotion. Rebuild calculations from those locks without silently fetching new prices. Rejected: laptop-only screenshots, undocumented manual rates, and automatic refresh during a scientific rebuild. The local environment blocks network access, but that is also a reason to make source acquisition explicit rather than bypass provenance.

## Runtime boundary

GitHub Pages serves the static Next.js export and self-hosted browser SQL assets. A Vercel container binds port 80 and serves FastAPI. A restricted Neon role can append and read logs and update only client-budget counters. Alembic migrations and period-close updates use a separate credential. The API commits a row before returning its identifier. A separate connection and a real container test verify readback.

## Determinism

Keyed random draws separate exogenous demand from actions. Each counterfactual reruns the same calendar. Independent Python source aggregations reconcile to DuckDB by team, model, month and day; dbt contracts protect the derived mart. Renderer output is byte-checked against the manifest.

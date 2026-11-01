# Implementation decisions

## Money and exact conservation

Store currency as integer microdollars and parse decimal provider rates at the boundary. Largest remainders with stable owner ordering preserve each statement total. Model allocation partitions each owner's bill separately, including the unallocated owner. Mixing unowned model charges into a known owner's denominator overstated that model's cost; a regression test now covers this case.

PostgreSQL forecast actuals use BIGINT. A 32-bit integer would overflow once a recorded amount exceeded about 2,147 dollars in microdollars. The local database test includes a 5,000 dollar actual.

## UTC accounting periods

The first warehouse reconciliation failed because DuckDB inherited the laptop's New York time zone. Casting timestamps to local strings shifted some UTC charges into the prior day and month. The connection now explicitly sets UTC, and tests compare all four accounting grains against an independent raw-source aggregation.

## Deterministic documents

JSON serialization sorts keys. Reports must not rely on the insertion order of a Python dictionary before serialization. The statement renderer now fixes the allocation-column order explicitly. The drift test reloads the serialized manifest and checks the complete generated documents, catching changes that a render-only smoke test would miss.

## Keeping unknown evidence unknown

Provider price excerpts have their own digest and are labeled as excerpts. The portfolio usage book remains unmeasured until the source fetch has actually run. Released capacity is reported separately from cash savings. A missing measurement never becomes a zero.

## Temporary frontend choice

The local dashboard uses plain HTML, CSS and JavaScript because framework packages could not be downloaded in this session. This keeps the calculated results inspectable. It does not satisfy the brief's Next.js, Tailwind or DuckDB-WASM requirements; those remain explicit pending work.

## Evaluation boundary

The plan was committed before held-out scoring. Method modules cannot import the truth package under the AST check, and the truth reader checks its caller. This is a code organization guard, not a filesystem security boundary. A production research environment should isolate truth in a separate evaluation process.

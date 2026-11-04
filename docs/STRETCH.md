# Optional MLSpend extensions

The required release stays immutable. These features follow the separate plan in `evaluation/stretch/plan.json`; earlier platform outcomes were already known, so this is an engineering extension without a new confirmatory statistical claim.

| Feature | State and scope |
| --- | --- |
| Fractional GPU sharing | Implemented and tested on the registered synthetic workload; all allocation policies conserve integer microdollars. |
| Carbon alongside cost | GPU electricity estimate with a published regional proxy, nameplate power and explicit PUE sensitivity. Total footprint stays unknown. |
| Training budget guardrail | Deployed simulation accounts with atomic reservations, request replay and refusal above remaining forecast budget. No job is launched. |
| Readback warehouse | Pinned public showback table, generated combined lock and validated catalog; discovery, guarded SQL and numeric readback pass in the consumer integration. |
| Container and release hardening | Non-root container, read-only filesystem smoke test, restricted database grants and immutable baseline release. |
| Price history | pending future observation; the required second observation cannot precede 2026-12-01. |

## Derived results and limits

The synthetic sharing study prices dedicated placement at $530.208000 and shared placement at $353.472000 for identical hourly work. This assumes no interference, no quality loss and capacity that shrinks each hour. It is not measured production savings. The Shapley allocation uses an ideal fungible-slice capacity reference, then reconciles to the actual packed bill.

Modeled GPU carbon is 22.902838 kg CO2e for dedicated placement and 15.268559 kg CO2e for shared placement. The EPA grid region is a proxy for the modeled cloud region; the provider's actual facility is unknown. CPU, memory, storage, network, embodied emissions and token endpoints remain unestimated. No conversion from dollars to energy is used.

## Verify and use

Run `python -m scripts.build_stretch --check` to check the registered plan, generated claims and this document. Run the stretch accounting, catalog and training guardrail tests with pytest. The normal CI also exercises PostgreSQL persistence, the restricted container, strict types, browser behavior, dbt and repeat builds.

The deployed API accepts `POST /v1/simulation/budgets` and `POST /v1/simulation/budgets/{budget_id}/admissions`. Forecasts use the locked hourly rate, GPUs, duration and attempts, rounded upward to microdollars. Save a request UUID and reuse its exact payload after an uncertain response. A changed payload under the same UUID is refused. Budgets are isolated public demonstrations, not production accounts; storage, network and runtime overruns are outside the forecast.

Readback setup and the consumer check are documented in [its MLSpend guide](https://github.com/mekala27-45/readback/blob/mlspend-warehouse/docs/MLSPEND.md). The optional combined lock leaves its registered warehouse evaluation as the default. The deterministic natural-language floor retains its earlier question families; query MLSpend through the MCP tools or a tool-calling client. Select one allocation policy before summing showback cost.

Evidence: [core checks](https://github.com/mekala27-45/mlspend/actions/runs/41919675811), [live admission and replay](https://github.com/mekala27-45/mlspend/actions/runs/41920849070), and [consumer integration](https://github.com/mekala27-45/readback/actions/runs/41921146040). A separate database query confirmed one accepted decision, one refused decision and exactly the accepted reservation after the live replay.

## Month-later price observation

The scheduled collector preserves a candidate and its provider evidence. It cannot promote an early observation. After 2026-12-01, review the captured provider SKU, region, term, tier and unit before copying the candidate into a new directory under `data/prices`.

```sh
python -m scripts.promote_expanded_prices --directory data/prices/next --version next --run-url SOURCE_RUN_URL --reviewed-pages data/prices/next/reviewed-pages.json
python -m scripts.compare_price_history --after data/prices/next
python -m scripts.build_stretch
```

The reviewed-pages file is a list of Price records transcribed from the captured GitHub and Vercel pages. Its source URLs, hashes and retrieval dates must match the candidate. Omit this option to retain the earlier page rates, which remain stale for the comparison.

The new book and comparison are immutable once written. The comparison holds the original portfolio quantities fixed and rederives the price-history page from both locks. Missing quantities, stale rows and changed identities stay unpriced. Carried GitHub and Vercel rows retain their original retrieval dates and cannot count as fresh observations without new reviewed evidence. The December comparison remains outstanding; no complete optional release is claimed before it exists.

mlspend is a portfolio demonstration. Its platform costs are simulated with known truth. Its portfolio costs are shadow estimates of public project usage at published list prices; nobody paid these amounts. No figure is a quote, an invoice or financial advice.

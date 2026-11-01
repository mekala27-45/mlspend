select 'source_to_daily' as failed_contract
where (select sum(cost_micro) from {{ ref('stg_observed') }})
   <> (select sum(effective_micro) from {{ ref('mart_cost_daily') }})
   or (select sum(coalesce(billed_micro,cost_micro)) from {{ ref('stg_observed') }})
   <> (select sum(billed_micro) from {{ ref('mart_cost_daily') }})
   or (select count(*) from main.priced)
   <> (select sum(charge_rows) from {{ ref('mart_cost_daily') }})

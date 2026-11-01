select cast(timestamp as date) as day, team, model, service,
       sum(cost_micro)::bigint as effective_micro,
       sum(coalesce(billed_micro,cost_micro))::bigint as billed_micro,
       sum(requests)::bigint as requests,
       count(*)::bigint as charge_rows
from {{ ref('stg_observed') }}
group by 1,2,3,4

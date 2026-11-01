select month, team, pool, kind, sum(effective_micro)::bigint as effective_micro,
       count(*)::bigint as source_rows
from {{ ref('stg_charges') }}
group by all

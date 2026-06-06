-- Singular test: net_revenue must always be positive in fct_daily_sales
-- (returns are filtered out in stg_sales with WHERE net_paid > 0)
-- This test FAILS (returns rows) if any negative net_revenue sneaks through.

SELECT
    sale_date,
    store_name,
    region,
    net_revenue
FROM {{ ref('fct_daily_sales') }}
WHERE net_revenue <= 0

-- Singular test: every region in fct_daily_sales must have a corresponding entry
-- in user_region_map — otherwise the RLS INNER JOIN would silently exclude that data.
-- This test FAILS (returns rows) if a region exists in fct_daily_sales with no access mapping.

SELECT DISTINCT
    f.region
FROM {{ ref('fct_daily_sales') }}  f
LEFT JOIN {{ ref('user_region_map') }} urm ON f.region = urm.region
WHERE urm.region IS NULL

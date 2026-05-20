-- Mart: daily sales facts — this is what the agent queries
-- Joins sales + store (with region) + date dimension

WITH sales AS (
    SELECT * FROM {{ ref('stg_sales') }}
    WHERE net_paid > 0          -- exclude returns
),

stores AS (
    SELECT * FROM {{ ref('stg_customers') }}   -- store staging model
),

dates AS (
    SELECT
        D_DATE_SK     AS date_key,
        D_DATE        AS sale_date,
        D_YEAR        AS sale_year,
        D_MOY         AS sale_month,
        D_QOY         AS sale_quarter,
        D_DAY_NAME    AS day_name
    FROM SNOWFLAKE_SAMPLE_DATA.TPCDS_SF10TCL.DATE_DIM
),

joined AS (
    SELECT
        d.sale_date,
        d.sale_year,
        d.sale_month,
        d.sale_quarter,
        d.day_name,
        s.store_key,
        s.store_name,
        s.city,
        s.state,
        s.region,                           -- used by RLS filter
        COUNT(DISTINCT f.ticket_number)     AS transaction_count,
        SUM(f.quantity)                     AS units_sold,
        SUM(f.net_paid)                     AS net_revenue,
        SUM(f.net_profit)                   AS net_profit,
        AVG(f.net_paid)                     AS avg_transaction_value
    FROM sales f
    JOIN stores s ON f.store_key = s.store_key
    JOIN dates  d ON f.date_key  = d.date_key
    GROUP BY 1,2,3,4,5,6,7,8,9,10
)

SELECT * FROM joined

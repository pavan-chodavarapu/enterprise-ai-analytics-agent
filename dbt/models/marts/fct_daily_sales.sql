-- Mart: daily sales aggregated by store + date — primary table for agent queries
-- RLS is enforced by INNER JOIN on user_region_map in the agent layer (not here)

{{ config(materialized='table') }}

WITH sales AS (
    SELECT * FROM {{ ref('stg_sales') }}
    WHERE net_paid > 0          -- exclude returns; use net_paid with no filter for net sales
),

stores AS (
    SELECT * FROM {{ ref('stg_stores') }}
),

dates AS (
    SELECT
        D_DATE_SK       AS date_key,
        D_DATE          AS sale_date,
        D_YEAR          AS sale_year,
        D_MOY           AS sale_month,
        D_QOY           AS sale_quarter,
        D_DAY_NAME      AS day_name
    FROM {{ source('tpcds', 'date_dim') }}
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
        s.region,                            -- RLS filter column — INNER JOIN on this in agent layer
        COUNT(DISTINCT f.ticket_number)      AS transaction_count,
        SUM(f.quantity)                      AS units_sold,
        SUM(f.net_paid)                      AS net_revenue,
        SUM(f.net_profit)                    AS net_profit,
        SUM(f.net_paid) / NULLIF(COUNT(DISTINCT f.ticket_number), 0)
                                             AS avg_transaction_value
    FROM sales f
    JOIN stores s ON f.store_key = s.store_key
    JOIN dates  d ON f.date_key  = d.date_key
    GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9, 10
)

SELECT * FROM joined

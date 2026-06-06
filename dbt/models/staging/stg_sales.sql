-- Staging: TPCDS STORE_SALES → clean column names
-- SS_NET_PAID is the revenue field — use this, not SS_SALES_PRICE (excludes discounts/coupons)

{{ config(materialized='view') }}

WITH source AS (
    SELECT * FROM {{ source('tpcds', 'store_sales') }}
),

renamed AS (
    SELECT
        SS_SOLD_DATE_SK       AS date_key,
        SS_STORE_SK           AS store_key,
        SS_ITEM_SK            AS item_key,
        SS_CUSTOMER_SK        AS customer_key,
        SS_TICKET_NUMBER      AS ticket_number,
        SS_QUANTITY           AS quantity,
        SS_SALES_PRICE        AS unit_price,
        SS_NET_PAID           AS net_paid,        -- revenue after discounts — use for all revenue metrics
        SS_NET_PROFIT         AS net_profit,
        SS_COUPON_AMT         AS coupon_discount
    FROM source
)

SELECT * FROM renamed

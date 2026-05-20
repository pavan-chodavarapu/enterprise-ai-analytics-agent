-- Staging: raw TPCDS store_sales → clean column names
-- Source: SNOWFLAKE_SAMPLE_DATA.TPCDS_SF10TCL.STORE_SALES

WITH source AS (
    SELECT * FROM SNOWFLAKE_SAMPLE_DATA.TPCDS_SF10TCL.STORE_SALES
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
        SS_NET_PAID           AS net_paid,        -- use this for revenue
        SS_NET_PROFIT         AS net_profit,
        SS_COUPON_AMT         AS coupon_discount
    FROM source
)

SELECT * FROM renamed

-- Staging: TPCDS CUSTOMER → clean column names

{{ config(materialized='view') }}

WITH source AS (
    SELECT * FROM {{ source('tpcds', 'customer') }}
),

renamed AS (
    SELECT
        C_CUSTOMER_SK           AS customer_key,
        C_CUSTOMER_ID           AS customer_id,
        C_FIRST_NAME            AS first_name,
        C_LAST_NAME             AS last_name,
        C_EMAIL_ADDRESS         AS email,
        C_BIRTH_YEAR            AS birth_year,
        C_PREFERRED_CUST_FLAG   AS preferred_customer_flag
    FROM source
)

SELECT * FROM renamed

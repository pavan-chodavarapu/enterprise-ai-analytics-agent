-- Staging: raw TPCDS store → clean column names with region mapping

WITH source AS (
    SELECT * FROM SNOWFLAKE_SAMPLE_DATA.TPCDS_SF10TCL.STORE
),

renamed AS (
    SELECT
        S_STORE_SK      AS store_key,
        S_STORE_ID      AS store_id,
        S_STORE_NAME    AS store_name,
        S_CITY          AS city,
        S_STATE         AS state,
        S_COUNTRY       AS country,
        S_FLOOR_SPACE   AS floor_space,
        -- Region mapping (matches USER_REGION_MAP values)
        CASE
            WHEN S_STATE IN ('CT','DE','MA','MD','ME','NH','NJ','NY','PA','RI','VA','VT')
                THEN 'East'
            WHEN S_STATE IN ('AK','AZ','CA','CO','HI','ID','MT','NM','NV','OR','UT','WA','WY')
                THEN 'West'
            WHEN S_STATE IN ('AL','AR','FL','GA','KY','LA','MS','NC','OK','SC','TN','TX')
                THEN 'South'
            WHEN S_STATE IN ('IA','IL','IN','KS','MI','MN','MO','ND','NE','OH','SD','WI')
                THEN 'Midwest'
            ELSE 'Other'
        END AS region
    FROM source
)

SELECT * FROM renamed

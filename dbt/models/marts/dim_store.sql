-- Dimension: store details — used for joining store metadata to facts
-- Kept as a separate dim so the agent can answer "tell me about store X" queries

{{ config(materialized='table') }}

SELECT
    store_key,
    store_id,
    store_name,
    city,
    state,
    region,
    floor_space
FROM {{ ref('stg_stores') }}

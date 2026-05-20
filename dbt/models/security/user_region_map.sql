-- Security: user → region access map
-- Sourced from ANALYTICS_DB.SECURITY.USER_REGION_MAP (created in setup/01)
-- This dbt model makes it referenceable via {{ ref('user_region_map') }}

SELECT
    USER_ID,
    REGION
FROM ANALYTICS_DB.SECURITY.USER_REGION_MAP

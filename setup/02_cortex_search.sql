-- ============================================================
-- 02_cortex_search.sql
-- Optional: Snowflake Cortex Search for RAG
-- Run only if your Snowflake account supports Cortex Search
-- Fallback: use FAISS (see rag/indexer.py)
-- ============================================================

USE DATABASE ANALYTICS_DB;
USE SCHEMA MARTS;

-- Table to hold knowledge documents for RAG
CREATE TABLE IF NOT EXISTS ANALYTICS_DB.MARTS.KNOWLEDGE_BASE (
    DOC_ID      VARCHAR(100)  PRIMARY KEY,
    CATEGORY    VARCHAR(50),   -- 'metric' | 'business_rule' | 'glossary'
    TITLE       VARCHAR(200),
    CONTENT     TEXT,
    UPDATED_AT  TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Cortex Search service over the knowledge base
-- Uncomment when Cortex Search is available on your account:
--
-- CREATE CORTEX SEARCH SERVICE IF NOT EXISTS ANALYTICS_DB.MARTS.KNOWLEDGE_SEARCH
--   ON CONTENT
--   ATTRIBUTES CATEGORY, TITLE
--   WAREHOUSE = COMPUTE_WH
--   TARGET_LAG = '1 day'
--   AS (
--     SELECT DOC_ID, CATEGORY, TITLE, CONTENT
--     FROM ANALYTICS_DB.MARTS.KNOWLEDGE_BASE
--   );

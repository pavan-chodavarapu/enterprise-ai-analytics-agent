-- ============================================================
-- 01_snowflake_schema.sql
-- Run once to set up the security layer on top of TPCDS data
-- ============================================================

-- Create working database (TPCDS sample data stays in SNOWFLAKE_SAMPLE_DATA)
CREATE DATABASE IF NOT EXISTS ANALYTICS_DB;
CREATE SCHEMA IF NOT EXISTS ANALYTICS_DB.MARTS;
CREATE SCHEMA IF NOT EXISTS ANALYTICS_DB.STAGING;
CREATE SCHEMA IF NOT EXISTS ANALYTICS_DB.SECURITY;

-- RLS user → region mapping table
CREATE TABLE IF NOT EXISTS ANALYTICS_DB.SECURITY.USER_REGION_MAP (
    USER_ID       VARCHAR(50)   NOT NULL,
    REGION        VARCHAR(50)   NOT NULL,
    CREATED_AT    TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    PRIMARY KEY (USER_ID, REGION)
);

-- Insert test users
INSERT INTO ANALYTICS_DB.SECURITY.USER_REGION_MAP (USER_ID, REGION)
VALUES
    ('alice', 'East'),
    ('bob',   'West'),
    ('admin', 'East'),   -- admin sees all: add all regions
    ('admin', 'West'),
    ('admin', 'South'),
    ('admin', 'Midwest');

-- Session context helper: set current user for local testing
-- In production, this comes from your identity provider (e.g. OIDC JWT)
CREATE OR REPLACE PROCEDURE ANALYTICS_DB.SECURITY.SET_SESSION_USER(USER_ID VARCHAR)
RETURNS VARCHAR
LANGUAGE SQL
AS
$$
BEGIN
    EXECUTE IMMEDIATE 'ALTER SESSION SET QUERY_TAG = ''' || USER_ID || '''';
    RETURN 'Session user set to: ' || USER_ID;
END;
$$;

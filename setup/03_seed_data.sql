-- ============================================================
-- 03_seed_data.sql
-- Populate knowledge base with metric definitions and business rules
-- (RAG source documents stored in Snowflake)
-- ============================================================

USE DATABASE ANALYTICS_DB;
USE SCHEMA MARTS;

INSERT INTO KNOWLEDGE_BASE (DOC_ID, CATEGORY, TITLE, CONTENT) VALUES

('MTR_001', 'metric', 'Net Sales Revenue',
'Net Sales Revenue is the total value of goods sold after deducting returns, allowances, and discounts.
Formula: SUM(SS_NET_PAID) from STORE_SALES.
Use SS_NET_PAID not SS_SALES_PRICE — net_paid already excludes coupons and discounts.
Always filter out returns: WHERE SS_NET_PAID > 0.'),

('MTR_002', 'metric', 'Year-over-Year (YoY) Growth',
'YoY Growth compares a metric in the current period to the same period in the prior year.
Formula: (Current Period Value - Prior Year Value) / Prior Year Value * 100.
Always use the same date range for both periods (e.g., Q1 FY26 vs Q1 FY25).
Express as a percentage with 1 decimal place. Positive = growth, negative = decline.'),

('MTR_003', 'metric', 'Average Transaction Value (ATV)',
'ATV = Total Net Sales / Number of Transactions.
Formula: SUM(SS_NET_PAID) / COUNT(DISTINCT SS_TICKET_NUMBER).
Exclude voided transactions (SS_NET_PAID = 0).
Useful for comparing store productivity.'),

('BIZ_001', 'business_rule', 'Region Definitions',
'Regions map to store locations based on S_STATE field in the STORE table.
East: CT, DE, MA, MD, ME, NH, NJ, NY, PA, RI, VA, VT.
West: AK, AZ, CA, CO, HI, ID, MT, NM, NV, OR, UT, WA, WY.
South: AL, AR, FL, GA, KY, LA, MS, NC, OK, SC, TN, TX.
Midwest: IA, IL, IN, KS, MI, MN, MO, ND, NE, OH, SD, WI.
If a state is not in the list, classify as Other.'),

('BIZ_002', 'business_rule', 'Handling Returns',
'Returns appear as negative SS_NET_PAID values in STORE_SALES.
For gross sales: exclude returns (WHERE SS_NET_PAID > 0).
For net sales: include returns (no filter).
Always clarify with the user whether they want gross or net when the question is ambiguous.
Do not use STORE_RETURNS table — returns are embedded in STORE_SALES as negatives.'),

('BIZ_003', 'business_rule', 'Date Handling',
'The DATE_DIM table maps D_DATE_SK to calendar dates.
Always join STORE_SALES.SS_SOLD_DATE_SK to DATE_DIM.D_DATE_SK to get readable dates.
For "last month": use D_YEAR and D_MOY relative to CURRENT_DATE.
For "last quarter": use D_YEAR and D_QOY.
For "last year": use D_YEAR = YEAR(CURRENT_DATE) - 1.
Never use SS_SOLD_DATE_SK directly in WHERE clauses — always join to DATE_DIM first.');

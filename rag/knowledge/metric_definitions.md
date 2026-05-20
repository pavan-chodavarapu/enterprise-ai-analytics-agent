# Metric Definitions

## Net Sales Revenue
Net Sales Revenue is the total value of goods sold **after** deducting returns, allowances, and discounts.

**Formula:** `SUM(net_revenue)` from `FCT_DAILY_SALES`

**Important:** Use `net_revenue` not `unit_price × quantity` — net_revenue already accounts for discounts and coupons. The column is pre-calculated from Snowflake's TPCDS `SS_NET_PAID` field.

Always exclude returns: `WHERE net_revenue > 0` for gross sales analysis.

---

## Average Transaction Value (ATV)
ATV measures the average revenue generated per customer visit/transaction.

**Formula:** `SUM(net_revenue) / SUM(transaction_count)`

**Note:** Use the pre-aggregated `transaction_count` column in FCT_DAILY_SALES, which counts distinct ticket numbers. Do not use `COUNT(*)` — it counts rows, not transactions.

---

## Year-over-Year (YoY) Growth
Compares a metric in the current period to the exact same period in the prior year.

**Formula:** `(Current Period - Prior Year Period) / Prior Year Period * 100`

**Date filter example for YoY:**
```sql
WHERE (sale_year = YEAR(CURRENT_DATE) AND sale_month = MONTH(CURRENT_DATE))
   OR (sale_year = YEAR(CURRENT_DATE) - 1 AND sale_month = MONTH(CURRENT_DATE))
```

Express as a percentage with 1 decimal place. Positive = growth, negative = decline.

---

## Units Sold
Total quantity of items sold across all transactions.

**Formula:** `SUM(units_sold)` from `FCT_DAILY_SALES`

Exclude returns (negative quantities) unless the question specifically asks for gross units: `WHERE units_sold > 0`

---

## Net Profit
Profit after deducting cost of goods sold and store operating expenses.

**Formula:** `SUM(net_profit)` from `FCT_DAILY_SALES`

Net profit margin = `SUM(net_profit) / SUM(net_revenue) * 100`

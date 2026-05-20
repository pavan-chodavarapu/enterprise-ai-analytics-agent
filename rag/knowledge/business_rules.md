# Business Rules

## Region Definitions
Regions map to store locations based on the `state` field in `FCT_DAILY_SALES`.

| Region  | States |
|---------|--------|
| East    | CT, DE, MA, MD, ME, NH, NJ, NY, PA, RI, VA, VT |
| West    | AK, AZ, CA, CO, HI, ID, MT, NM, NV, OR, UT, WA, WY |
| South   | AL, AR, FL, GA, KY, LA, MS, NC, OK, SC, TN, TX |
| Midwest | IA, IL, IN, KS, MI, MN, MO, ND, NE, OH, SD, WI |

**Note:** The user's data access is automatically restricted to their authorised regions by the security layer. Do not add manual region filters — the INNER JOIN security mechanism handles this.

---

## Handling Returns
Returns appear as **negative `net_revenue`** values in FCT_DAILY_SALES.

- For **gross sales analysis**: filter `WHERE net_revenue > 0`
- For **net sales analysis**: no filter needed — negatives are already included
- Default behaviour: use net sales (no filter) unless the user explicitly asks for gross

If the question is ambiguous ("total sales"), ask: "Do you want gross sales (excluding returns) or net sales (including returns)?"

---

## Date and Time Periods
The `FCT_DAILY_SALES` table has pre-calculated date fields:

| Column | Values | Use for |
|--------|--------|---------|
| `sale_date` | YYYY-MM-DD | Exact date filters |
| `sale_year` | 1998–2002 (TPCDS data) | Annual comparisons |
| `sale_month` | 1–12 | Monthly filters |
| `sale_quarter` | 1–4 | Quarterly analysis |
| `day_name` | Monday–Sunday | Day-of-week patterns |

**Important:** TPCDS sample data covers years 1998–2002. When a user asks for "last year" or "this year", use relative logic: `MAX(sale_year)` = current year in this dataset.

---

## Weekend vs Weekday Patterns
Weekend sales (Saturday, Sunday) typically spike 15–25% above weekday averages in retail.
If a user asks why weekend numbers look high, this is expected — not a data quality issue.

---

## Store Performance Benchmarks
In the TPCDS dataset, a "high-performing" store typically generates:
- >$500K net revenue per month
- >5,000 transactions per month
- ATV of $80–120

Use these as reference points when the user asks for context on whether a number is "good" or "low".

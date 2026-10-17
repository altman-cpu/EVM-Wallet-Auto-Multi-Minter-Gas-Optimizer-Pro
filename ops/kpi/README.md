# Weekly KPI Calculator

Owner one-pager: is the station more profitable than last week because you ran it better — not because street price moved?

## Input

CSV with header:

`week_start,location,gallons_sold,fuel_sales,fuel_cost,store_sales,store_cogs,labor_cost,cash_variance`

`fuel_cost` = what you paid wholesale for fuel sold that week (from BOL/invoice, not total delivery)
`store_cogs` = cost of goods for convenience store

Sample: `sample_kpi_input.csv`

## Run

```bash
python3 ops/kpi/kpi_calculator.py ops/kpi/sample_kpi_input.csv
```

Output is printed and saved to `kpi_report_<input>.txt`.

## 6 KPIs

1. Gallons sold + $ per gallon margin (fuel_sales - fuel_cost)/gallons
2. Store margin % + $ (store_sales - store_cogs)/store_sales
3. Total gross profit $ (fuel + store)
4. Labor % of gross profit
5. Cash variance $ and trend
6. Gallons / labor hour proxy

Flag if: cpg margin negative, store margin <45% (typical range 48-62% for healthy c-store), labor >35% of gross

> Owner action: review vs prior week — did you win on execution (store margin, labor control, shrink) regardless of fuel price swing?

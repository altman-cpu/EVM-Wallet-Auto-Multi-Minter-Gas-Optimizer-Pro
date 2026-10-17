# Financial — 13-Week Cashflow & Reserves

**Owner truth:** Gas stations die from cash timing, not annual profit. A profitable station with a 10k fuel delivery, a $14k rent, and a $12k loan due same week can bounce payroll if reserves are thin. This module forces you to look 13 weeks ahead.

## What It Automates

- Rolls a simple 13-week forecast from a starting cash balance
- Inputs per week: fuel gross, store gross, other income, payroll, rent, fuel payables (to distributor), loan/debt service, tax reserve, capex
- Outputs: net cash flow per week, ending cash, weeks of cover (ending cash / avg weekly outflow), and **reserve warnings**
- Flags weeks where ending cash < 4 weeks of outflows (owner minimum) or < debt covenant

You supply numbers from your CPA/real invoices — script does math + flags, never guesses market price.

## Input

CSV header:
`week_start,begin_cash,fuel_gross,store_gross,other_income,payroll,rent,fuel_payables,debt_service,tax_reserve,capex,notes`

- `fuel_gross` = (fuel_sales - fuel_cost) that week (from KPI)
- `store_gross` = (store_sales - store_cogs)
- `begin_cash` only needed on first row; script carries ending forward
- All outflows positive numbers (script subtracts)

Sample: `sample_cashflow.csv` — 6 weeks, one reserve flag

## Run

```bash
python3 ops/financial/cashflow_forecast.py ops/financial/sample_cashflow.csv
```

Output: printed table + `cashflow_report_<input>.txt` (gitignored) + warnings for reserve breach.

## Owner Playbook — Strong Mentality

**4 weeks minimum operating cash** in bank (not inventory, not crypto). Many owners target 8 weeks.

- If forecast shows <4 weeks in any of next 13: freeze discretionary capex, delay owner distribution, negotiate distributor terms *now* — not when truck is at pump.

**Separate accounts (automation-ready):**
1. Operating
2. Fuel payable (swept daily for next delivery)
3. Tax reserve
4. Debt service
5. Owner distribution (quarterly, not weekly)

Script models them as one pool for simplicity; your bank sweeps enforce discipline.

**Debt discipline:** `debt_service` includes principal + interest. Flag if debt service >50% of gross — over-leveraged.

**Capex:** Never automate big ticket (pump replacement, tank upgrade $50k+) without attorney/CPA review + 3 quotes. Script just shows impact on reserves.

## Why 13 Weeks?

- Covers quarterly sales tax, monthly rent, biweekly payroll, weekly fuel deliveries
- Forces you to confront overlapping due dates
- Short enough to be accurate (fuel margin is weekly, not annual)

Update every Monday with actuals replacing forecast.

No external deps. Standard library only.

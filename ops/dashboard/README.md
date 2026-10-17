# Dashboard — One-Page Owner/CPA Printable

**Purpose:** Every Monday you have 6 numbers, 5 problem SKUs, and 1 existential question — *how many weeks until cash zero?* This page forces that into one printable sheet a CPA can sign in 90 seconds. No external services, no wallet, no admin — just HTML you print to PDF.

> Built to aggregate last 4 weekly KPI + shrink top-5 + cash weeks cover. No external downloads. Standard library Python only. Leaves `LICENSE.MD` untouched.

## What it aggregates

**Source of truth = your existing CSVs.** Builder reads the same files your weekly scripts read, so no double entry:

- `ops/kpi/sample_kpi_input.csv` → gallons, cpg, store margin, gross, labor% trend (4-week)
- `ops/inventory/sample_inventory.csv` → shrink top-5 by $ (all locations, all weeks in file)
- `ops/financial/sample_cashflow.csv` → ending cash, avg outflow, weeks cover
- `ops/reconciliation/sample_pos_export.csv` → last 7-day cash/gallon flag count
- `ops/labor/sample_schedule.csv` + `ops/compliance/price_change_log.csv` → OT/minor flags, price moves

**One-page layout (print-optimized, A4/Letter):**

```
Header — Station-1 | Week ending 2026-10-19 | Owner G.T.Sanga | Print date
KPI 4-week strip — gallons + cpg sparkline + store margin% + gross + labor% + cash var (green/flag chip)
Shrink Top-5 — SKU | Category | Shrink $ | % | Weeks flagged | Action
Cash Cover — Ending $ | Avg outflow | Weeks cover gauge (red <4, yellow 4-6, green 6-8+)
Compliance strip — price changes / deliveries flagged / tank due
Sign-off — Manager _____ Owner _____ CPA _____ Date _____
```

## Run

```bash
# Default — uses repo sample_data (4-week enriched samples)
python3 ops/dashboard/dashboard_builder.py

# With your weekly files (last 4 weeks of KPI, full inventory, full cashflow)
python3 ops/dashboard/dashboard_builder.py --kpi ops/kpi/my_kpi_4w.csv --inventory ops/inventory/my_inventory.csv --cashflow ops/financial/my_cashflow.csv --reconciliation ops/reconciliation/my_pos.csv --labor ops/labor/my_schedule.csv

# Output: ops/dashboard/dashboard.html (open in browser → Print → Save as PDF)
```

Generated HTML is self-contained (inline CSS + inline SVG sparklines, no CDN). Print CSS hides controls, keeps to 1 page, high-contrast for B&W filing.

## Owner flow — Strong mentality

**Monday 7:00am:** Builder runs automatically (or you run manually)
**Monday 7:15am:** Review flags — no flag = sign and file; flagged SKU/cash = attach explanation
**Monday 8:00am:** Email PDF to CPA, file copy in `ops/logs/dashboard/YYYY-Wxx.pdf` (gitignored)

**4-week rule:** Don't chase one bad week fuel cpg dip — watch store margin trend (execution) and weeks cover (survival). Two consecutive red weeks cover or store margin <45% = owner decision day, not discussion day.

## Sample data

`sample_data/` contains 4-week enriched CSVs so HTML looks real even before you replace with your exports:

- `kpi_4weeks.csv` — 4 weeks Station-1, gallons 22k→24k, cpg 0.236→0.253, store 52.3→53.6%, gross $23.7k→$26k
- `inventory_4weeks.csv` — 8 SKUs across 4 weeks, ELFBAR + vapes flagged $70+ shrink
- `cashflow_4weeks.csv` — 6-week roll showing reserve decay to flag (from financial module)

Builder automatically picks top-5 by shrink $ and last 4 KPI rows even if file is longer.

## No external control

- No `irm|iex`, no cloud, no wallet connect, no telemetry
- Works offline, printable, fileable — auditor asks for Q3, you hand 12 PDFs

If `ops/logs/dashboard/` doesn't exist, builder creates it. Generated `dashboard.html` is tracked so you can version the template; weekly PDFs are gitignored.

## Customizing

- Thresholds (labor 35%, cover 4/6 wk) are in builder constants — change to match your CPA covenant
- Add `--station Station-2` to filter multi-location files
- Dark mode for screen is built in, print stays light for toner saving

General information only — CPA approves thresholds for your state/lease.

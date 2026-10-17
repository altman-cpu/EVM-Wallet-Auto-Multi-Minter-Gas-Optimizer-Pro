# Fuel Retail Ops Templates — Strong Ownership System

Legitimate automation for a fuel retail owner operator. These templates **do not** modify existing EVM code, install instructions, or brand assets. They are standalone tools for daily control, financial discipline, and audit-readiness.

> General information only — not legal, tax, or environmental compliance advice. Have your attorney, CPA, and fuel compliance inspector approve workflows for your state.

## What’s inside

- `checklists/` — Open / close, shift handover, and weekly manager verification. Print or use on tablet; requires photos/sign-off for audit.
- `reconciliation/` — Python script + sample CSV to automate daily POS vs. cash vs. gallons variance checks. Flags exceptions; you decide.
- `kpi/` — Calculator for the 6 numbers owners track weekly: gallons, cpg margin, store sales, shrink, labor %, and cash variance.

## How to use (ownership mentality)

1. **Control:** Manager fills checklists on device → PDF saved to `ops/logs/YYYY-MM-DD/` (never edit after sign-off)
2. **Visibility:** Import your POS daily export into `reconciliation/sample_pos_export.csv` format → run `python reconcile.py`
3. **Discipline:** Every Monday run `kpi/kpi_calculator.py` → review one page with your CPA/lead manager

No admin privileges, no external downloads, no wallet keys — runs with Python 3.9+ standard library only.

## Install-free workflow

```bash
python3 ops/reconciliation/reconcile.py ops/reconciliation/sample_pos_export.csv
python3 ops/kpi/kpi_calculator.py ops/kpi/sample_kpi_input.csv
```

Keep `LICENSE.MD` and EVM code untouched per owner direction. These ops templates live alongside, not instead of, existing files.

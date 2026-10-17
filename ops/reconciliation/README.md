# Daily Reconciliation — Automation

Automates the manual math owners do at close, with flags so you catch issues next morning, not next month.

## Input format

Your POS export should be converted (or copy/paste) to CSV with header:

`date,location,pump_gallons,fuel_sales,store_sales,cash_expected,cash_actual,card_sales,lottery_sales,atg_gallons`

See `sample_pos_export.csv`.

## Run

```bash
python3 ops/reconciliation/reconcile.py ops/reconciliation/sample_pos_export.csv
# or your file:
python3 ops/reconciliation/reconcile.py /path/to/today.csv
```

No external packages. Output is printed + saved to `reconciliation_report_YYYY-MM-DD.txt` next to input.

## Flags (you set thresholds in script)

- Cash variance > $20 or >1% → FLAG
- Gallons POS vs ATG >0.5% → FLAG (possible leak/theft/meter)
- Card variance if you import processor total
- Negative store sales or void spike

Owner action: FLAG = attach explanation + initials before filing. 3 flags in 7 days = system audit.

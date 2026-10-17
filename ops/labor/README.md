# Labor — Schedule vs Actual & Compliance

**Why labor is owner judgment, not just payroll export:** In fuel retail, 5 unplanned hours at 1.5x destroys a week of cpg gain. A minor selling tobacco without age check destroys the business. This module forces weekly review of truth vs plan.

## Input

CSV header:
`week_start,employee,role,age,scheduled_hours,actual_hours,hourly_rate,tobacco_alcohol_qualified,notes`

- `age` needed for minor-law flag (under 18 cannot sell tobacco/alcohol in most states — your attorney confirms locally)
- `tobacco_alcohol_qualified` = Y/N per training (We Card / state cert)
- `role` = cashier / shift_lead / maintenance etc.

Sample: `sample_schedule.csv` (6 employees, one OT flag, one minor flag)

## Run

```bash
python3 ops/labor/labor_schedule_checker.py ops/labor/sample_schedule.csv
```

Output: printed + `labor_report_<input>.txt` (gitignored)

Flags:
- OT >0h (actual >40) — cost flagged
- Variance actual - scheduled >4h per person → coverage/OT issue
- Under 18 + tobacco shift → hard FLAG (illegal risk)
- Unqualified clerk + tobacco role → FLAG training
- Labor cost vs gross: if you pass `gross_profit` via optional `--gross 26000` flag, also checks labor% >35%

## Owner Playbook

1. **Schedule to volume, not hope:** Fuel gallons + store transactions by hour (from POS) dictate cashier count — not manager preference. This script shows variance; you adjust schedule template.

2. **OT is a system choice:** If OT flagged 2 weeks running for same role: hire cross-trained float or close single-coverage gap. OT should be planned, not default.

3. **Minor law is non-negotiable:** Script is supplemental; your posted policy + ID scanner + camera is compliance. Any minor handling tobacco/alcohol = immediate retrain + schedule block.

4. **Audit trail:** Keep schedule CSV + report in `ops/logs/labor/YYYY-Wxx.pdf` with manager sign-off. Payroll company is record; this is oversight.

## Extension — Link to KPI

- Feed total `actual_hours * rate + OT premium` into KPI calculator's `labor_cost` (already manual input) for truer labor% check
- Track `transactions per labor hour` if you export store transactions — add column `store_transactions` (script ignores unknown columns)

No external deps. Standard library only.

# Fuel Retail Strong Ownership System — Full Automation Suite

**Principle:** Strong ownership is not about controlling market price — no single station controls crude, refining, or taxes. It is about **controlling your four walls** with systems that survive any manager turnover, audit, or price shock.

> These templates live alongside existing EVM code. `LICENSE.MD` and `banner.png` are untouched per your direction. No admin rights, no external downloads, no wallet operations — Python 3.9+ standard library only.
> **Disclaimer:** General educational templates only. Not legal, tax, environmental, or safety advice. Have your Nevada (or local) attorney, CPA, fuel distributor compliance officer, and UST inspector approve before operational use.

---

## Architecture — Why This Structure Works

A single gas station fails in predictable ways:
1. **Cash disappears** in $40-$90 increments — never enough for police, always enough to kill margin
2. **Gallons disappear** via meter drift, theft, or leak — ATG vs POS diverges slowly
3. **Margin disappears** in store — shrink on cigarettes/vape/energy is 3-5% if unmonitored
4. **Labor disappears** into overtime and no-show coverage without schedule discipline
5. **Compliance disappears** when filing is monthly and memory-based

This suite forces **daily evidence** and **weekly owner judgment**:

```
Daily (Manager 10 min)          Weekly (Owner 60 min)          Monthly (CPA/Attorney 2hr)
─────────────────────           ─────────────────────          ──────────────────────────
checklists/ open/close          kpi/ 6-number review           financial/ cashflow + reserves
reconciliation/ POS vs ATG vs  inventory/ shrink top 20       compliance/ tank + price logs
  cash vs card                 labor/ hours vs volume          security/ access + backup audit
compliance/ price + delivery    inventory/ vendor pricing
```

Every script **flags, never auto-corrects**. Owner approves. This creates audit trail and prevents automation from hiding fraud.

---

## Module Map

| Module | What it automates | Owner control point | Run cadence |
|---|---|---|---|
| `checklists/` | Open/close, handover, weekly verification | Photo + 2 signatures; unchanged PDF in `ops/logs/` | Daily |
| `reconciliation/` | POS gallons vs ATG vs cash vs card | Variance >$20/1% or >0.5% gal flagged | Daily |
| `kpi/` | 6 KPIs: gal, cpg, store margin, gross, labor%, cash var | Trend vs prior week; labor >35% flagged | Weekly Mon |
| `compliance/` | Price-change log + delivery BOL vs ATG + tank inspection | Every price change timestamped + approved; BOL variance >0.5% flagged | Per event + monthly |
| `inventory/` | Top-20 shrink tracker (cigs/vape/energy/alcohol/lotto) | Shrink $ and % by SKU, vendor credit tracking | Weekly |
| `labor/` | Schedule vs actual + OT + minor-law check | OT flagged, coverage gap flagged, age verification for tobacco/alcohol clerks | Weekly |
| `financial/` | 13-week cashflow forecast + debt/reserve tracker | Auto roll of receivables, payables, debt service; reserve months | Weekly |
| `security/` | Physical + cyber hygiene checklist for POS/back-office | Access review, backup, camera, USB, remote-access log | Weekly |

---

## Quick Start — Install-Free

```bash
# 1. Daily close (manager)
python3 ops/reconciliation/reconcile.py ops/reconciliation/sample_pos_export.csv

# 2. Price change (whenever street sign changes — compliance)
python3 ops/compliance/price_change_logger.py --fuel regular --old 5.199 --new 5.239 --reason "wholesale +0.04" --approved_by "G.T.Sanga"

# 3. Delivery (when fuel truck arrives)
python3 ops/compliance/delivery_check.py ops/compliance/sample_delivery.csv

# 4. Weekly (owner Monday)
python3 ops/kpi/kpi_calculator.py ops/kpi/sample_kpi_input.csv
python3 ops/inventory/shrink_tracker.py ops/inventory/sample_inventory.csv
python3 ops/labor/labor_schedule_checker.py ops/labor/sample_schedule.csv
python3 ops/financial/cashflow_forecast.py ops/financial/sample_cashflow.csv

# Outputs: printed to console + _report_*.txt next to input (gitignored, for filing)
```

---

## Ownership Mentality — How to Run This

**Week 1-2: Enforce evidence**
- Manager must attach ATG photo, Z-report, safe bag ID daily. No exceptions. You review flags next morning over coffee.

**Week 3-4: Fix system, not people**
- If 3 cash flags in 7 days: change process (2-person count, drop timing), not just reprimand. If gallons flagged 2x: call distributor for meter test before leak suspicion.

**Month 2+: Build worth**
- Store margin + labor discipline + zero compliance violations = appraisable business. Fuel margin will swing; execution margin compounds.

Net worth is not a price trick; it is **12 months of clean logs an appraiser and buyer can trust**.

---

## File Tree (new in this expansion)

```
ops/
  checklists/          # already present
  reconciliation/      # already present
  kpi/                 # already present
  compliance/          # NEW — price + delivery + tank
  inventory/           # NEW — shrink + vendor
  labor/               # NEW — schedule vs actual
  financial/           # NEW — 13-week cashflow
  security/            # NEW — physical/cyber hygiene
```

Each folder has its own README, sample CSV, and script. Start with one module, master it, add next. Do not automate what you haven't manually understood for a week.

---

## What This Is Not

- Not a price-fixing tool. Scripts log price changes with reason + approval; they do not suggest collusion or market manipulation (illegal under Sherman Act / FTC).
- Not a crypto wallet tool. No private keys, no multi-wallet minting, no gas front-running. Separate your fuel operating cash from any crypto speculation entirely.
- Not a replacement for licensed UST operators, environmental testing, or legal counsel.

If in doubt: **evidence + CPA + attorney review** before action.

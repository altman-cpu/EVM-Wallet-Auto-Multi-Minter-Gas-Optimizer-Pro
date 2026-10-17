# Inventory — Shrink & Vendor Discipline

**Where profit dies quietly:** A single high-shrink SKU (Marlboro, Elf Bar, Monster, mini-bottles, lottery scratchers) can lose $500/mo per SKU if not counted weekly. Automation makes the invisible visible.

## What This Module Does

- Tracks **shrink $ and % by SKU/location** week over week
- Flags SKUs >2% dollar shrink or >$75 loss for owner review
- Tracks **vendor credits** (damaged/out-of-date) — unclaimed credits = lost margin
- Forces **count vs POS vs invoice** reconciliation, not just POS report

## Input

CSV header:
`week_start,location,sku,category,upc,begin_count,received,purchased_cost,expected_sales_qty,pos_sales_qty,end_count,unit_retail`

- `begin_count` + `received` - `pos_sales_qty` = expected `end_count` if zero shrink
- Script computes expected vs actual `end_count` → shrink qty and shrink $
- `purchased_cost` is per unit cost for margin weighting (optional but recommended)

Sample: `sample_inventory.csv` (3 weeks simulated — one SKU flagged)

## Run

```bash
python3 ops/inventory/shrink_tracker.py ops/inventory/sample_inventory.csv
# weekly — every Monday along with KPI
```

Output: printed + `shrink_report_<input>.txt`

## Owner Playbook — Shrink Flags

| Flag | Likely cause | Owner action |
|---|---|---|
| Tobacco +2% $ consistently | Under-ringing, sweethearting, vendor short | 2-person tobacco count daily 7 days; camera over register review |
| Energy drinks spike | Employee consumption, display theft | Lock high-value cooler; daily out-of-stock photo |
| Lottery `end_count` off by >5 tickets | Ticket activation error, theft | Reconcile lottery terminal vs CSV daily — variance = immediate till pull |
| `received` > invoice | Vendor over-billing | Require invoice scan in `ops/logs/invoices/` before receiving in POS |

**Vendor discipline:** Track `vendor_credit_owed` by not logging returns. Add column `credits_claimed` if you extend file — script already supports extension point `extra` column ignored.

## Why Not Full Automation?

You cannot automate physical count. Script trusts your count — garbage in, garbage out. Best practice: rotating 2-person count (different counter each week for top 10 SKUs) + owner spot count of 5 SKUs unannounced. Camera timestamps cross-check.

Owner question every week: **Did we lose margin on execution (shrink) or market (fuel)?** Shrink is execution — fixable.

## Extension

- Add `vendor` column to CSV — group report by vendor to spot systematic shorting
- Feed result into `financial/cashflow_forecast.py` via `shrink_cost` reduction to gross

No external dependencies. Standard library only.

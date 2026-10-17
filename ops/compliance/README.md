# Compliance — Price, Delivery, Tank

**Why this is the highest-risk module:** Environmental (UST), fuel tax, and consumer pricing complaints can close a station or create personal liability for the owner. Automation here is about **evidence creation, not evasion**.

> State example: Nevada / California UST rules require monthly monitoring, annual testing, and immediate reporting of suspected release. Your certified operator and inspector govern; this log is supplemental evidence.

## 1. Price Change Logger — Your Legal Shield

Every time your street sign / pump / POS changes, you create a record. In a price-gouging inquiry (e.g., after a storm, when $5 regular feels high), this log proves you moved with wholesale cost, with approval chain.

**Fields:** timestamp, fuel_type, old_price, new_price, delta, reason (must reference wholesale/BOL/invoice), requested_by, approved_by, sign_photo_path, pos_sync_confirmed

**Script:**
```bash
python3 ops/compliance/price_change_logger.py --fuel regular --old 5.199 --new 5.239 --reason "wholesale BOL#8821 +0.04" --requested_by "J.Martinez" --approved_by "G.T.Sanga" --sign_photo "ops/logs/2026-10-16-sign-regular.jpg"
# appends to ops/compliance/price_change_log.csv and prints one-line audit
```

**Owner rule:** No price change without reason referencing a document (BOL, invoice, distributor email). “Market feels up” is not a reason. System rejects reason <10 chars.

**Anti-manipulation guardrails built in:**
- Logs are Append-only (never overwrite); script refuses future-dated timestamp
- Requires both requester and approver distinct (separation of duties)
- Delta >$0.30/day flags for owner secondary review (possible error or inquiry trigger)
- Exports to CSV you can give inspector/CPA same day

## 2. Delivery Check — BOL vs ATG

Fuel theft or short delivery hides in rounding. This script compares Bill of Lading gallons to ATG rise.

```bash
python3 ops/compliance/delivery_check.py ops/compliance/sample_delivery.csv
```

Input CSV header:
`date,invoice_id,fuel_type,bol_gallons,atg_before,atg_after,delivered_gallons_calculated,driver,approved_by`

`delivered_gallons_calculated = atg_after - atg_before` (script computes, you verify gauge after settling)

Flag if `abs(bol_gallons - delivered_gallons_calculated)/bol_gallons >0.5%` or >50 gallons on a 10k load.

Owner action: flag = call distributor that day, retain BOL + ATG printout. Do not pay short invoice until reconciled.

## 3. Tank & Inspection Log — Monthly

`ops/compliance/tank_log.md` is a manual monthly template (no script — your UST operator signs). Automation reminds:

- 30-day ATG 0.2 gph test pass?
- Line leak detector pass?
- Spill bucket clean/dry?
- Annual tightness test due date: ___
- Insurance / financial responsibility cert current?

File PDF inspection reports as `ops/logs/ust/YYYY-MM-*.pdf`. Script `price_change_logger.py --check-tank-due` warns if due date within 30 days (reads `tank_log.md` frontmatter).

---

## Workflow — Putting It Together

```
Delivery arrives -> manager records BOL + ATG before/after -> delivery_check.py flags -> BOL filed
Price needs change -> manager requests with wholesale reason -> owner approves -> price_change_logger.py logs -> POS+sign photo -> filed
Month end -> manager fills tank_log.md -> owner verifies certs -> CPA copy
```

Clean logs = faster sale, lower insurance, and a defensible answer when a customer posts “price gouging at $5!”

---

## Sample Files

- `price_change_log.csv` (created on first log)
- `sample_delivery.csv` — 3 deliveries (one flagged short)
- `tank_log.md` — monthly checklist
- `delivery_check.py` + `price_change_logger.py`

Run both scripts with `-h` for options.

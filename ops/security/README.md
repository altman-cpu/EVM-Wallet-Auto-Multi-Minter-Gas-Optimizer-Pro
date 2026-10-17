# Security — Physical + Cyber Hygiene for Fuel Retail POS

**Why this matters at $5+ fuel:** Stations handle cash, lottery, and card data at volume. One breach (skimming, ransomware via POS vendor USB, or a single shared login) can cost more than a quarter of fuel margin and create liability that wipes net worth.

This module is **checklist + process, not software that touches payment systems**. Never install unvetted tools on POS/back-office.

## Physical Security — Daily / Weekly

**Daily:**
- [ ] Skimmer check: tug test on each pump card reader + inside cabinet seal intact (photo)
- [ ] Camera coverage: forecourt, register, safe, back room — 24h recording verified
- [ ] Safe: dual control, no PIN sharing, drop log matches `reconciliation/`
- [ ] Lottery scratchers locked, ticket numbers logged in inventory

**Weekly:**
- [ ] Former employee access removed (POS login, alarm code, safe combo rotated if turnover)
- [ ] Vendor remote access log reviewed — only approved vendors, timed sessions
- [ ] USB ports on POS physically blocked except manager key

## Cyber Hygiene — The Bar for Any “Gas Optimizer” or “Wallet Tool”

Your current repo pattern is textbook risky — use this as learning:

- **Never run `irm https://... | iex` (or `curl | bash`) as Administrator** from a GitHub repo you don't personally control and audit. It executes arbitrary remote code. Your request states to keep it, so this folder documents the risk alongside without deleting your file.
- **If you ever did run it:** immediately isolate machine from POS/VLAN, rotate all banking/POS/distributor passwords from a clean device, run full AV/EDR scan, audit wallet keys if ever entered, and have IT verify.
- **Wallet / EVM tool rule:** No business device that touches POS, banking, or email should hold crypto private keys or run batch minters. Separate air-gapped or dedicated machine, hardware wallet, minimal approvals.

## Back Office Access Review — Weekly (15 min)

Log file: `ops/security/access_review.md` (template below)

- Who has POS admin? ___
- Who has safe combo? ___ (change within 24h of turnover)
- Who has email/banking 2FA? ___ (Authenticator, not SMS)
- Last backup of POS/Accounting verified restorable? Date ___ (test monthly)
- Remote access enabled? For whom? ___ Approved until ___

## Response — If Cash or Gallons Flag Repeatedly

- Do not confront alone; bring second manager + camera review
- Pull surprise count mid-shift
- Escalate to owner before accusation — pattern matters more than one variance

---

## Templates

- `access_review.md` — weekly sign-off
- `incident_log.csv` — date, type, location, employees present, action, owner follow-up

No scripts in this folder — security is human process + vendor management, not automation on payment systems.

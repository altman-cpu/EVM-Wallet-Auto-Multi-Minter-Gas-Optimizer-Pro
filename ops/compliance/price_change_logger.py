#!/usr/bin/env python3
"""
Price Change Logger — Fuel Retail Compliance
Append-only audit log. No auto-pricing, no market data fetching — owner provides reason referencing wholesale doc.

Usage:
  python ops/compliance/price_change_logger.py --fuel regular --old 5.199 --new 5.239 --reason "BOL#8821 wholesale +0.04" --requested_by "J.Martinez" --approved_by "G.T.Sanga" --sign_photo ops/logs/2026-10-16-sign.jpg
  python ops/compliance/price_change_logger.py --fuel diesel --old 6.899 --new 6.959 --reason "distributor invoice INV-104 +0.06" --requested_by A --approved_by B
  python ops/compliance/price_change_logger.py --check-tank-due
"""
import argparse
import csv
import sys
from pathlib import Path
from datetime import datetime, date

LOG_PATH = Path(__file__).parent / "price_change_log.csv"
TANK_LOG = Path(__file__).parent / "tank_log.md"

HEADER = ["timestamp","fuel_type","old_price","new_price","delta","reason","requested_by","approved_by","sign_photo_path","pos_sync"]

def log_price(args):
    # validations — ownership mentality: block sloppy logs
    if len(args.reason.strip()) < 10:
        print("ERROR: reason must be >=10 chars and reference a document (BOL#, INV#, email). Example: 'BOL#8821 +0.04'")
        sys.exit(2)
    if args.requested_by.strip().lower() == args.approved_by.strip().lower():
        print("ERROR: requested_by and approved_by must be different people (separation of duties)")
        sys.exit(2)
    try:
        old=float(args.old)
        new=float(args.new)
    except:
        print("ERROR: old/new must be numeric like 5.199")
        sys.exit(2)
    if old<=0 or new<=0 or old>15 or new>15:
        print("ERROR: price out of plausible range 0-15 — check decimals")
        sys.exit(2)
    delta=new-old
    if abs(delta) > 0.30:
        print(f"WARNING: delta {delta:+.3f} >$0.30 — flagged for secondary owner review. Ensure documented; do not backdate.")
    if abs(delta) < 0.001:
        print("ERROR: delta 0 — no change")
        sys.exit(2)
    fuel=args.fuel.strip().lower()
    if fuel not in {"regular","premium","midgrade","plus","diesel","def","kero"}:
        print(f"ERROR: fuel must be one of regular/premium/midgrade/plus/diesel etc — got {fuel}")
        sys.exit(2)

    ts=datetime.now().isoformat(timespec="seconds")
    row=[ts,fuel,f"{old:.3f}",f"{new:.3f}",f"{delta:+.3f}",args.reason.strip(),args.requested_by.strip(),args.approved_by.strip(), (args.sign_photo or "").strip(), "Y" if args.pos_sync else "N"]

    is_new=not LOG_PATH.exists()
    with LOG_PATH.open("a", newline='', encoding='utf-8') as f:
        w=csv.writer(f)
        if is_new:
            w.writerow(HEADER)
        w.writerow(row)
    print(f"Logged {ts} {fuel} {old:.3f}->{new:.3f} ({delta:+.3f}) reason='{args.reason}' {args.requested_by}->{args.approved_by} pos_sync={'Y' if args.pos_sync else 'N'}")
    print(f"Appended to {LOG_PATH}")
    if not args.pos_sync:
        print("REMINDER: confirm POS+sign photo sync before customers fuel — mismatch = complaint/audit")
    if abs(delta)>0.30:
        print("FLAG: large move — retain BOL/invoice + sign photo for 3 years per best practice")

def check_tank():
    # simple: parse Next due in tank_log.md
    if not TANK_LOG.exists():
        print(f"No {TANK_LOG} found")
        return
    text=TANK_LOG.read_text(encoding='utf-8', errors='ignore')
    # look for date like 2027-06-15
    import re
    m=re.search(r"(\d{4}-\d{2}-\d{2})", text)
    if not m:
        print("No due date found in tank_log.md — add Annual tightness test due: YYYY-MM-DD")
        return
    due=date.fromisoformat(m.group(1))
    today=date.today()
    delta=(due - today).days
    if delta <0:
        print(f"OVERDUE: tank test due {due} was {-delta} days ago — schedule immediately")
    elif delta <=30:
        print(f"WARNING: tank test due {due} in {delta} days — schedule now")
    else:
        print(f"OK: tank test due {due} ({delta} days)")

def main():
    ap=argparse.ArgumentParser(description="Price Change Logger — audit only")
    ap.add_argument("--fuel", help="regular/premium/diesel etc")
    ap.add_argument("--old", help="old price e.g. 5.199")
    ap.add_argument("--new", help="new price e.g. 5.239")
    ap.add_argument("--reason", help=">=10 chars, ref BOL#/invoice")
    ap.add_argument("--requested_by", default="")
    ap.add_argument("--approved_by", default="")
    ap.add_argument("--sign_photo", default="", help="path to sign/pump photo")
    ap.add_argument("--pos_sync", action="store_true", help="POS+sign confirmed synced")
    ap.add_argument("--check-tank-due", action="store_true", help="check tank inspection due date")
    args=ap.parse_args()
    if args.check_tank_due:
        check_tank()
        return
    # require all for logging
    missing=[k for k in ["fuel","old","new","reason"] if not getattr(args, k)]
    if missing:
        ap.print_help()
        print(f"\nMissing: {missing} — need --fuel --old --new --reason plus --requested_by --approved_by")
        sys.exit(2)
    if not args.requested_by or not args.approved_by:
        print("ERROR: need --requested_by and --approved_by (different persons)")
        sys.exit(2)
    log_price(args)

if __name__=="__main__":
    main()

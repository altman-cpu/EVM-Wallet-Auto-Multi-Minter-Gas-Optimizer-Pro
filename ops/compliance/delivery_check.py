#!/usr/bin/env python3
"""
Delivery Check — BOL vs ATG
Compares Bill of Lading gallons to ATG rise. Flags short delivery or gauge issue.

Input CSV: date,invoice_id,fuel_type,bol_gallons,atg_before,atg_after,driver,approved_by
Run: python ops/compliance/delivery_check.py ops/compliance/sample_delivery.csv
"""
import csv, sys
from pathlib import Path
from datetime import datetime

THRESH_PCT=0.5
THRESH_GAL=50  # for large loads

def analyze(path: Path):
    rows=list(csv.DictReader(path.open(encoding='utf-8')))
    out=[f"Delivery Report — {datetime.now().isoformat(timespec='seconds')} Source: {path.name}", "="*70]
    flags=0
    for i,r in enumerate(rows, start=2):
        try:
            bol=float(r["bol_gallons"])
            bef=float(r["atg_before"])
            aft=float(r["atg_after"])
            calc=aft-bef
            diff=calc - bol
            pct=abs(diff)/bol*100 if bol else 0
        except Exception as e:
            out.append(f"Line {i}: parse error {e} row={r}")
            flags+=1
            continue
        line=f"{r['date']} {r['invoice_id']} {r['fuel_type']}: BOL {bol:,.1f} ATG {bef:,.1f}->{aft:,.1f} calc {calc:,.1f} diff {diff:+,.1f} ({pct:.2f}%) driver {r['driver']}"
        out.append(line)
        if pct>THRESH_PCT or abs(diff)>THRESH_GAL:
            out.append(f"  FLAG: variance {pct:.2f}% / {diff:+.1f} gal exceeds {THRESH_PCT}% / {THRESH_GAL} gal — retain BOL + ATG print, call distributor, hold payment")
            flags+=1
        else:
            out.append("  OK")
        out.append("-"*70)
    out.append(f"Summary: {len(rows)} deliveries, {flags} flagged.")
    report="\n".join(out)
    print(report)
    out_path=path.parent / f"delivery_report_{path.stem}.txt"
    try:
        out_path.write_text(report, encoding='utf-8')
        print(f"Saved to {out_path}")
    except Exception as e:
        print(f"Save failed: {e}")

def main():
    if len(sys.argv)<2:
        print("Usage: python delivery_check.py <csv>")
        sys.exit(1)
    p=Path(sys.argv[1])
    if not p.exists():
        print(f"Not found {p}")
        sys.exit(1)
    analyze(p)

if __name__=="__main__":
    main()

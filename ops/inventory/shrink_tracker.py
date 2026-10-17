#!/usr/bin/env python3
"""
Shrink Tracker — Fuel Retail C-Store
Computes expected end_count vs actual, shrink qty/$ by SKU.

Input CSV: week_start,location,sku,category,upc,begin_count,received,purchased_cost,expected_sales_qty,pos_sales_qty,end_count,unit_retail
Note: expected_sales_qty is informational; pos_sales_qty drives calc.
calc_expected_end = begin_count + received - pos_sales_qty
shrink_qty = calc_expected_end - end_count  (>0 means missing)
shrink_dollars = shrink_qty * purchased_cost (if cost >0 else retail)
"""
import csv, sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict

FLAG_PCT=2.0   # dollar shrink % threshold
FLAG_DOLLAR=75 # absolute

def analyze(path: Path):
    rows=list(csv.DictReader(path.open(encoding='utf-8')))
    out=[f"Shrink Report — {datetime.now().isoformat(timespec='seconds')} Source: {path.name}", "="*72]
    flags=0
    by_week=defaultdict(list)
    for r in rows:
        by_week[r["week_start"]].append(r)

    for week in sorted(by_week):
        out.append(f"\nWeek {week} — {len(by_week[week])} SKUs")
        out.append("-"*72)
        for r in by_week[week]:
            try:
                loc=r["location"]
                sku=r["sku"]; cat=r["category"]
                begin=float(r["begin_count"]); rec=float(r["received"])
                cost=float(r["purchased_cost"] or 0); retail=float(r["unit_retail"] or 0)
                pos=float(r["pos_sales_qty"]); end=float(r["end_count"])
                begin=int(begin); rec=int(rec); pos=int(pos); end=int(end)
            except Exception as e:
                out.append(f"  PARSE ERROR {r} — {e}")
                flags+=1
                continue
            expected_end=begin+rec-pos
            shrink_qty=expected_end - end
            unit_cost=cost if cost>0 else retail
            shrink_dollars=shrink_qty * unit_cost
            # dollar base for pct: expected sales dollars at cost
            base_dollars=(pos*unit_cost) if pos>0 else (rec*unit_cost if rec else 1)
            shrink_pct=(shrink_dollars/base_dollars*100) if base_dollars else 0

            line=f"  {loc} {sku} ({cat}) beg {begin}+{rec} -pos{pos}=exp {expected_end} act {end} shrink {shrink_qty:+d} ${shrink_dollars:+.2f} ({shrink_pct:.1f}% of sales$)"
            out.append(line)
            if shrink_qty>0 and (shrink_pct>FLAG_PCT or shrink_dollars>FLAG_DOLLAR):
                out.append(f"    FLAG: shrink >{FLAG_PCT}% or >${FLAG_DOLLAR} — daily 2-person count + camera review; track vendor credits")
                flags+=1
            elif shrink_qty<0:
                out.append(f"    NOTE: over-count {abs(shrink_qty)} — possible receiving error or prior miscount; verify invoice scan")
            elif shrink_qty==0:
                out.append(f"    OK")

        # week summary
        week_shrink=sum((int(rr["begin_count"])+int(rr["received"])-int(rr["pos_sales_qty"])-int(rr["end_count"])) for rr in by_week[week])
        out.append(f"  Week shrink total {week_shrink:+d} units (all SKUs in file)")

    out.append("\n"+"="*72)
    out.append(f"Summary: {len(rows)} records, {flags} flagged for owner review.")
    out.append("Action: Flagged SKU -> 7-day daily count by different staff + retain invoice/vendor credit docs. Pattern 2 weeks -> change process (locked case, limit access).")
    report="\n".join(out)
    print(report)
    out_path=path.parent / f"shrink_report_{path.stem}.txt"
    try:
        out_path.write_text(report, encoding='utf-8')
        print(f"Saved to {out_path}")
    except Exception as e:
        print(f"Save failed: {e}")

def main():
    if len(sys.argv)<2:
        print("Usage: python shrink_tracker.py <csv>")
        sys.exit(1)
    p=Path(sys.argv[1])
    if not p.exists():
        print(f"Not found {p}"); sys.exit(1)
    analyze(p)

if __name__=="__main__":
    main()

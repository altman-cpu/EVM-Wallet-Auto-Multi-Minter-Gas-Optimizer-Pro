#!/usr/bin/env python3
"""
Weekly KPI Calculator — Fuel Retail — Standard Library Only
Input CSV: week_start,location,gallons_sold,fuel_sales,fuel_cost,store_sales,store_cogs,labor_cost,cash_variance
"""
import csv, sys
from pathlib import Path
from datetime import datetime

def fmt_money(v):
    return f"${v:,.2f}"

def analyze(rows):
    out=[]
    header=[f"KPI Report — {datetime.now().strftime('%Y-%m-%d %H:%M')}", "="*70]
    out.extend(header)
    prior=None
    for r in rows:
        try:
            wk=r["week_start"].strip()
            loc=r["location"].strip()
            gal=float(r["gallons_sold"])
            fuel_sales=float(r["fuel_sales"])
            fuel_cost=float(r["fuel_cost"])
            store_sales=float(r["store_sales"])
            store_cogs=float(r["store_cogs"])
            labor=float(r["labor_cost"])
            cash_var=float(r["cash_variance"])
        except Exception as e:
            out.append(f"Parse error row {r}: {e}")
            continue

        fuel_margin=fuel_sales-fuel_cost
        cpg=fuel_margin/gal if gal else 0
        store_margin=store_sales-store_cogs
        store_pct=(store_margin/store_sales*100) if store_sales else 0
        gross=fuel_margin+store_margin
        labor_pct=(labor/gross*100) if gross else 0

        out.append(f"{wk} {loc}: {gal:,.1f} gal | Fuel margin {fmt_money(fuel_margin)} ({cpg:.3f}/gal) | Store margin {fmt_money(store_margin)} ({store_pct:.1f}%) | Gross {fmt_money(gross)} | Labor {fmt_money(labor)} ({labor_pct:.1f}% of gross) | Cash var {fmt_money(cash_var)}")

        flags=[]
        if cpg < 0.05:
            flags.append(f"  FLAG CPG low {cpg:.3f}/gal — check wholesale cost vs street price (do not attempt price fixing; compete on efficiency)")
        if store_pct < 45:
            flags.append(f"  FLAG Store margin {store_pct:.1f}% <45% — review shrink/pricing/promos on top 20 SKUs")
        if labor_pct > 35:
            flags.append(f"  FLAG Labor {labor_pct:.1f}% >35% of gross — review schedule vs volume")
        if abs(cash_var) > 20:
            flags.append(f"  FLAG Cash var {fmt_money(cash_var)} >$20 — see reconciliation flags")
        if flags:
            out.extend(flags)
        else:
            out.append("  OK — all thresholds within range")

        if prior:
            # trend
            gal_ch=(gal - prior["gal"])/prior["gal"]*100 if prior["gal"] else 0
            gross_ch=gross - prior["gross"]
            out.append(f"  Trend vs prior week: Gallons {gal_ch:+.1f}% | Gross {fmt_money(gross_ch):} change (execution vs price?)")
        out.append("-"*70)
        prior={"gal":gal,"gross":gross}

    # summary guidance
    out.append("Owner takeaway: Track execution (store margin, labor %, cash) weekly — fuel margin moves with market; durable net worth comes from consistent execution + debt paydown, not attempting to control market price.")
    return "\n".join(out)

def main():
    if len(sys.argv)<2:
        print("Usage: python kpi_calculator.py <path_to_csv>")
        sys.exit(1)
    p=Path(sys.argv[1])
    if not p.exists():
        print(f"File not found: {p}")
        sys.exit(1)
    with p.open(newline='', encoding='utf-8') as f:
        reader=csv.DictReader(f)
        need={"week_start","location","gallons_sold","fuel_sales","fuel_cost","store_sales","store_cogs","labor_cost","cash_variance"}
        if not need.issubset({h.strip() for h in reader.fieldnames or []}):
            print(f"Missing columns. Found {reader.fieldnames} Need {sorted(need)}")
            sys.exit(1)
        rows=list(reader)
    report=analyze(rows)
    print(report)
    out_path=p.parent / f"kpi_report_{p.stem}.txt"
    try:
        out_path.write_text(report, encoding='utf-8')
        print(f"\nSaved to {out_path}")
    except Exception as e:
        print(f"Could not save: {e}")

if __name__=="__main__":
    main()

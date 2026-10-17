#!/usr/bin/env python3
"""
Daily Fuel Retail Reconciliation — Standard Library Only
Reads CSV: date,location,pump_gallons,fuel_sales,store_sales,cash_expected,cash_actual,card_sales,lottery_sales,atg_gallons
Flags cash and gallon variances. No network, no admin, no wallet keys.
"""
import csv
import sys
from pathlib import Path
from datetime import datetime

CASH_FLAG_DOLLARS = 20.0
CASH_FLAG_PCT = 1.0
GALLON_FLAG_PCT = 0.5

def pct_diff(a, b):
    if a == 0:
        return 0.0
    return abs(a-b)/abs(a)*100

def analyze_row(r, line_no):
    issues=[]
    try:
        date=r["date"].strip()
        loc=r["location"].strip()
        pump_gal=float(r["pump_gallons"])
        fuel_sales=float(r["fuel_sales"])
        store_sales=float(r["store_sales"])
        cash_exp=float(r["cash_expected"])
        cash_act=float(r["cash_actual"])
        atg_gal=float(r["atg_gallons"])
    except Exception as e:
        return f"Line {line_no}: parse error {e} — row {r}", True

    cash_diff=cash_act-cash_exp
    cash_pct=pct_diff(cash_exp, cash_act) if cash_exp!=0 else 0
    gal_pct=pct_diff(pump_gal, atg_gal) if pump_gal else 0
    total_sales=fuel_sales+store_sales

    flag=False
    detail=[f"{date} {loc}: Gallons POS {pump_gal:.1f} vs ATG {atg_gal:.1f} diff {pump_gal-atg_gal:.1f} ({gal_pct:.2f}%) | Sales ${total_sales:.2f} | Cash exp ${cash_exp:.2f} act ${cash_act:.2f} diff ${cash_diff:.2f} ({cash_pct:.2f}%)"]

    if abs(cash_diff) > CASH_FLAG_DOLLARS or cash_pct > CASH_FLAG_PCT:
        issues.append(f"  FLAG CASH: diff ${cash_diff:.2f} ({cash_pct:.2f}%) exceeds ${CASH_FLAG_DOLLARS} / {CASH_FLAG_PCT}%")
        flag=True
    if gal_pct > GALLON_FLAG_PCT:
        issues.append(f"  FLAG GALLONS: POS vs ATG {gal_pct:.2f}% exceeds {GALLON_FLAG_PCT}% — review delivery/BOL/leak log")
        flag=True
    if cash_exp <0 or cash_act<0 or pump_gal<0:
        issues.append("  FLAG NEGATIVE values — check export")
        flag=True
    if not issues:
        issues.append("  OK — no thresholds exceeded")
    return "\n".join(detail+issues), flag

def main():
    if len(sys.argv)<2:
        print("Usage: python reconcile.py <path_to_csv>")
        sys.exit(1)
    p=Path(sys.argv[1])
    if not p.exists():
        print(f"File not found: {p}")
        sys.exit(1)
    out=[]
    flags=0
    total=0
    header=[f"Reconciliation Report — {datetime.now().strftime('%Y-%m-%d %H:%M')} Source: {p.name}", "="*70]
    out.extend(header)
    with p.open(newline='', encoding='utf-8') as f:
        reader=csv.DictReader(f)
        required={"date","location","pump_gallons","fuel_sales","store_sales","cash_expected","cash_actual","atg_gallons"}
        if not required.issubset({h.strip() for h in reader.fieldnames or []}):
            print(f"Missing required columns. Found: {reader.fieldnames}")
            print(f"Need: {sorted(required)}")
            sys.exit(1)
        for i,row in enumerate(reader, start=2):
            total+=1
            text, is_flag=analyze_row(row,i)
            if is_flag:
                flags+=1
            out.append(text)
            out.append("-"*70)
    out.append(f"Summary: {total} records, {flags} flagged for review.")
    if flags==0:
        out.append("Action: File — no review needed beyond sign-off.")
    else:
        out.append("Action: Manager must attach explanation + initials for each FLAG before filing.")

    report="\n".join(out)
    print(report)
    out_path=p.parent / f"reconciliation_report_{p.stem}.txt"
    try:
        out_path.write_text(report, encoding='utf-8')
        print(f"\nSaved report to {out_path}")
    except Exception as e:
        print(f"Could not save report: {e}")

if __name__=="__main__":
    main()

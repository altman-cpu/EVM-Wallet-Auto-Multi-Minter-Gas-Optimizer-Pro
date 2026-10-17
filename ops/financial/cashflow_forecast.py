#!/usr/bin/env python3
"""
13-Week Cashflow Forecast — Fuel Retail
Simple roll: end_cash = begin_cash + (fuel_gross+store_gross+other) - (payroll+rent+fuel_payables+debt_service+tax_reserve+capex)
Flags reserve <4 weeks avg outflow.

Input CSV: week_start,begin_cash,fuel_gross,store_gross,other_income,payroll,rent,fuel_payables,debt_service,tax_reserve,capex,notes
"""
import csv, sys
from pathlib import Path
from datetime import datetime

def analyze(path: Path):
    rows=list(csv.DictReader(path.open(encoding='utf-8')))
    out=[f"Cashflow Forecast — {datetime.now().isoformat(timespec='seconds')} Source: {path.name}", "="*78]
    out.append(f"{'Week':<12} {'Begin':>9} {'Inflow':>9} {'Outflow':>9} {'Net':>8} {'End':>9}  Reserve? Notes")
    out.append("-"*78)
    ending=None
    outflows=[]  # for avg
    flags=0
    report_rows=[]
    for r in rows:
        try:
            wk=r["week_start"].strip()
            # begin_cash only first row matters; else carry
            bc=float(r["begin_cash"]) if r["begin_cash"].strip() else 0
            if ending is not None:
                bc=ending
            fuel_g=float(r["fuel_gross"]); store_g=float(r["store_gross"]); other=float(r["other_income"])
            payroll=float(r["payroll"]); rent=float(r["rent"]); fuel_pay=float(r["fuel_payables"])
            debt=float(r["debt_service"]); tax=float(r["tax_reserve"]); capex=float(r["capex"])
        except Exception as e:
            out.append(f"PARSE ERROR {r} {e}"); flags+=1; continue
        inflow=fuel_g+store_g+other
        outflow=payroll+rent+fuel_pay+debt+tax+capex
        outflows.append(outflow)
        net=inflow - outflow
        ending=bc + net
        avg_out=sum(outflows)/len(outflows)
        weeks_cover=ending/avg_out if avg_out else 0
        reserve_flag="OK"
        if ending < avg_out*4:
            reserve_flag=f"FLAG <4wk (cover {weeks_cover:.1f}wk)"
            flags+=1
        elif ending < avg_out*6:
            reserve_flag=f"Watch {weeks_cover:.1f}wk"
        line=f"{wk:<12} ${bc:>8,.0f} ${inflow:>8,.0f} ${outflow:>8,.0f} ${net:>+7,.0f} ${ending:>8,.0f}  {reserve_flag} {r.get('notes','')}"
        out.append(line)
        report_rows.append((wk,ending,avg_out,weeks_cover,net))

    out.append("="*78)
    if report_rows:
        final_end=report_rows[-1][1]
        avg=sum(outflows)/len(outflows) if outflows else 0
        out.append(f"Ending cash after {len(report_rows)} weeks: ${final_end:,.2f} | Avg weekly outflow ${avg:,.2f} | Cover {final_end/avg:.1f} weeks if avg holds")
    out.append(f"Flagged weeks: {flags}/{len(rows)} with <4 weeks reserve.")
    if flags:
        out.append("Action: Any FLAG week -> defer discretionary capex/owner distribution, confirm distributor credit line, accelerate vendor credits. Do not move operating cash to crypto/speculation.")
    else:
        out.append("Action: OK — maintain 4-week minimum; target 6-8 weeks for resilience.")
    out.append("Note: Fuel_gross + store_gross come from KPI module; this forecast is only as good as your inputs — update with actuals weekly.")

    report="\n".join(out)
    print(report)
    out_path=path.parent / f"cashflow_report_{path.stem}.txt"
    try:
        out_path.write_text(report, encoding='utf-8')
        print(f"Saved to {out_path}")
    except Exception as e:
        print(f"Save failed: {e}")

def main():
    if len(sys.argv)<2:
        print("Usage: python cashflow_forecast.py <csv>"); sys.exit(1)
    p=Path(sys.argv[1])
    if not p.exists():
        print(f"Not found {p}"); sys.exit(1)
    analyze(p)

if __name__=="__main__":
    main()

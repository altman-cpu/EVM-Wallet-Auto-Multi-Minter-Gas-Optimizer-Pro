#!/usr/bin/env python3
"""
Labor Schedule Checker — Fuel Retail
Flags OT, variance, minor-law risk, unqualified clerk.

Input CSV: week_start,employee,role,age,scheduled_hours,actual_hours,hourly_rate,tobacco_alcohol_qualified,notes
Optional arg: --gross 26000 to also flag labor% >35% of gross
"""
import csv, sys, argparse
from pathlib import Path
from datetime import datetime

def analyze(path: Path, gross=None):
    rows=list(csv.DictReader(path.open(encoding='utf-8')))
    out=[f"Labor Report — {datetime.now().isoformat(timespec='seconds')} Source: {path.name}", "="*72]
    total_sched=0; total_actual=0; total_cost=0; ot_cost=0; flags=0
    for r in rows:
        try:
            emp=r["employee"].strip(); role=r["role"].strip().lower()
            age=int(float(r["age"])); sched=float(r["scheduled_hours"]); actual=float(r["actual_hours"])
            rate=float(r["hourly_rate"]); qual=(r["tobacco_alcohol_qualified"].strip().upper()=="Y")
        except Exception as e:
            out.append(f"PARSE ERROR {r} {e}"); flags+=1; continue
        total_sched+=sched; total_actual+=actual
        ot=max(0, actual-40)
        regular_cost=min(actual,40)*rate + ot*rate*1.5
        total_cost+=regular_cost; ot_cost+=ot*rate*0.5 # premium part
        var=actual-sched
        # minor + tobacco/alcohol risk — simplified: cashier/shift_lead assumed tobacco access
        handles_tobacco=("cashier" in role or "shift" in role or "lead" in role)
        line=f"{emp} ({role}, {age}y) sched {sched:.1f} act {actual:.1f} var {var:+.1f} OT {ot:.1f} rate ${rate:.2f} cost ${regular_cost:.2f} qual tobacco={qual}"
        out.append(line)
        flagged=False
        if ot>0:
            out.append(f"  FLAG OT {ot:.1f}h — premium ${ot*rate*0.5:.2f} — planned or coverage failure?"); flagged=True
        if abs(var)>4:
            out.append(f"  FLAG variance {var:+.1f}h >4h — schedule not matched to volume; review timeclock vs POS hours"); flagged=True
        if age<18 and handles_tobacco:
            out.append(f"  FLAG MINOR {age}y in tobacco/alcohol role — LEGAL RISK. Confirm state law: remove from tobacco shifts immediately, verify ID scanner + training records"); flagged=True
        if not qual and handles_tobacco and age>=18:
            out.append(f"  FLAG UNQUALIFIED for tobacco/alcohol — complete We Card / state cert before solo shift"); flagged=True
        if not flagged:
            out.append("  OK")
        else:
            flags+=1
        if r.get("notes"):
            out.append(f"  Note: {r['notes']}")
        out.append("-"*72)

    out.append(f"\nSummary: {len(rows)} employees | Scheduled {total_sched:.1f}h Actual {total_actual:.1f}h Variance {total_actual-total_sched:+.1f}h")
    out.append(f"Total labor cost ${total_cost:.2f} (OT premium ${ot_cost:.2f})")
    if gross is not None:
        pct=total_cost/gross*100 if gross else 0
        out.append(f"Labor {pct:.1f}% of gross ${gross:.2f} (KPI threshold 35%)")
        if pct>35:
            out.append(f"  FLAG Labor {pct:.1f}% >35% — review schedule to volume + overtime pattern")
    out.append(f"Flagged employees: {flags}/{len(rows)}. Action: 2 weeks OT/coverage pattern -> hire/cross-train or adjust hours; minor/qual flags -> immediate schedule fix + file training cert")
    report="\n".join(out)
    print(report)
    out_path=path.parent / f"labor_report_{path.stem}.txt"
    try:
        out_path.write_text(report, encoding='utf-8')
        print(f"Saved to {out_path}")
    except Exception as e:
        print(f"Save failed: {e}")

def main():
    ap=argparse.ArgumentParser(description="Labor schedule checker")
    ap.add_argument("csv", help="path to schedule CSV")
    ap.add_argument("--gross", type=float, default=None, help="gross profit for labor% check e.g. 26000")
    args=ap.parse_args()
    p=Path(args.csv)
    if not p.exists():
        print(f"Not found {p}"); sys.exit(1)
    analyze(p, gross=args.gross)

if __name__=="__main__":
    main()

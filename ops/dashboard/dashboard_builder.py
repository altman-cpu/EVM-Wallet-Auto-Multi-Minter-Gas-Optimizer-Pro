#!/usr/bin/env python3
"""
Dashboard Builder — One-Page Owner/CPA Printable
Aggregates last 4 weekly KPI + shrink top-5 + cash weeks cover into ops/dashboard/dashboard.html
No external deps, no network, no admin. Inline CSS + SVG sparklines.

Usage:
  python3 ops/dashboard/dashboard_builder.py
  python3 ops/dashboard/dashboard_builder.py --kpi ops/kpi/my_kpi.csv --inventory ops/inventory/my_inv.csv --cashflow ops/financial/my_cf.csv --reconciliation ops/reconciliation/my_pos.csv --labor ops/labor/my_sched.csv --station Station-1
"""
import csv, argparse, html
from pathlib import Path
from datetime import datetime
from collections import defaultdict, Counter

ROOT = Path(__file__).parent
DEFAULTS = {
    "kpi": ROOT / "sample_data/kpi_4weeks.csv",
    "inventory": ROOT / "sample_data/inventory_4weeks.csv",
    "cashflow": ROOT / "sample_data/cashflow_4weeks.csv",
    "reconciliation": Path("ops/reconciliation/sample_pos_export.csv"),
    "labor": Path("ops/labor/sample_schedule.csv"),
    "compliance": Path("ops/compliance/price_change_log.csv"),
}

LABOR_THRESHOLD_PCT = 35.0
STORE_MARGIN_THRESHOLD = 45.0
CPG_THRESHOLD = 0.05
CASH_WEEKS_RED = 4.0
CASH_WEEKS_YELLOW = 6.0

def read_csv(path: Path):
    if not path or not path.exists():
        return [], None
    with path.open(encoding='utf-8') as f:
        r=csv.DictReader(f)
        rows=list(r) if r.fieldnames else []
        return rows, r.fieldnames

def filter_station(rows, station):
    if not station or not rows:
        return rows
    # any column that looks like location
    loc_keys=[k for k in rows[0].keys() if k.lower() in ("location","station","site")] if rows else []
    if not loc_keys:
        return rows
    k=loc_keys[0]
    filtered=[r for r in rows if r.get(k,"").strip()==station]
    return filtered if filtered else rows

def kpi_metrics(rows):
    # expects week_start,gallons_sold,fuel_sales,fuel_cost,store_sales,store_cogs,labor_cost,cash_variance
    out=[]
    for r in rows:
        try:
            gal=float(r["gallons_sold"])
            fuel_sales=float(r["fuel_sales"]); fuel_cost=float(r["fuel_cost"])
            store_sales=float(r["store_sales"]); store_cogs=float(r["store_cogs"])
            labor=float(r["labor_cost"]); cash_var=float(r.get("cash_variance",0))
            fuel_margin=fuel_sales-fuel_cost
            cpg=fuel_margin/gal if gal else 0
            store_margin=store_sales-store_cogs
            store_pct=store_margin/store_sales*100 if store_sales else 0
            gross=fuel_margin+store_margin
            labor_pct=labor/gross*100 if gross else 0
        except Exception:
            continue
        out.append({
            "week": r["week_start"],
            "gal": gal,
            "cpg": cpg,
            "fuel_margin": fuel_margin,
            "store_pct": store_pct,
            "store_margin": store_margin,
            "gross": gross,
            "labor": labor,
            "labor_pct": labor_pct,
            "cash_var": cash_var,
        })
    # sort by week
    out.sort(key=lambda x: x["week"])
    last4=out[-4:] if len(out)>=4 else out
    return out, last4

def sparkline_svg(values, w=80, h=20):
    if not values or len(values)<2:
        return '<span style="color:#999">—</span>'
    mn=min(values); mx=max(values)
    rng=mx-mn if mx!=mn else 1
    # pad
    pad=2
    points=[]
    for i,v in enumerate(values):
        x=pad + i*(w-2*pad)/(len(values)-1)
        y=h-pad - (v - mn)/rng * (h-2*pad)
        points.append(f"{x:.1f},{y:.1f}")
    poly=" ".join(points)
    color="#0f766e" if values[-1]>=values[0] else "#dc2626"
    return f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg"><polyline fill="none" stroke="{color}" stroke-width="1.6" stroke-linejoin="round" stroke-linecap="round" points="{poly}"/><circle cx="{points[-1].split(",")[0]}" cy="{points[-1].split(",")[1]}" r="2" fill="{color}"/></svg>'

def inventory_top5(rows):
    # compute total shrink $ by sku across file
    totals=defaultdict(lambda: {"sku":"","category":"","shrink_qty":0,"shrink_dollars":0,"weeks_flagged":0,"occurrences":0})
    # per row calc same as shrink_tracker.py
    for r in rows:
        try:
            begin=int(float(r["begin_count"])); rec=int(float(r["received"])); pos=int(float(r["pos_sales_qty"])); end=int(float(r["end_count"]))
            cost=float(r.get("purchased_cost",0) or r.get("unit_retail",0) or 0)
            retail=float(r.get("unit_retail",0) or 0)
            unit_cost=cost if cost>0 else retail
            expected=begin+rec-pos
            shrink_qty=expected - end
            shrink_dollars=shrink_qty * unit_cost if shrink_qty>0 else 0
            base=pos*unit_cost if pos else 1
            shrink_pct=shrink_dollars/base*100 if base else 0
        except:
            continue
        key=(r.get("sku","").strip(), r.get("location","").strip())
        totals[key]["sku"]=r.get("sku","").strip()
        totals[key]["category"]=r.get("category","").strip()
        totals[key]["location"]=r.get("location","").strip()
        if shrink_qty>0:
            totals[key]["shrink_qty"]+=shrink_qty
            totals[key]["shrink_dollars"]+=shrink_dollars
            # flag per original thresholds
            if shrink_pct>2 or shrink_dollars>75:
                totals[key]["weeks_flagged"]+=1
            totals[key]["occurrences"]+=1
    # top 5 by dollars
    ranked=sorted(totals.values(), key=lambda x: x["shrink_dollars"], reverse=True)[:5]
    return ranked

def cash_metrics(rows):
    if not rows:
        return None
    ending=None
    outflows=[]
    for r in rows:
        try:
            bc=float(r["begin_cash"]) if r.get("begin_cash","").strip() else 0
            if ending is not None:
                bc=ending
            fuel_g=float(r["fuel_gross"]); store_g=float(r["store_gross"]); other=float(r.get("other_income",0))
            payroll=float(r["payroll"]); rent=float(r["rent"]); fuel_pay=float(r["fuel_payables"])
            debt=float(r["debt_service"]); tax=float(r["tax_reserve"]); capex=float(r["capex"])
        except:
            continue
        inflow=fuel_g+store_g+other
        outflow=payroll+rent+fuel_pay+debt+tax+capex
        outflows.append(outflow)
        net=inflow - outflow
        ending=bc + net
    if not outflows:
        return None
    avg=sum(outflows)/len(outflows)
    weeks_cover=ending/avg if avg else 0
    return {"ending": ending, "avg_out": avg, "weeks_cover": weeks_cover, "rows": len(rows)}

def reconciliation_flags(rows):
    if not rows:
        return {"total":0,"cash_flags":0,"gal_flags":0}
    cash_f=0; gal_f=0
    for r in rows:
        try:
            cash_exp=float(r.get("cash_expected",0)); cash_act=float(r.get("cash_actual",0))
            gal_pos=float(r.get("pump_gallons",0)); atg=float(r.get("atg_gallons",0))
        except:
            continue
        cash_pct=abs(cash_act-cash_exp)/abs(cash_exp)*100 if cash_exp else 0
        if abs(cash_act-cash_exp)>20 or cash_pct>1:
            cash_f+=1
        gal_pct=abs(gal_pos-atg)/abs(gal_pos)*100 if gal_pos else 0
        if gal_pct>0.5:
            gal_f+=1
    return {"total": len(rows), "cash_flags": cash_f, "gal_flags": gal_f}

def labor_flags(rows):
    if not rows:
        return {"count":0,"ot":0,"minor":0,"unqual":0}
    ot=0; minor=0; unqual=0
    for r in rows:
        try:
            age=int(float(r["age"])); sched=float(r["scheduled_hours"]); actual=float(r["actual_hours"])
            qual=(r.get("tobacco_alcohol_qualified","").strip().upper()=="Y")
            role=r.get("role","").lower()
            handles="cashier" in role or "shift" in role
        except:
            continue
        if actual>40:
            ot+=1
        if age<18 and handles:
            minor+=1
        if not qual and handles and age>=18:
            unqual+=1
    return {"count": len(rows), "ot": ot, "minor": minor, "unqual": unqual}

def build_html(kpi_all, kpi_last4, top5, cash, recon, labor, station, generated_on):
    # sparklines
    gal_vals=[k["gal"] for k in kpi_last4]
    cpg_vals=[k["cpg"] for k in kpi_last4]
    store_vals=[k["store_pct"] for k in kpi_last4]
    gross_vals=[k["gross"] for k in kpi_last4]
    # cash gauge
    cover=cash["weeks_cover"] if cash else 0
    cover_color="#dc2626" if cover < CASH_WEEKS_RED else ("#d97706" if cover < CASH_WEEKS_YELLOW else "#16a34a")
    cover_label="RED <4w" if cover <4 else ("CAUTION 4-6w" if cover <6 else "HEALTHY 6w+")
    # table rows for KPI 4-week
    kpi_rows=""
    for k in kpi_last4:
        labor_flag=" 🔴" if k["labor_pct"]>LABOR_THRESHOLD_PCT else ""
        store_flag=" 🔴" if k["store_pct"]<STORE_MARGIN_THRESHOLD else ""
        cpg_flag=" 🔴" if k["cpg"]<CPG_THRESHOLD else ""
        kpi_rows+=f"""
        <tr>
          <td>{html.escape(k['week'])}</td>
          <td style="text-align:right">{k['gal']:,.0f}</td>
          <td style="text-align:right">{k['cpg']:.3f}{cpg_flag}</td>
          <td style="text-align:right">{k['store_pct']:.1f}%{store_flag}</td>
          <td style="text-align:right">${k['gross']:,.0f}</td>
          <td style="text-align:right">{k['labor_pct']:.1f}%{labor_flag}</td>
          <td style="text-align:right;color:{'#dc2626' if abs(k['cash_var'])>20 else '#111'}">${k['cash_var']:+.2f}</td>
        </tr>"""

    # top5 rows
    if top5:
        top_rows=""
        for t in top5:
            flag="🔴" if t["weeks_flagged"]>0 else "—"
            top_rows+=f"<tr><td>{html.escape(t['sku'])}</td><td>{html.escape(t['category'])}</td><td style='text-align:right'>{t['shrink_qty']:+d}</td><td style='text-align:right'>${t['shrink_dollars']:,.2f}</td><td style='text-align:center'>{t['weeks_flagged']}</td><td style='text-align:center'>{flag} daily 2-person count</td></tr>"
    else:
        top_rows="<tr><td colspan=6 style='text-align:center;color:#666'>No shrink data — run inventory 4 weeks first</td></tr>"

    # compliance strip
    price_log_exists = Path("ops/compliance/price_change_log.csv").exists()
    price_note = "Price log present" if price_log_exists else "No price log yet — log every $ change with BOL ref"
    recon_note = f"{recon['cash_flags']} cash / {recon['gal_flags']} gal flags in last {recon['total']} days" if recon['total'] else "No reconciliation data"
    labor_note = f"{labor['ot']} OT / {labor['minor']} minor-risk / {labor['unqual']} unqualified" if labor['count'] else "No labor data"

    html_doc=f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Station Dashboard — {html.escape(station or 'Station-1')} | {html.escape(generated_on)}</title>
<style>
  :root {{ --red:#dc2626; --yellow:#d97706; --green:#16a34a; --ink:#0f172a; --muted:#64748b; --line:#e2e8f0; --bg:#f8fafc; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; font-family: ui-sans, system-ui, -apple-system, Segoe UI, Roboto, Arial; color:var(--ink); background:#fff; font-size:12px; line-height:1.35; }}
  header {{ display:flex; justify-content:space-between; align-items:flex-start; border-bottom:2px solid var(--ink); padding:10px 14px 8px; }}
  header h1 {{ margin:0; font-size:14px; letter-spacing:.2px; }}
  header .meta {{ text-align:right; font-size:11px; color:var(--muted); }}
  .grid {{ display:grid; grid-template-columns: 1.6fr 1fr; gap:10px; padding:10px 14px; }}
  .card {{ border:1px solid var(--line); border-radius:8px; padding:8px 10px; background:var(--bg); }}
  .card h2 {{ margin:0 0 6px; font-size:11px; letter-spacing:.6px; text-transform:uppercase; color:var(--muted); }}
  table {{ width:100%; border-collapse:collapse; font-size:11px; }}
  th {{ text-align:left; font-weight:600; color:var(--muted); border-bottom:1px solid var(--line); padding:4px 4px; font-size:10px; text-transform:uppercase; letter-spacing:.3px; }}
  td {{ padding:4px 4px; border-bottom:1px solid #f1f5f9; }}
  .kpis {{ display:grid; grid-template-columns: repeat(4,1fr); gap:8px; margin-bottom:8px; }}
  .kpi-mini {{ border:1px solid var(--line); border-radius:8px; padding:6px 8px; background:#fff; text-align:center; }}
  .kpi-mini .label {{ font-size:9px; color:var(--muted); text-transform:uppercase; letter-spacing:.5px; }}
  .kpi-mini .value {{ font-size:13px; font-weight:700; }}
  .kpi-mini .spark {{ margin-top:4px; }}
  .gauge {{ text-align:center; }}
  .gauge .number {{ font-size:20px; font-weight:800; color:{cover_color}; }}
  .gauge .badge {{ display:inline-block; padding:2px 6px; border-radius:999px; font-size:9px; font-weight:700; color:#fff; background:{cover_color}; }}
  .strip {{ display:flex; gap:8px; padding:0 14px 8px; }}
  .strip > div {{ flex:1; border:1px solid var(--line); border-radius:8px; padding:6px 8px; background:#fff; font-size:11px; }}
  .sign {{ display:flex; gap:12px; padding:8px 14px 10px; }}
  .sign > div {{ flex:1; border-top:1px solid var(--ink); padding-top:4px; font-size:11px; text-align:center; }}
  .controls {{ padding:6px 14px; display:flex; gap:8px; justify-content:flex-end; }}
  .btn {{ padding:6px 10px; border:1px solid var(--line); border-radius:6px; background:#fff; cursor:pointer; font-size:11px; }}
  .note {{ font-size:10px; color:var(--muted); padding:0 14px 10px; }}
  @media print {{
    .controls {{ display:none !important; }}
    body {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
    .grid {{ padding:8px 10px; }}
    header {{ padding:8px 10px 6px; }}
  }}
  @media (prefers-color-scheme: dark) {{
    body {{ background:#0b1220; color:#e2e8f0; }}
    .card, .kpi-mini, .strip > div {{ background:#0f172a; border-color:#1e293b; }}
    th {{ color:#94a3b8; border-color:#1e293b; }}
    td {{ border-color:#1e293b; }}
  }}
</style>
</head>
<body>
<header>
  <div>
    <h1>⛽ Mobile 1 Gas — {html.escape(station or 'Station-1')} <span style="font-weight:400; color:var(--muted)">| Strong Ownership Dashboard</span></h1>
    <div style="font-size:11px; color:var(--muted)">Week ending {html.escape(kpi_last4[-1]['week'] if kpi_last4 else generated_on)} • Owner: G.T.Sanga (review) • Builder: ops/dashboard/dashboard_builder.py</div>
  </div>
  <div class="meta">
    <div>Generated {html.escape(generated_on)}</div>
    <div>Last 4 weeks • Print → Save as PDF → file in ops/logs/dashboard/</div>
  </div>
</header>

<div class="controls">
  <button class="btn" onclick="window.print()">⎙ Print / Save PDF</button>
  <button class="btn" onclick="navigator.clipboard.writeText(location.href)">Copy link</button>
</div>

<div class="grid">
  <div class="card">
    <h2>KPI — Last 4 Weeks (execution > market)</h2>
    <div class="kpis">
      <div class="kpi-mini"><div class="label">Gallons</div><div class="value">{kpi_last4[-1]['gal']:,.0f}</div><div class="spark">{sparkline_svg(gal_vals)}</div><div style="font-size:10px;color:var(--muted)">{gal_vals[0]:,.0f} → {gal_vals[-1]:,.0f}</div></div>
      <div class="kpi-mini"><div class="label">CPG Margin</div><div class="value">${kpi_last4[-1]['cpg']:.3f}</div><div class="spark">{sparkline_svg(cpg_vals)}</div><div style="font-size:10px;color:var(--muted)">Fuel margin ÷ gal</div></div>
      <div class="kpi-mini"><div class="label">Store Margin</div><div class="value">{kpi_last4[-1]['store_pct']:.1f}%</div><div class="spark">{sparkline_svg(store_vals)}</div><div style="font-size:10px;color:var(--muted)">Target >45% (52-54% healthy)</div></div>
      <div class="kpi-mini"><div class="label">Gross Profit</div><div class="value">${kpi_last4[-1]['gross']:,.0f}</div><div class="spark">{sparkline_svg(gross_vals)}</div><div style="font-size:10px;color:var(--muted)">Fuel + store gross</div></div>
    </div>
    <table>
      <thead><tr><th>Week</th><th style="text-align:right">Gal</th><th style="text-align:right">CPG</th><th style="text-align:right">Store%</th><th style="text-align:right">Gross</th><th style="text-align:right">Labor%</th><th style="text-align:right">Cash Var</th></tr></thead>
      <tbody>{kpi_rows}</tbody>
    </table>
    <div style="font-size:10px;color:var(--muted);margin-top:4px">🔴 = labor >{LABOR_THRESHOLD_PCT}% / store <{STORE_MARGIN_THRESHOLD}% / cpg <${CPG_THRESHOLD:.2f} — owner decision, not discussion. Trend vs prior week matters more than one week.</div>
  </div>

  <div class="card">
    <h2>Cash — Weeks of Cover (survival)</h2>
    <div class="gauge">
      <div class="number">{cover:.1f} weeks</div>
      <div class="badge">{cover_label}</div>
      <div style="font-size:11px; margin-top:6px; color:var(--muted)">Ending ${cash['ending']:,.0f} ÷ Avg outflow ${cash['avg_out']:,.0f}</div>
    </div>
    <table style="margin-top:8px">
      <tr><th>Ending cash</th><td style="text-align:right">${cash['ending']:,.0f}</td></tr>
      <tr><th>Avg weekly outflow</th><td style="text-align:right">${cash['avg_out']:,.0f}</td></tr>
      <tr><th>Weeks in forecast</th><td style="text-align:right">{cash['rows']}</td></tr>
      <tr><th>Reserve rule</th><td style="text-align:right"><span style="color:var(--red)">RED &lt;{CASH_WEEKS_RED}w</span> • <span style="color:var(--yellow)">{CASH_WEEKS_RED}-{CASH_WEEKS_YELLOW}w caution</span> • <span style="color:var(--green)">6w+ healthy</span></td></tr>
    </table>
    <div style="font-size:10px; color:var(--muted); margin-top:6px">If RED: freeze capex/owner distro, confirm distributor credit line. Do not shift operating cash to crypto/speculation. Ending < avg*4 = action that day.</div>
  </div>
</div>

<div class="grid" style="padding-top:0">
  <div class="card">
    <h2>Shrink — Top 5 by $ Loss (all weeks in file)</h2>
    <table>
      <thead><tr><th>SKU</th><th>Category</th><th style="text-align:right">Qty</th><th style="text-align:right">$ Loss</th><th>Wk Flagged</th><th>Action</th></tr></thead>
      <tbody>{top_rows}</tbody>
    </table>
    <div style="font-size:10px;color:var(--muted);margin-top:4px">Rank = total shrink $ (qty × cost). Flag = >2% or >$75 in any week. Pattern 2 wks → locked case / limit access / invoice scan required.</div>
  </div>
  <div class="card">
    <h2>Compliance & Ops Flags (7-day)</h2>
    <table>
      <tr><th>Reconciliation</th><td>{html.escape(recon_note)}</td></tr>
      <tr><th>Labor</th><td>{html.escape(labor_note)}</td></tr>
      <tr><th>Price log</th><td>{html.escape(price_note)} — every $ change needs BOL/INV reason + dual approval</td></tr>
      <tr><th>Tank</th><td>Check <code>ops/compliance/tank_log.md</code> due date — run <code>--check-tank-due</code></td></tr>
    </table>
    <div style="margin-top:8px; padding:6px; border:1px dashed var(--line); border-radius:6px; background:#fff; font-size:11px">
      <strong>Owner takeaway this week:</strong> Fuel cpg moves with market — win on store margin + labor % + 0 shrink + 0 compliance misses. Clean logs = durable worth.
    </div>
  </div>
</div>

<div class="strip">
  <div><strong>Manager notes (attach to PDF):</strong><br><br><span style="color:var(--muted)">Exceptions, void/refund >$20 with receipt #, price change BOL#</span></div>
  <div><strong>Owner decision:</strong><br><br><span style="color:var(--muted)">System changed this week: ____________________ (not just coaching)</span></div>
</div>

<div class="sign">
  <div>Manager ______ Date ______</div>
  <div>Owner G.T.Sanga ______ Date ______</div>
  <div>CPA ______ Date ______</div>
  <div>File: ops/logs/dashboard/YYYY-W___.pdf</div>
</div>

<div class="note">General information only — not legal/tax/safety advice. thresholds (labor 35%, store 45%, cover 4/6 wks) match suite defaults — have CPA/lease adjust. Generated offline, no external calls, no wallet operations. Source CSVs versioned; PDFs gitignored.</div>

</body>
</html>"""
    return html_doc

def main():
    ap=argparse.ArgumentParser(description="One-page dashboard builder")
    ap.add_argument("--kpi", default=str(DEFAULTS["kpi"]), help="KPI CSV (last 4 weeks)")
    ap.add_argument("--inventory", default=str(DEFAULTS["inventory"]), help="Inventory CSV")
    ap.add_argument("--cashflow", default=str(DEFAULTS["cashflow"]), help="Cashflow CSV")
    ap.add_argument("--reconciliation", default=str(DEFAULTS["reconciliation"]), help="Reconciliation POS CSV")
    ap.add_argument("--labor", default=str(DEFAULTS["labor"]), help="Labor schedule CSV")
    ap.add_argument("--station", default="", help="Filter to station name if multi-site file")
    args=ap.parse_args()

    # resolve paths relative to repo root if needed
    def resolve(p):
        pp=Path(p)
        if pp.exists():
            return pp
        # try from repo root
        alt=Path.cwd() / p
        if alt.exists():
            return alt
        # try relative to dashboard folder root
        alt2=ROOT.parent.parent / p
        if alt2.exists():
            return alt2
        return pp

    kpi_p=resolve(args.kpi); inv_p=resolve(args.inventory); cash_p=resolve(args.cashflow)
    rec_p=resolve(args.reconciliation); lab_p=resolve(args.labor)

    kpi_rows,_ = read_csv(kpi_p)
    kpi_rows = filter_station(kpi_rows, args.station)
    inv_rows,_ = read_csv(inv_p)
    inv_rows = filter_station(inv_rows, args.station)
    cash_rows,_ = read_csv(cash_p)
    rec_rows,_ = read_csv(rec_p)
    rec_rows = filter_station(rec_rows, args.station)
    lab_rows,_ = read_csv(lab_p)

    # fallback to sample_data if defaults missing
    if not kpi_rows and not kpi_p.exists():
        kpi_rows,_ = read_csv(DEFAULTS["kpi"])
    if not inv_rows and not inv_p.exists():
        inv_rows,_ = read_csv(DEFAULTS["inventory"])
    if not cash_rows and not cash_p.exists():
        cash_rows,_ = read_csv(DEFAULTS["cashflow"])

    kpi_all, kpi_last4 = kpi_metrics(kpi_rows)
    if not kpi_last4:
        print("ERROR: no KPI rows parsed — check CSV header week_start,location,gallons_sold,fuel_sales,fuel_cost,store_sales,store_cogs,labor_cost,cash_variance")
        return
    top5 = inventory_top5(inv_rows)
    cash = cash_metrics(cash_rows) or {"ending":0,"avg_out":1,"weeks_cover":0,"rows":0}
    recon = reconciliation_flags(rec_rows)
    labor = labor_flags(lab_rows)

    station_name = args.station or (kpi_last4[-1].get("location") if hasattr(kpi_last4[-1], 'get') else None)  # fallback
    # station from KPI last row location field not in kpi_all dict, get from original rows
    if not args.station and kpi_rows:
        # last row's location
        loc_key=next((k for k in kpi_rows[0].keys() if k.lower()=="location"), None)
        if loc_key:
            station_name=kpi_rows[-1].get(loc_key,"Station-1")

    generated_on=datetime.now().strftime("%Y-%m-%d %H:%M")
    html_out=build_html(kpi_all, kpi_last4, top5, cash, recon, labor, station_name or "Station-1", generated_on)

    out_path=ROOT / "dashboard.html"
    out_path.write_text(html_out, encoding='utf-8')
    print(f"Built {out_path} from:")
    print(f"  KPI {kpi_p} ({len(kpi_rows)} rows, last4 weeks used)")
    print(f"  Inventory {inv_p} ({len(inv_rows)} rows, top5 ranked)")
    print(f"  Cashflow {cash_p} ({len(cash_rows)} rows, cover {cash['weeks_cover']:.1f} wks)")
    print(f"  Recon {rec_p} ({len(rec_rows)} rows) Labor {lab_p} ({len(lab_rows)} rows)")
    print(f"Open: file://{out_path.resolve()} → Print → Save as PDF → ops/logs/dashboard/")
    # also ensure logs folder exists
    Path("ops/logs/dashboard").mkdir(parents=True, exist_ok=True)
    # write a copy into logs for filing
    try:
        safe_week=str(kpi_last4[-1]['week']).replace("/","-")
        log_copy=Path(f"ops/logs/dashboard/{safe_week}_dashboard.html")
        log_copy.write_text(html_out, encoding='utf-8')
        print(f"Also saved filing copy to {log_copy}")
    except Exception as e:
        print(f"Filing copy note: {e}")

if __name__=="__main__":
    main()

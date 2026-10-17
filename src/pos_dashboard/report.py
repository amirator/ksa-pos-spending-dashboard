"""Write the executive summary (Markdown), the 2-page PDF and the interactive HTML dashboard."""
from __future__ import annotations

import html
import textwrap
from datetime import date

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

from .charts import SOURCE_NOTE, draw_dashboard, kpi_cards, plotly_figures, save_individual_figures
from .config import PALETTE as C
from .config import REPORTS
from .insights import build_insights

METHOD_NOTE = (
    "Method: the raw SAMA CSVs are loaded into DuckDB, cleaned and pivoted in SQL, and modelled as a star schema "
    "(dim_date with Umm al-Qura Ramadan/Eid flags, dim_city, dim_sector, three weekly fact tables). Years are compared "
    "on average weekly values because some calendar years hold 53 week-starts. The newer SAMA release is appended "
    "only for national and city totals, which match the older release in the overlapping weeks; sector trends stop "
    "in July 2025 because the sector taxonomy changed. Figures cover card POS terminals only (no cash, no e-commerce)."
)


def write_markdown(k: dict, insights: list[dict]) -> str:
    lines = [
        "# Executive summary: Saudi Consumer Spending Pulse",
        "",
        f"*Data: SAMA weekly point-of-sale statistics, {k['coverage']['first_week']} to {k['coverage']['last_week']} "
        f"({k['coverage']['weeks']} weeks). Generated {date.today().isoformat()} by `python run.py`; every figure "
        f"below is read from `data/processed/kpis.json`.*",
        "",
        "## Headline KPIs",
        "",
        "| KPI | Value | Context |",
        "|---|---|---|",
    ]
    lines += [f"| {a} | {b} | {c} |" for a, b, c in kpi_cards(k)]
    lines += ["", "## Key insights", ""]
    for i, ins in enumerate(insights, 1):
        lines += [f"**{i}. {ins['title']}.** {ins['body']}", "", f"*So what:* {ins['so_what']}", ""]
    lines += ["## Method and caveats", "", METHOD_NOTE, "", SOURCE_NOTE, ""]
    md = "\n".join(lines)
    (REPORTS / "executive_summary.md").write_text(md)
    return md


def _summary_page(pdf: PdfPages, k: dict, insights: list[dict]) -> None:
    fig = plt.figure(figsize=(16, 9.6), facecolor="white")
    fig.text(0.05, 0.93, "Executive summary", fontsize=20, weight="bold", color=C["dark"])
    fig.text(0.05, 0.895, f"Saudi Consumer Spending Pulse | SAMA weekly POS data, {k['coverage']['first_week']} "
             f"to {k['coverage']['last_week']}", fontsize=10.5, color=C["muted"])
    y = 0.84
    for i, ins in enumerate(insights, 1):
        fig.text(0.05, y, f"{i}. {ins['title']}", fontsize=12, weight="bold", color=C["primary"])
        y -= 0.03
        for line in textwrap.wrap(ins["body"], 175):
            fig.text(0.065, y, line, fontsize=9.6, color=C["dark"])
            y -= 0.024
        for line in textwrap.wrap("So what: " + ins["so_what"], 175):
            fig.text(0.065, y, line, fontsize=9.6, color=C["muted"], style="italic")
            y -= 0.024
        y -= 0.018
    for line in textwrap.wrap(METHOD_NOTE, 210):
        fig.text(0.05, y, line, fontsize=8, color=C["muted"])
        y -= 0.019
    fig.text(0.05, 0.03, SOURCE_NOTE, fontsize=6.8, color=C["muted"])
    pdf.savefig(fig)
    plt.close(fig)


def write_html(f: dict, k: dict, insights: list[dict]) -> None:
    figs = plotly_figures(f)
    divs = [g.to_html(full_html=False, include_plotlyjs=(i == 0), config={"displaylogo": False})
            for i, g in enumerate(figs)]
    cards = "".join(
        f'<div class="card"><div class="lab">{html.escape(a)}</div><div class="val">{html.escape(b)}</div>'
        f'<div class="sub {"neg" if c.strip().startswith("-") else ""}">{html.escape(c)}</div></div>'
        for a, b, c in kpi_cards(k)
    )
    ins = "".join(
        f"<li><b>{html.escape(x['title'])}.</b> {html.escape(x['body'])}<br><i>So what: {html.escape(x['so_what'])}</i></li>"
        for x in insights
    )
    grid = "".join(f'<div class="panel{" wide" if i in (0, len(divs) - 1) else ""}">{d}</div>' for i, d in enumerate(divs))
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Saudi Consumer Spending Pulse | SAMA POS dashboard</title>
<style>
 body{{margin:0;background:{C['bg']};font-family:"Segoe UI",Arial,sans-serif;color:{C['dark']}}}
 header{{padding:22px 32px 6px}} h1{{margin:0;font-size:28px}} .subt{{color:{C['muted']};margin-top:4px}}
 .cards{{display:grid;grid-template-columns:repeat(5,1fr);gap:14px;padding:14px 32px}}
 .card{{background:#fff;border:1px solid {C['light']};border-left:5px solid {C['primary']};border-radius:8px;padding:12px 16px}}
 .lab{{color:{C['muted']};font-size:13px}} .val{{font-size:26px;font-weight:700;margin:4px 0}}
 .sub{{color:{C['primary']};font-size:13px}} .sub.neg{{color:{C['neg']}}}
 .grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:14px;padding:0 32px}}
 .panel{{background:#fff;border:1px solid {C['light']};border-radius:8px;padding:6px}} .wide{{grid-column:1/-1}}
 section{{padding:10px 32px 30px}} li{{margin-bottom:10px;line-height:1.45}} .note{{color:{C['muted']};font-size:12px}}
 @media(max-width:900px){{.cards{{grid-template-columns:repeat(2,1fr)}}.grid{{grid-template-columns:1fr}}}}
</style></head><body>
<header><h1>Saudi Consumer Spending Pulse</h1>
<div class="subt">Weekly card point-of-sale spending in KSA, {k['coverage']['first_week']} to {k['coverage']['last_week']}
 ({k['coverage']['weeks']} weeks). Hover the charts for exact values.</div></header>
<div class="cards">{cards}</div>
<div class="grid">{grid}</div>
<section><h2>Executive summary</h2><ol>{ins}</ol>
<p class="note">{html.escape(METHOD_NOTE)}</p><p class="note">{html.escape(SOURCE_NOTE)}</p></section>
</body></html>"""
    (REPORTS / "dashboard.html").write_text(page, encoding="utf-8")


def build_reports(f: dict, k: dict) -> dict:
    REPORTS.mkdir(parents=True, exist_ok=True)
    insights = build_insights(k)
    write_markdown(k, insights)
    with PdfPages(REPORTS / "dashboard_and_summary.pdf") as pdf:
        draw_dashboard(f, k, REPORTS / "dashboard.png", pdf=pdf)
        _summary_page(pdf, k, insights)
        meta = pdf.infodict()
        meta["Title"] = "Saudi Consumer Spending Pulse"
        meta["Subject"] = "SAMA weekly POS KPI dashboard"
    figs = save_individual_figures(f)
    write_html(f, k, insights)
    print(f"[report] dashboard.png, dashboard_and_summary.pdf, dashboard.html, executive_summary.md, {len(figs)} figures")
    return {"insights": insights}

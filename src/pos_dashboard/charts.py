"""Static (matplotlib) Power BI-style dashboard + individual figures, and Plotly figures for HTML."""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
import plotly.graph_objects as go
from matplotlib.patches import FancyBboxPatch

from .config import FIGURES, PALETTE as C

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 9,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.edgecolor": C["light"],
    "axes.labelcolor": C["dark"],
    "xtick.color": C["muted"],
    "ytick.color": C["muted"],
    "axes.titleweight": "bold",
    "axes.titlesize": 10.5,
    "axes.titlecolor": C["dark"],
    "axes.titlelocation": "left",
})

SOURCE_NOTE = ("Source: Saudi Central Bank (SAMA) weekly POS statistics via KAPSARC Data Portal "
               "(datasets: point-of-sale-transactions-by-sector-and-city; detailed-point-of-sale-transactions-by-sector-and-city). "
               "Values are card POS transactions only; analysis by the author.")


SHORT = {
    "Miscellaneous Goods and Services": "Misc. goods & services",
    "Construction & Building Materials": "Building materials",
    "Electronic & Electric Devices": "Electronics",
    "Clothing and Footwear": "Clothing & footwear",
    "Beverage and Food": "Food & beverage",
    "Restaurants & Café": "Restaurants & cafés",
    "Recreation and Culture": "Recreation & culture",
}


def kpi_cards(k: dict) -> list[tuple[str, str, str]]:
    h, y, c = k["headline"], k["latest_ytd"], k["cities"]
    f0, f1 = k["first_full_year"], k["last_full_year"]
    return [
        (f"POS spending {f1}", f"SAR {h['value_bn_sar']:.0f} bn", f"{h['value_yoy_pct']:+.1f}% YoY (avg weekly)"),
        (f"Transactions {f1}", f"{h['txn_bn']:.2f} bn", f"{h['txn_yoy_pct']:+.1f}% YoY"),
        (f"Average ticket {f1}", f"SAR {h['avg_ticket_sar']:.1f}", f"{h['avg_ticket_change_pct']:+.1f}% vs {f0}"),
        (f"Riyadh share {f1}", f"{c['riyadh_share_last']:.1f}%", f"Jeddah {c['jeddah_share_last']:.1f}%"),
        (f"{y['to'][:4]} to date ({y['weeks']} wks)", f"SAR {y['value_bn_sar']:.0f} bn", f"{y['value_yoy_pct']:+.1f}% vs same weeks"),
    ]


# ---------------------------------------------------------------- matplotlib panels
def _shade_ramadan(ax, nw):
    ram = nw[nw.is_ramadan_week]
    for wk in ram.week_start:
        ax.axvspan(wk, wk + pd.Timedelta(days=7), color=C["accent"], alpha=0.18, lw=0)


def p_trend(ax, f):
    nw = f["national_weekly"]
    _shade_ramadan(ax, nw)
    ax.plot(nw.week_start, nw.value_bn_sar, color=C["muted"], lw=0.7, alpha=0.6, label="Weekly")
    ax.plot(nw.week_start, nw.value_bn_sar_4wk_avg, color=C["primary"], lw=1.8, label="4-week average")
    b = nw[nw.source == "B"].week_start.min()
    ax.axvline(b, color=C["dark"], lw=0.6, ls=":")
    ax.text(b, ax.get_ylim()[1] * 0.98, " newer SAMA release", fontsize=7, color=C["muted"], va="top")
    ax.set_title("Weekly POS spending, SAR bn (gold bands = Ramadan weeks)")
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.legend(frameon=False, fontsize=7.5, loc="upper left")
    ax.grid(axis="y", color=C["light"], lw=0.6)


def p_yearly(ax, f):
    ny = f["national_yearly"]
    bars = ax.bar(ny.year.astype(str), ny.avg_weekly_value_bn_sar, color=C["primary"], width=0.72)
    for b, v, g in zip(bars, ny.avg_weekly_value_bn_sar, ny.value_yoy_pct):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.2, f"{v:.1f}", ha="center", fontsize=8, color=C["dark"])
        if pd.notna(g):
            ax.text(b.get_x() + b.get_width() / 2, v / 2, f"{g:+.1f}%", ha="center", fontsize=6.8, color="white", weight="bold")
    ax.set_title("Avg weekly spend, SAR bn\n(label = YoY %)")
    ax.set_ylim(0, ny.avg_weekly_value_bn_sar.max() * 1.15)
    ax.set_yticks([])
    ax.spines["left"].set_visible(False)


def p_sectors(ax, f):
    s = f["sector_mix"].head(10).iloc[::-1]
    cmap = matplotlib.colormaps["RdYlGn"]
    norm = matplotlib.colors.TwoSlopeNorm(vmin=min(-10, s.cagr_2021_2024_pct.min()), vcenter=0,
                                          vmax=max(25, s.cagr_2021_2024_pct.max()))
    ax.barh([SHORT.get(n, n) for n in s.sector_name], s.share_2024_pct, color=[cmap(norm(v)) for v in s.cagr_2021_2024_pct])
    for i, (sh, g) in enumerate(zip(s.share_2024_pct, s.cagr_2021_2024_pct)):
        ax.text(sh + 0.3, i, f"{sh:.1f}%  ({g:+.0f}%/yr)", va="center", fontsize=7, color=C["dark"])
    ax.set_title("Top 10 sectors: share of 2024 value\n(colour/label = CAGR 2021-24)")
    ax.set_xlim(0, s.share_2024_pct.max() * 1.6)
    ax.tick_params(axis="y", labelsize=7.5)
    ax.set_xticks([])
    ax.spines["bottom"].set_visible(False)


def p_cities(ax, f):
    cs = f["city_share"]
    y0, y1 = cs.year.min(), cs.year.max()
    a = cs[cs.year == y0].set_index("city_name").share_pct
    b = cs[cs.year == y1].set_index("city_name").share_pct
    order = b.sort_values().index
    for i, city in enumerate(order):
        col = C["primary"] if b[city] >= a[city] else C["neg"]
        ax.plot([a[city], b[city]], [i, i], color=col, lw=2)
        ax.scatter(a[city], i, color=C["muted"], s=18, zorder=3)
        ax.scatter(b[city], i, color=col, s=26, zorder=3)
        ax.text(max(a[city], b[city]) + 0.8, i, f"{b[city]:.1f}%", va="center", fontsize=7)
    ax.set_yticks(range(len(order)), order, fontsize=7.5)
    ax.set_title(f"City share of national value\n{y0} (grey) to {y1}")
    ax.set_xlim(0, b.max() * 1.18)
    ax.grid(axis="x", color=C["light"], lw=0.6)


def p_ticket(ax, f):
    ny = f["national_yearly"]
    base_t, base_n = ny.avg_ticket_sar.iloc[0], ny.avg_weekly_txn_mn.iloc[0]
    yrs = ny.year.astype(str)
    ax.plot(yrs, 100 * ny.avg_weekly_txn_mn / base_n, marker="o", color=C["primary"], label="Transactions")
    ax.plot(yrs, 100 * ny.avg_weekly_value_bn_sar / ny.avg_weekly_value_bn_sar.iloc[0], marker="o",
            color=C["accent"], label="Value")
    ax.plot(yrs, 100 * ny.avg_ticket_sar / base_t, marker="o", color=C["neg"], label="Avg ticket")
    for x, t in zip(yrs, ny.avg_ticket_sar):
        ax.annotate(f"SAR {t:.0f}", (x, 100 * t / base_t), textcoords="offset points", xytext=(0, -12),
                    ha="center", fontsize=6.5, color=C["neg"])
    ax.axhline(100, color=C["light"], lw=0.8)
    ax.set_title(f"More, smaller payments\n(index, {ny.year.iloc[0]} = 100)")
    ax.set_ylim(40, None)
    ax.legend(frameon=False, fontsize=7, loc="upper left")
    ax.grid(axis="y", color=C["light"], lw=0.6)


def p_ramadan(ax, f):
    r = f["ramadan_effect"]
    x = range(len(r))
    w = 0.38
    ax.bar([i - w / 2 for i in x], r.peak_week_index - 100, w, color=C["primary"], label="Peak week (Ramadan to Eid)")
    ax.bar([i + w / 2 for i in x], r.post_eid_week_index - 100, w, color=C["neg"], label="Week after Eid")
    for i, (p, q) in enumerate(zip(r.peak_week_index - 100, r.post_eid_week_index - 100)):
        ax.text(i - w / 2, p + 1, f"{p:+.0f}%", ha="center", fontsize=6.5)
        ax.text(i + w / 2, q - 4, f"{q:+.0f}%", ha="center", fontsize=6.5)
    ax.axhline(0, color=C["dark"], lw=0.6)
    ax.set_xticks(list(x), r.year.astype(str))
    ax.set_title("Ramadan/Eid swing vs the\n4 weeks before Ramadan")
    ax.set_ylim(min(-35, (r.post_eid_week_index - 100).min() - 8), (r.peak_week_index - 100).max() + 42)
    ax.legend(frameon=False, fontsize=6.8, loc="upper left", ncol=1)


PANELS = {
    "01_weekly_trend": p_trend,
    "02_yearly_growth": p_yearly,
    "03_sector_mix": p_sectors,
    "04_city_share": p_cities,
    "05_ticket_vs_volume": p_ticket,
    "06_ramadan_eid": p_ramadan,
}


def draw_dashboard(f: dict, k: dict, path_png, pdf=None):
    fig = plt.figure(figsize=(16, 9.6), facecolor=C["bg"])
    gs = fig.add_gridspec(3, 4, height_ratios=[0.5, 1.2, 1.3], left=0.085, right=0.985, top=0.885,
                          bottom=0.06, hspace=0.42, wspace=0.45)
    fig.text(0.085, 0.955, "Saudi Consumer Spending Pulse", fontsize=20, weight="bold", color=C["dark"])
    fig.text(0.085, 0.92, f"Weekly card point-of-sale spending in KSA, {k['coverage']['first_week']} to "
             f"{k['coverage']['last_week']} ({k['coverage']['weeks']} weeks)", fontsize=10.5, color=C["muted"])
    # KPI cards
    cards = kpi_cards(k)
    card_ax = fig.add_subplot(gs[0, :])
    card_ax.axis("off")
    n = len(cards)
    for i, (lab, val, sub) in enumerate(cards):
        x0 = i / n + 0.004
        card_ax.add_patch(FancyBboxPatch((x0, 0.02), 1 / n - 0.012, 0.96, boxstyle="round,pad=0,rounding_size=0.04",
                                         transform=card_ax.transAxes, facecolor="white", edgecolor=C["light"]))
        card_ax.add_patch(FancyBboxPatch((x0, 0.02), 0.004, 0.96, boxstyle="square,pad=0", transform=card_ax.transAxes,
                                         facecolor=C["primary"], edgecolor="none"))
        card_ax.text(x0 + 0.015, 0.74, lab, transform=card_ax.transAxes, fontsize=9, color=C["muted"])
        card_ax.text(x0 + 0.015, 0.36, val, transform=card_ax.transAxes, fontsize=17, weight="bold", color=C["dark"])
        neg = sub.strip().startswith("-")
        card_ax.text(x0 + 0.015, 0.11, sub, transform=card_ax.transAxes, fontsize=8.5,
                     color=C["neg"] if neg else C["primary"])
    axes = [fig.add_subplot(gs[1, 0:3]), fig.add_subplot(gs[1, 3]),
            fig.add_subplot(gs[2, 0]), fig.add_subplot(gs[2, 1]), fig.add_subplot(gs[2, 2]), fig.add_subplot(gs[2, 3])]
    for ax, fn in zip(axes, PANELS.values()):
        ax.set_facecolor("white")
        fn(ax, f)
    fig.text(0.085, 0.018, SOURCE_NOTE, fontsize=6.8, color=C["muted"])
    fig.savefig(path_png, dpi=150, facecolor=fig.get_facecolor())
    if pdf is not None:
        pdf.savefig(fig, facecolor=fig.get_facecolor())
    plt.close(fig)


def save_individual_figures(f: dict) -> list:
    FIGURES.mkdir(parents=True, exist_ok=True)
    out = []
    for name, fn in PANELS.items():
        size = (11, 4) if name == "01_weekly_trend" else (6.4, 4.2)
        fig, ax = plt.subplots(figsize=size)
        fn(ax, f)
        fig.tight_layout()
        p = FIGURES / f"{name}.png"
        fig.savefig(p, dpi=150)
        plt.close(fig)
        out.append(p)
    return out


# ---------------------------------------------------------------- plotly (interactive HTML)
def plotly_figures(f: dict) -> list[go.Figure]:
    lay = dict(template="plotly_white", margin=dict(l=40, r=20, t=50, b=40), height=380,
               font=dict(family="Segoe UI, Arial", size=12), colorway=[C["primary"], C["accent"], C["neg"]])
    nw, ny, sec, cs, r = (f["national_weekly"], f["national_yearly"], f["sector_mix"], f["city_share"],
                          f["ramadan_effect"])
    figs = []

    g = go.Figure()
    g.add_scatter(x=nw.week_start, y=nw.value_bn_sar, name="Weekly", line=dict(color=C["muted"], width=1))
    g.add_scatter(x=nw.week_start, y=nw.value_bn_sar_4wk_avg, name="4-week avg", line=dict(color=C["primary"], width=2.5))
    ram = nw[nw.is_ramadan_week]
    g.add_bar(x=ram.week_start, y=[nw.value_bn_sar.max() * 1.05] * len(ram), name="Ramadan week",
              marker_color=C["accent"], opacity=0.25, hoverinfo="skip")
    g.update_layout(title="Weekly POS spending (SAR bn)", hovermode="x unified", bargap=0, **lay)
    figs.append(g)

    g = go.Figure(go.Bar(x=ny.year.astype(str), y=ny.avg_weekly_value_bn_sar, marker_color=C["primary"],
                         text=[f"{v:.1f}<br>{'' if pd.isna(p) else f'{p:+.1f}%'}" for v, p in
                               zip(ny.avg_weekly_value_bn_sar, ny.value_yoy_pct)], textposition="outside"))
    g.update_layout(title="Average weekly spend by year (SAR bn, YoY %)", **lay)
    figs.append(g)

    s = sec.head(10).iloc[::-1]
    g = go.Figure(go.Bar(y=s.sector_name, x=s.share_2024_pct, orientation="h",
                         marker=dict(color=s.cagr_2021_2024_pct, colorscale="RdYlGn", cmid=0,
                                     colorbar=dict(title="CAGR %")),
                         text=[f"{a:.1f}% ({b:+.0f}%/yr)" for a, b in zip(s.share_2024_pct, s.cagr_2021_2024_pct)],
                         textposition="outside", cliponaxis=False))
    g.update_xaxes(range=[0, s.share_2024_pct.max() * 1.45])
    g.update_layout(title="Top 10 sectors: share of 2024 value (colour = CAGR 2021-24)", **lay)
    figs.append(g)

    y0, y1 = cs.year.min(), cs.year.max()
    w = cs.pivot(index="city_name", columns="year", values="share_pct").sort_values(y1)
    g = go.Figure()
    g.add_bar(y=w.index, x=w[y0], name=str(y0), orientation="h", marker_color=C["light"])
    g.add_bar(y=w.index, x=w[y1], name=str(y1), orientation="h", marker_color=C["primary"])
    g.update_layout(title=f"City share of national POS value, {y0} vs {y1} (%)", barmode="group", **lay)
    figs.append(g)

    g = go.Figure()
    for col, nm, colr in [("avg_weekly_txn_mn", "Transactions", C["primary"]),
                          ("avg_weekly_value_bn_sar", "Value", C["accent"]), ("avg_ticket_sar", "Avg ticket", C["neg"])]:
        g.add_scatter(x=ny.year.astype(str), y=100 * ny[col] / ny[col].iloc[0], name=nm, mode="lines+markers",
                      line=dict(color=colr, width=2.5))
    g.update_layout(title=f"Index ({ny.year.iloc[0]} = 100): more, smaller card payments", **lay)
    figs.append(g)

    g = go.Figure()
    g.add_bar(x=r.year.astype(str), y=r.peak_week_index - 100, name="Peak week (Ramadan to Eid)", marker_color=C["primary"])
    g.add_bar(x=r.year.astype(str), y=r.post_eid_week_index - 100, name="Week after Eid", marker_color=C["neg"])
    g.update_layout(title="Ramadan/Eid swing vs 4 weeks before Ramadan (%)", barmode="group", **lay)
    figs.append(g)
    return figs

"""Run the named KPI queries in sql/03_kpis.sql and assemble kpis.json."""
from __future__ import annotations

import json
import re

import duckdb
import pandas as pd

from .config import PROCESSED, SQL_DIR


def load_named_queries() -> dict[str, str]:
    text = (SQL_DIR / "03_kpis.sql").read_text()
    parts = re.split(r"^-- name: (\w+)\s*$", text, flags=re.M)
    return {parts[i]: parts[i + 1].strip().rstrip(";") for i in range(1, len(parts), 2)}


def run_kpis(con: duckdb.DuckDBPyConnection) -> tuple[dict[str, pd.DataFrame], dict]:
    frames = {name: con.execute(sql).df() for name, sql in load_named_queries().items()}
    for name, df in frames.items():
        df.to_csv(PROCESSED / f"kpi_{name}.csv", index=False)

    ny = frames["national_yearly"].set_index("year")
    last_full = int(ny.index.max())
    first_full = int(ny.index.min())
    ytd = frames["latest_ytd"].iloc[0]
    sec = frames["sector_mix"]
    city = frames["city_share"]
    ram = frames["ramadan_effect"]
    lift = frames["ramadan_sector_lift"]
    nw = frames["national_weekly"]

    def cs(y, c):
        r = city[(city.year == y) & (city.city_name == c)]
        return float(r.share_pct.iloc[0])

    def cg(c):
        # per-week normalised so a 53-week year cannot inflate growth
        a = city[(city.year == first_full) & (city.city_name == c)].iloc[0]
        b = city[(city.year == last_full) & (city.city_name == c)].iloc[0]
        return float(100 * ((b.value_bn_sar / b.weeks) / (a.value_bn_sar / a.weeks) - 1))

    peak = nw.loc[nw.value_bn_sar.idxmax()]
    k = {
        "coverage": {
            "first_week": str(nw.week_start.min().date()),
            "last_week": str(nw.week_start.max().date()),
            "weeks": int(len(nw)),
            "weeks_from_dataset_b": int((nw.source == "B").sum()),
            "full_years": [int(y) for y in ny.index],
        },
        "yearly": {str(int(yr)): {c: (None if pd.isna(v) else float(v)) for c, v in row.items()}
                   for yr, row in ny.iterrows()},
        "last_full_year": last_full,
        "first_full_year": first_full,
        "headline": {
            "value_bn_sar": float(ny.loc[last_full, "value_bn_sar"]),
            "weeks": int(ny.loc[last_full, "weeks"]),
            "avg_weekly_value_bn_sar": float(ny.loc[last_full, "avg_weekly_value_bn_sar"]),
            "value_yoy_pct": float(ny.loc[last_full, "value_yoy_pct"]),
            "txn_bn": float(ny.loc[last_full, "txn_bn"]),
            "txn_yoy_pct": float(ny.loc[last_full, "txn_yoy_pct"]),
            "avg_ticket_sar": float(ny.loc[last_full, "avg_ticket_sar"]),
            "avg_ticket_first_full_year_sar": float(ny.loc[first_full, "avg_ticket_sar"]),
            "avg_ticket_change_pct": float(
                100 * (ny.loc[last_full, "avg_ticket_sar"] / ny.loc[first_full, "avg_ticket_sar"] - 1)
            ),
            "value_growth_first_to_last_pct": float(
                100 * (ny.loc[last_full, "avg_weekly_value_bn_sar"] / ny.loc[first_full, "avg_weekly_value_bn_sar"] - 1)
            ),
            "txn_growth_first_to_last_pct": float(
                100 * (ny.loc[last_full, "avg_weekly_txn_mn"] / ny.loc[first_full, "avg_weekly_txn_mn"] - 1)
            ),
        },
        "latest_ytd": {
            "from": str(pd.Timestamp(ytd.cur_from).date()),
            "to": str(pd.Timestamp(ytd.cur_to).date()),
            "weeks": int(ytd.weeks),
            "value_bn_sar": float(ytd.cur_value_bn_sar),
            "value_yoy_pct": float(ytd.value_yoy_pct),
            "txn_yoy_pct": float(ytd.txn_yoy_pct),
        },
        "peak_week": {"week_start": str(peak.week_start.date()), "value_bn_sar": float(peak.value_bn_sar)},
        "sectors_2024": {
            "top3": sec.head(3)[["sector_name", "share_2024_pct"]].to_dict("records"),
            "top_named": sec[sec.sector_name != "Other"].head(2)[["sector_name", "share_2024_pct", "avg_ticket_sar_2024"]]
            .to_dict("records"),
            "top3_share_pct": float(sec.head(3).share_2024_pct.sum()),
            "fastest_cagr": sec.sort_values("cagr_2021_2024_pct", ascending=False)
            .head(3)[["sector_name", "cagr_2021_2024_pct"]]
            .to_dict("records"),
            "slowest_cagr": sec.sort_values("cagr_2021_2024_pct")
            .head(2)[["sector_name", "cagr_2021_2024_pct"]]
            .to_dict("records"),
        },
        "cities": {
            "riyadh_share_first": cs(first_full, "Riyadh"),
            "riyadh_share_last": cs(last_full, "Riyadh"),
            "jeddah_share_first": cs(first_full, "Jeddah"),
            "jeddah_share_last": cs(last_full, "Jeddah"),
            "makkah_share_last": cs(last_full, "Makkah"),
            "madinah_share_last": cs(last_full, "Madinah"),
            "jeddah_value_bn_sar_last": float(
                city[(city.year == last_full) & (city.city_name == "Jeddah")].value_bn_sar.iloc[0]
            ),
            "named_cities_share_last": float(city[city.year == last_full].share_pct.sum()),
            "jeddah_value_growth_pct": cg("Jeddah"),
            "riyadh_value_growth_pct": cg("Riyadh"),
            "makkah_value_growth_pct": cg("Makkah"),
            "madinah_value_growth_pct": cg("Madinah"),
            "national_value_growth_pct": float(
                100 * (ny.loc[last_full, "avg_weekly_value_bn_sar"] / ny.loc[first_full, "avg_weekly_value_bn_sar"] - 1)
            ),
        },
        "ramadan": {
            "years": [int(y) for y in ram.year],
            "peak_index_min": float(ram.peak_week_index.min()),
            "peak_index_max": float(ram.peak_week_index.max()),
            "peak_index_median": float(ram.peak_week_index.median()),
            "post_eid_index_min": float(ram.post_eid_week_index.min()),
            "post_eid_index_max": float(ram.post_eid_week_index.max()),
            "peak_weeks": [str(pd.Timestamp(w).date()) for w in ram.peak_week_start],
            "ramadan_avg_index_min": float(ram.ramadan_avg_index.min()),
            "ramadan_avg_index_max": float(ram.ramadan_avg_index.max()),
            "top_sector_lift": lift.head(3).to_dict("records"),
            "bottom_sector_lift": lift.tail(2).to_dict("records"),
        },
    }
    (PROCESSED / "kpis.json").write_text(json.dumps(k, indent=2, default=str))
    print(f"[kpis] wrote kpis.json ({len(frames)} KPI tables)")
    return frames, k

"""Run the DuckDB SQL layers and build the Hijri-aware date dimension."""
from __future__ import annotations

from datetime import date, timedelta

import duckdb
import pandas as pd
from hijridate import Gregorian

from .config import DATASETS, DB_PATH, PROCESSED, RAW, SQL_DIR


def build_dim_date(start: date, end: date) -> pd.DataFrame:
    """One row per Sunday week start. Ramadan / Eid flags come from the Umm al-Qura
    calendar (hijridate), not from hand-typed dates."""
    rows = []
    wk = start
    while wk <= end:
        days = [wk + timedelta(days=i) for i in range(7)]
        hij = [Gregorian(d.year, d.month, d.day).to_hijri() for d in days]
        ramadan_days = sum(h.month == 9 for h in hij)
        rows.append(
            {
                "week_start": wk,
                "week_end": wk + timedelta(days=6),
                "year": wk.year,
                "quarter": (wk.month - 1) // 3 + 1,
                "month": wk.month,
                "month_name": wk.strftime("%b"),
                "iso_week": wk.isocalendar()[1],
                "hijri_year": hij[0].year,
                "hijri_month": hij[0].month,
                "ramadan_days_in_week": ramadan_days,
                "is_ramadan_week": ramadan_days >= 4,
                "is_eid_fitr_week": any(h.month == 10 and h.day == 1 for h in hij),
                "is_eid_adha_week": any(h.month == 12 and h.day == 10 for h in hij),
                "is_national_day_week": any(d.month == 9 and d.day == 23 for d in days),
                "is_founding_day_week": any(d.month == 2 and d.day == 22 for d in days),
            }
        )
        wk += timedelta(days=7)
    return pd.DataFrame(rows)


def _run_sql_file(con: duckdb.DuckDBPyConnection, name: str) -> None:
    con.execute((SQL_DIR / name).read_text())


def build_star_schema() -> duckdb.DuckDBPyConnection:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()
    con = duckdb.connect(str(DB_PATH))
    con.execute("SET VARIABLE raw_a = ?", [str(RAW / f"{DATASETS['pos_a']['dataset_id']}.csv")])
    con.execute("SET VARIABLE raw_b = ?", [str(RAW / f"{DATASETS['pos_b']['dataset_id']}.csv")])
    print("[transform] 01_staging.sql")
    _run_sql_file(con, "01_staging.sql")

    lo, hi = con.execute("SELECT min(week_start), max(week_start) FROM stg_pos").fetchone()
    dim_date = build_dim_date(lo, hi)
    con.register("dim_date_df", dim_date)
    con.execute("CREATE OR REPLACE TABLE dim_date AS SELECT * FROM dim_date_df")
    con.unregister("dim_date_df")

    print("[transform] 02_star_schema.sql")
    _run_sql_file(con, "02_star_schema.sql")

    # Power BI-ready CSV exports
    for t in ["dim_date", "dim_city", "dim_sector", "fact_national_weekly", "fact_city_weekly", "fact_sector_weekly"]:
        out = PROCESSED / f"{t}.csv"
        con.execute(f"COPY {t} TO '{out}' (HEADER, DELIMITER ',')")
        n = con.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
        print(f"[transform] {t:<22} {n:>6} rows -> {out.relative_to(PROCESSED.parent.parent)}")
    return con

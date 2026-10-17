"""Data-validation tests. Run after `python run.py` (the Makefile does this for you)."""
import json
import math
import sys
from pathlib import Path

import duckdb
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from pos_dashboard.config import DATASETS, DB_PATH, PROCESSED, RAW, REPORTS  # noqa: E402


@pytest.fixture(scope="session")
def con():
    if not DB_PATH.exists():
        pytest.skip("run `python run.py` first")
    c = duckdb.connect(str(DB_PATH), read_only=True)
    yield c
    c.close()


def q(con, sql):
    return con.execute(sql).fetchone()


# ---- raw layer ---------------------------------------------------------------
@pytest.mark.parametrize("key", list(DATASETS))
def test_raw_files_present_and_match_manifest(key):
    import hashlib
    manifest = json.loads((RAW / "manifest.json").read_text())
    f = RAW / manifest[key]["file"]
    assert f.exists()
    assert hashlib.sha256(f.read_bytes()).hexdigest() == manifest[key]["sha256"]
    df = pd.read_csv(f, nrows=5)
    assert {"starting_date", "number_value_change_transactions", "sectors", "city", "value"} <= set(df.columns)


def test_all_indicators_mapped(con):
    assert q(con, "SELECT count(*) FROM stg_pos_long WHERE metric IS NULL")[0] == 0


# ---- star schema integrity ---------------------------------------------------
@pytest.mark.parametrize("table,keys", [
    ("fact_national_weekly", "week_start"),
    ("fact_city_weekly", "week_start, city_key"),
    ("fact_sector_weekly", "week_start, sector_key"),
    ("dim_date", "week_start"),
])
def test_no_duplicate_keys(con, table, keys):
    total = q(con, f"SELECT count(*) FROM {table}")[0]
    distinct = q(con, f"SELECT count(*) FROM (SELECT DISTINCT {keys} FROM {table})")[0]
    assert total == distinct > 0


def test_weekly_series_has_no_gaps(con):
    gaps = q(con, """SELECT count(*) FROM (
        SELECT week_start - lag(week_start) OVER (ORDER BY week_start) AS d FROM fact_national_weekly)
        WHERE d IS NOT NULL AND d <> 7  -- DATE - DATE = days""")[0]
    assert gaps == 0


def test_all_weeks_start_on_sunday(con):
    assert q(con, "SELECT count(*) FROM fact_national_weekly WHERE dayofweek(week_start) <> 0")[0] == 0


def test_values_positive_and_not_null(con):
    for t in ["fact_national_weekly", "fact_city_weekly", "fact_sector_weekly"]:
        bad = q(con, f"SELECT count(*) FROM {t} WHERE txn_value_k_sar IS NULL OR txn_value_k_sar <= 0 "
                     f"OR txn_count_k IS NULL OR txn_count_k <= 0")[0]
        assert bad == 0, t


def test_foreign_keys_resolve(con):
    assert q(con, "SELECT count(*) FROM fact_city_weekly f ANTI JOIN dim_city USING (city_key)")[0] == 0
    assert q(con, "SELECT count(*) FROM fact_sector_weekly f ANTI JOIN dim_sector USING (sector_key)")[0] == 0
    assert q(con, "SELECT count(*) FROM fact_national_weekly f ANTI JOIN dim_date USING (week_start)")[0] == 0


# ---- reconciliation with the publisher --------------------------------------
def test_sectors_sum_to_national_total(con):
    worst = q(con, """SELECT max(abs(s.v / n.txn_value_k_sar - 1)) FROM
        (SELECT week_start, sum(txn_value_k_sar) v FROM fact_sector_weekly GROUP BY 1) s
        JOIN fact_national_weekly n USING (week_start)""")[0]
    assert worst < 1e-4  # within 0.01% (rounding in the source)


def test_cities_never_exceed_national_total(con):
    assert q(con, """SELECT count(*) FROM
        (SELECT week_start, sum(txn_value_k_sar) v FROM fact_city_weekly GROUP BY 1) c
        JOIN fact_national_weekly n USING (week_start) WHERE c.v > n.txn_value_k_sar * 1.0001""")[0] == 0


def test_recomputed_wow_matches_published_change(con):
    """Our week-on-week % from levels must reproduce SAMA's own published change % (dataset A, national)."""
    worst = q(con, """WITH t AS (
        SELECT week_start, txn_value_k_sar, pub_value_wow_pct,
               100 * (txn_value_k_sar / lag(txn_value_k_sar) OVER (ORDER BY week_start) - 1) AS calc
        FROM stg_pos WHERE source = 'A' AND sector = 'All sectors' AND city = 'KSA total')
        SELECT max(abs(calc - pub_value_wow_pct)) FROM t WHERE calc IS NOT NULL AND pub_value_wow_pct IS NOT NULL""")[0]
    assert worst < 0.01  # percentage points


def test_releases_agree_in_overlap_weeks(con):
    """National and city totals must match between the old (A) and new (B) SAMA releases before stitching."""
    n, worst = q(con, """SELECT count(*), max(abs(b.txn_value_k_sar / a.txn_value_k_sar - 1)) FROM stg_pos a
        JOIN stg_pos b ON a.week_start = b.week_start AND a.city = b.city AND a.sector = b.sector
        WHERE a.source = 'A' AND b.source = 'B' AND a.sector = 'All sectors'
          AND a.city IN (SELECT city_name FROM dim_city UNION SELECT 'KSA total')""")
    assert n >= 11
    assert worst < 1e-4


def test_dim_date_ramadan_flags_plausible(con):
    # Every Hijri year in range has ~4 Ramadan weeks and exactly one Eid al-Fitr week
    rows = con.execute("""SELECT hijri_year, sum(is_ramadan_week::INT) r, sum(is_eid_fitr_week::INT) e
        FROM dim_date GROUP BY 1 HAVING min(week_start) > DATE '2020-06-01' AND max(week_start) < DATE '2026-01-01'
    """).fetchall()
    assert rows
    for hy, r, e in rows:
        assert 3 <= r <= 5 and e == 1, (hy, r, e)


# ---- outputs -----------------------------------------------------------------
def _finite(obj):
    if isinstance(obj, dict):
        return all(_finite(v) for v in obj.values())
    if isinstance(obj, list):
        return all(_finite(v) for v in obj)
    if isinstance(obj, float):
        return math.isfinite(obj)
    return True


def test_kpis_json_complete_and_finite():
    k = json.loads((PROCESSED / "kpis.json").read_text())
    for key in ["coverage", "headline", "latest_ytd", "sectors_2024", "cities", "ramadan"]:
        assert key in k
    hl = {kk: v for kk, v in k["headline"].items()}
    assert _finite(hl) and _finite(k["cities"]) and _finite(k["ramadan"])
    assert k["coverage"]["weeks"] > 300


@pytest.mark.parametrize("name,min_bytes", [
    ("dashboard.png", 100_000), ("dashboard_and_summary.pdf", 30_000),
    ("dashboard.html", 100_000), ("executive_summary.md", 1_500),
])
def test_report_outputs_exist(name, min_bytes):
    p = REPORTS / name
    assert p.exists() and p.stat().st_size > min_bytes


def test_summary_numbers_trace_to_kpis():
    """Spot-check that headline numbers in the summary are the ones in kpis.json."""
    k = json.loads((PROCESSED / "kpis.json").read_text())
    md = (REPORTS / "executive_summary.md").read_text()
    assert f"SAR {k['headline']['avg_ticket_sar']:.1f}" in md
    assert f"{k['cities']['riyadh_share_last']:.1f}%" in md
    assert f"{k['headline']['value_yoy_pct']:+.1f}%" in md


def test_readme_findings_match_kpis():
    """The README findings table is hand-written prose: fail if the data no longer supports it."""
    k = json.loads((PROCESSED / "kpis.json").read_text())
    readme = (ROOT / "README.md").read_text()
    h, c = k["headline"], k["cities"]
    expected = [
        f"SAR {h['avg_ticket_sar']:.1f}",
        f"SAR {h['avg_ticket_first_full_year_sar']:.1f}",
        f"{h['value_growth_first_to_last_pct']:+.1f}%",
        f"{h['value_yoy_pct']:+.1f}%",
        f"{k['latest_ytd']['value_yoy_pct']:+.1f}%",
        f"{h['txn_growth_first_to_last_pct']:+.1f}%",
        f"{c['riyadh_share_last']:.1f}%",
        f"{c['jeddah_share_last']:.1f}%",
        f"{c['jeddah_value_growth_pct']:+.1f}%",
    ]
    missing = [e for e in expected if e not in readme]
    assert not missing, f"README out of date: {missing}"

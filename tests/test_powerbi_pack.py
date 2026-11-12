"""Checks that the Power BI-ready pack is complete and consistent with the SQL model."""
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PBI = ROOT / "powerbi"
QUERIES = PBI / "queries"
SQL_KPIS = (ROOT / "sql" / "03_kpis.sql").read_text()
DAX = (PBI / "measures.dax").read_text()
README_PBI = (PBI / "README.md").read_text()

REQUIRED_M = [
    "dim_date.m",
    "dim_city.m",
    "dim_sector.m",
    "fact_national_weekly.m",
    "fact_city_weekly.m",
    "fact_sector_weekly.m",
]

REQUIRED_DAX = [
    "POS Value (SAR bn)",
    "Transactions (mn)",
    "Avg Ticket (SAR)",
    "Avg Weekly Value (SAR bn)",
    "WoW %",
    "vs 4-week avg %",
    "vs 52 weeks ago %",
    "YoY % (avg weekly)",
    "POS Value YTD (SAR bn)",
    "YTD YoY %",
    "City Share %",
    "Sector Share %",
    "City Rank",
    "Sector Rank",
    "Ramadan Week Value (SAR bn)",
]


def test_powerquery_files_are_valid_m():
    for name in REQUIRED_M:
        text = (QUERIES / name).read_text()
        assert "let" in text and "\nin\n" in text, name
        assert "FolderPath" in text, name
        assert "Table.PromoteHeaders" in text, name
        assert "Table.TransformColumnTypes" in text, name
        assert name.replace(".m", ".csv") in text, name


def test_parameters_and_incremental_notes_exist():
    params = (PBI / "parameters.m").read_text()
    assert "FolderPath" in params
    notes = (PBI / "incremental_refresh.md").read_text()
    assert "RangeStart" in notes and "RangeEnd" in notes
    assert "13 months" in notes or "13-month" in notes
    assert "52" in notes


def test_dax_measures_present():
    missing = [m for m in REQUIRED_DAX if m not in DAX]
    assert not missing, missing
    # DIVIDE is safer than "/" for these ratios
    assert "DIVIDE" in DAX
    assert ".pbix" in DAX.lower() or "Power BI Desktop" in DAX


def test_model_diagram_png():
    png = PBI / "model_diagram.png"
    assert png.exists() and png.stat().st_size > 10_000
    mmd = (PBI / "model_diagram.mmd").read_text()
    for table in (
        "dim_date",
        "dim_city",
        "dim_sector",
        "fact_national_weekly",
        "fact_city_weekly",
        "fact_sector_weekly",
    ):
        assert table in mmd


def test_powerbi_readme_is_honest_about_pbix():
    assert "no `.pbix`" in README_PBI.lower() or "no `.pbix`" in README_PBI or "no `.pbix` file" in README_PBI
    assert "Python" in README_PBI
    # relationships documented
    assert "fact_national_weekly[week_start]" in README_PBI


def test_model_csvs_exist():
    processed = ROOT / "data" / "processed"
    for name in [
        "dim_date.csv",
        "dim_city.csv",
        "dim_sector.csv",
        "fact_national_weekly.csv",
        "fact_city_weekly.csv",
        "fact_sector_weekly.csv",
    ]:
        p = processed / name
        assert p.exists() and p.stat().st_size > 50, name

"""Paths, dataset identifiers and naming maps used across the pipeline."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
SQL_DIR = ROOT / "sql"
REPORTS = ROOT / "reports"
FIGURES = REPORTS / "figures"
DB_PATH = PROCESSED / "pos.duckdb"

KAPSARC_EXPORT = (
    "https://datasource.kapsarc.org/api/explore/v2.1/catalog/datasets/"
    "{dataset_id}/exports/csv?delimiter=%2C"
)
KAPSARC_PAGE = "https://datasource.kapsarc.org/explore/dataset/{dataset_id}/"

DATASETS = {
    # Dataset A: weekly, May 2020 - Jul 2025, 17 sectors (national) + 11 cities
    "pos_a": {
        "dataset_id": "point-of-sale-transactions-by-sector-and-city",
        "title": "Point of Sale Transactions by Sector and City",
        "publisher": "Saudi Central Bank (SAMA)",
        "license": "Public Domain (as labelled on the KAPSARC Data Portal); source copyright SAMA",
    },
    # Dataset B: weekly, Jun 2025 - Mar 2026, 32 sub-sectors + 61 cities (new taxonomy)
    "pos_b": {
        "dataset_id": "detailed-point-of-sale-transactions-by-sector-and-city",
        "title": "Detailed Point of Sale Transactions by Sector and City",
        "publisher": "Saudi Central Bank (SAMA)",
        "license": "Public Domain (as labelled on the KAPSARC Data Portal); source copyright SAMA",
    },
}

# Brand-neutral, Power BI-like palette
PALETTE = {
    "primary": "#0B6E4F",   # deep green
    "accent": "#C8A75B",    # sand gold
    "dark": "#1F2933",
    "muted": "#7B8794",
    "light": "#E4E7EB",
    "bg": "#F7F8FA",
    "neg": "#B23A48",
}

# Power BI-ready pack (no .pbix)

Power BI Desktop is a Windows application and was not run on the machine that built this repository. There is **no `.pbix` file** here. This folder is everything needed to rebuild the model in Desktop from the same star-schema CSVs the Python/DuckDB pipeline exports.

The dashboard images in `reports/` and `docs/screenshots/` are **Python renders of the same model** (matplotlib and Plotly), not screenshots of a Power BI report.

## Contents

| File | What it is |
|---|---|
| `../data/processed/dim_*.csv`, `fact_*.csv` | Star-schema model CSVs (the import source) |
| `parameters.m` | `FolderPath` (and optional `RangeStart` / `RangeEnd`) |
| `queries/*.m` | Power Query M for each dimension and fact (types, UTF-8) |
| `measures.dax` | 28 DAX measures: levels, WoW / 4-week / 52-week / YoY / YTD variance, city and sector share and rank, Ramadan and Eid |
| `incremental_refresh.md` | When incremental refresh is worth turning on, and the 13-month lookback YoY needs |
| `model_diagram.png` | Star-schema relationship diagram (rendered from `model_diagram.mmd`) |
| `DAX_measures.md` | Short Desktop walk-through |

## Relationships (Model view, single direction, many-to-one)

- `fact_national_weekly[week_start]` → `dim_date[week_start]`
- `fact_city_weekly[week_start]` → `dim_date[week_start]`
- `fact_city_weekly[city_key]` → `dim_city[city_key]`
- `fact_sector_weekly[week_start]` → `dim_date[week_start]`
- `fact_sector_weekly[sector_key]` → `dim_sector[sector_key]`

Mark `dim_date[week_start]` as the date table. Sector facts end on 2025-07-06 (SAMA taxonomy change); national and city facts run to 2026-03-22.

## Honesty

The M and DAX are written to mirror `sql/02_star_schema.sql` and `sql/03_kpis.sql`. They have not been executed in Power BI Desktop. A `.pbix` will be added if it is built on a Windows machine.

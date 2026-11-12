# Rebuilding the model in Power BI Desktop

A `.pbix` is not included: Power BI Desktop runs only on Windows, and it was not run for this repository. The dashboard PNGs and PDF in `reports/` are Python renders of the same star schema, not Power BI screenshots.

**Full pack:** see [`README.md`](README.md) in this folder. Paste [`queries/*.m`](queries/) into Advanced Editor (after creating the `FolderPath` parameter in [`parameters.m`](parameters.m)), set the relationships below, mark `dim_date` as the date table, and add the measures in [`measures.dax`](measures.dax) to a `_Measures` table. Incremental-refresh notes are in [`incremental_refresh.md`](incremental_refresh.md).

## Relationships (single direction, many-to-one)

- `fact_national_weekly[week_start]` → `dim_date[week_start]`
- `fact_city_weekly[week_start]` → `dim_date[week_start]`; `fact_city_weekly[city_key]` → `dim_city[city_key]`
- `fact_sector_weekly[week_start]` → `dim_date[week_start]`; `fact_sector_weekly[sector_key]` → `dim_sector[sector_key]`

## Measure groups in `measures.dax`

1. National levels: POS value, transactions, average ticket, week count, average weekly value.
2. Period variance: week-on-week, vs 4-week average, vs 52 weeks ago (level and %), year-on-year on average weekly value (fairer when a year has 53 weeks).
3. Year-to-date: YTD, prior-year YTD, YTD YoY %.
4. City and sector: value, share, rank, city vs 52 weeks ago.
5. Seasonality: Ramadan, Eid al-Fitr and Eid al-Adha week values, using Hijri flags on `dim_date`.

Suggested pages: (1) Overview with KPI cards, weekly trend and variance vs 52 weeks ago; (2) Sectors; (3) Cities; (4) Seasonality, using `dim_date` Hijri flags as slicers.

The measures mirror `sql/03_kpis.sql`. They are drafts and have not been tested in Power BI Desktop yet.

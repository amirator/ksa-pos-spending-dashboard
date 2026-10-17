# Rebuilding the model in Power BI Desktop

1. **Get Data > Text/CSV** and load every file in `data/processed/` whose name starts with `dim_` or `fact_`.
2. **Model view** relationships (single direction, many-to-one):
   - `fact_national_weekly[week_start]` → `dim_date[week_start]`
   - `fact_city_weekly[week_start]` → `dim_date[week_start]`; `fact_city_weekly[city_key]` → `dim_city[city_key]`
   - `fact_sector_weekly[week_start]` → `dim_date[week_start]`; `fact_sector_weekly[sector_key]` → `dim_sector[sector_key]`
3. Mark `dim_date` as the date table (column `week_start`).
4. Add the measures below to a `_Measures` table.

```DAX
POS Value (SAR bn)      = DIVIDE ( SUM ( fact_national_weekly[txn_value_k_sar] ), 1e6 )
Transactions (mn)       = DIVIDE ( SUM ( fact_national_weekly[txn_count_k] ), 1e3 )
Avg Ticket (SAR)        = DIVIDE ( SUM ( fact_national_weekly[txn_value_k_sar] ), SUM ( fact_national_weekly[txn_count_k] ) )
Weeks                   = DISTINCTCOUNT ( fact_national_weekly[week_start] )
Avg Weekly Value (SAR bn) = DIVIDE ( [POS Value (SAR bn)], [Weeks] )

Avg Weekly Value PY =
VAR y = SELECTEDVALUE ( dim_date[year] )
RETURN CALCULATE ( [Avg Weekly Value (SAR bn)], REMOVEFILTERS ( dim_date ), dim_date[year] = y - 1 )

YoY % (avg weekly)      = DIVIDE ( [Avg Weekly Value (SAR bn)] - [Avg Weekly Value PY], [Avg Weekly Value PY] )

City Value (SAR bn)     = DIVIDE ( SUM ( fact_city_weekly[txn_value_k_sar] ), 1e6 )
City Share %            = DIVIDE ( [City Value (SAR bn)], [POS Value (SAR bn)] )

Sector Value (SAR bn)   = DIVIDE ( SUM ( fact_sector_weekly[txn_value_k_sar] ), 1e6 )
Sector Share %          = DIVIDE ( [Sector Value (SAR bn)], CALCULATE ( [Sector Value (SAR bn)], ALL ( dim_sector ) ) )

Ramadan Week Value (SAR bn) = CALCULATE ( [POS Value (SAR bn)], dim_date[is_ramadan_week] = TRUE () )
```

Suggested pages: (1) Overview with KPI cards and a weekly trend; (2) Sectors; (3) Cities; (4) Seasonality, using `dim_date` Hijri flags as slicers. These measures mirror the logic in `sql/03_kpis.sql`. They are drafts and have not been tested in Power BI Desktop yet. A `.pbix` file is not included because Power BI Desktop runs only on Windows.

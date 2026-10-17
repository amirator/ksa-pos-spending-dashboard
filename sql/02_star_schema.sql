-- 02_star_schema.sql
-- Build a Power BI-ready star schema.
--   fact_national_weekly : KSA total, A (May 2020 - Jul 2025) stitched with B for later weeks
--   fact_city_weekly     : 10 named cities, all sectors, same stitching rule
--   fact_sector_weekly   : 17 sectors, national, A only (B changed the sector taxonomy)
--   dim_city, dim_sector ; dim_date is created in Python (Hijri calendar flags) before this runs.

CREATE OR REPLACE TABLE stitch_cutover AS
SELECT max(week_start) AS last_week_a FROM stg_pos WHERE source = 'A';

CREATE OR REPLACE TABLE fact_national_weekly AS
SELECT s.week_start, s.source, s.txn_count_k, s.txn_value_k_sar
FROM stg_pos s, stitch_cutover c
WHERE s.sector = 'All sectors' AND s.city = 'KSA total'
  AND (s.source = 'A' OR (s.source = 'B' AND s.week_start > c.last_week_a))
ORDER BY week_start;

CREATE OR REPLACE TABLE dim_city AS
SELECT * FROM (VALUES
    (1,  'Riyadh',   'Riyadh Region'),
    (2,  'Jeddah',   'Makkah Region'),
    (3,  'Makkah',   'Makkah Region'),
    (4,  'Madinah',  'Madinah Region'),
    (5,  'Dammam',   'Eastern Province'),
    (6,  'Khobar',   'Eastern Province'),
    (7,  'Buraidah', 'Qassim Region'),
    (8,  'Abha',     'Asir Region'),
    (9,  'Tabouk',   'Tabuk Region'),
    (10, 'Hail',     'Hail Region')
) AS t(city_key, city_name, admin_region);

CREATE OR REPLACE TABLE fact_city_weekly AS
SELECT s.week_start, d.city_key, s.source, s.txn_count_k, s.txn_value_k_sar
FROM stg_pos s
JOIN dim_city d ON d.city_name = s.city
CROSS JOIN stitch_cutover c
WHERE s.sector = 'All sectors'
  AND (s.source = 'A' OR (s.source = 'B' AND s.week_start > c.last_week_a))
ORDER BY week_start, city_key;

CREATE OR REPLACE TABLE dim_sector AS
SELECT row_number() OVER (ORDER BY sector) AS sector_key, sector AS sector_name
FROM (SELECT DISTINCT sector FROM stg_pos WHERE source = 'A' AND sector <> 'All sectors');

CREATE OR REPLACE TABLE fact_sector_weekly AS
SELECT s.week_start, d.sector_key, s.txn_count_k, s.txn_value_k_sar
FROM stg_pos s
JOIN dim_sector d ON d.sector_name = s.sector
WHERE s.source = 'A' AND s.city = 'KSA total'
ORDER BY week_start, sector_key;

-- 01_staging.sql
-- Load the two raw SAMA POS extracts, standardise names, units and week dates,
-- and pivot from long (one row per indicator) to wide (one row per week x sector x city).
-- Paths are injected by run.py as DuckDB variables: raw_a, raw_b.

CREATE OR REPLACE TABLE stg_pos_long AS
WITH raw AS (
    SELECT 'A' AS source, * FROM read_csv(getvariable('raw_a'), header = true, delim = ',')
    UNION ALL BY NAME
    SELECT 'B' AS source, * FROM read_csv(getvariable('raw_b'), header = true, delim = ',')
),
typed AS (
    SELECT
        source,
        CAST(starting_date AS DATE)                         AS raw_date,
        TRIM(number_value_change_transactions)              AS indicator,
        TRIM(sectors)                                       AS sector_raw,
        TRIM(city)                                          AS city_raw,
        CAST(value AS DOUBLE)                               AS value
    FROM raw
)
SELECT
    source,
    raw_date,
    -- SAMA weeks start on Sunday. One week in 2020 is stamped Saturday 2020-06-20;
    -- snap every date to the nearest Sunday (DuckDB dayofweek: Sunday = 0).
    CASE WHEN dayofweek(raw_date) <= 3
         THEN raw_date - CAST(dayofweek(raw_date) AS INTEGER)
         ELSE raw_date + CAST(7 - dayofweek(raw_date) AS INTEGER)
    END                                                     AS week_start,
    CASE indicator
        WHEN 'Number of Transactions (In Thousand)'     THEN 'txn_count_k'
        WHEN 'Value of Transactions (In Thousand SAR)'  THEN 'txn_value_k_sar'
        WHEN 'Number of Transactions Change %'          THEN 'pub_count_wow_pct'
        WHEN 'Value of Transactions Change %'           THEN 'pub_value_wow_pct'
    END                                                     AS metric,
    -- National totals: A uses 'Total', B uses '20.Total'
    CASE WHEN sector_raw IN ('Total', '20.Total') THEN 'All sectors' ELSE sector_raw END AS sector,
    -- Harmonise B's city spellings to A's 10 named cities; everything else keeps its B name
    CASE
        WHEN city_raw = 'Total'                         THEN 'KSA total'
        WHEN upper(city_raw) = 'RIYADH'                 THEN 'Riyadh'
        WHEN upper(city_raw) = 'JEDDAH'                 THEN 'Jeddah'
        WHEN upper(city_raw) = 'MAKKAH'                 THEN 'Makkah'
        WHEN upper(city_raw) = 'DAMMAM'                 THEN 'Dammam'
        WHEN upper(city_raw) = 'ABHA'                   THEN 'Abha'
        WHEN upper(city_raw) = 'BURAIDAH'               THEN 'Buraidah'
        WHEN upper(city_raw) = 'TABOUK'                 THEN 'Tabouk'
        WHEN city_raw IN ('MADINA', 'Al-Madinah')       THEN 'Madinah'
        WHEN city_raw IN ('KHOBAR', 'Al-Khubar')        THEN 'Khobar'
        WHEN city_raw IN ('HAIL', 'Hayel')              THEN 'Hail'
        WHEN city_raw = 'OTHER'                         THEN 'Other (A only)'
        ELSE city_raw
    END                                                     AS city,
    value
FROM typed;

CREATE OR REPLACE TABLE stg_pos AS
PIVOT stg_pos_long
ON metric IN ('txn_count_k', 'txn_value_k_sar', 'pub_count_wow_pct', 'pub_value_wow_pct')
USING first(value)
GROUP BY source, week_start, sector, city;

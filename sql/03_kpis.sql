-- 03_kpis.sql
-- KPI queries. Each block starts with "-- name: <key>" and is run by kpis.py.
-- Units: txn_value_k_sar = SAR thousands; txn_count_k = transactions in thousands.
-- Years are compared on AVERAGE WEEKLY values because some calendar years hold 53 week-starts.

-- name: national_weekly
-- Weekly series with 4-week rolling average, week-on-week and 52-week-ago comparison
SELECT
    f.week_start,
    f.source,
    f.txn_value_k_sar / 1e6                                         AS value_bn_sar,
    f.txn_count_k / 1e3                                             AS txn_mn,
    f.txn_value_k_sar / f.txn_count_k                               AS avg_ticket_sar,
    avg(f.txn_value_k_sar / 1e6) OVER (ORDER BY f.week_start ROWS BETWEEN 3 PRECEDING AND CURRENT ROW)
                                                                    AS value_bn_sar_4wk_avg,
    100 * (f.txn_value_k_sar / lag(f.txn_value_k_sar) OVER w - 1)   AS value_wow_pct,
    100 * (f.txn_value_k_sar / lag(f.txn_value_k_sar, 52) OVER w - 1) AS value_vs_52wk_ago_pct,
    d.is_ramadan_week, d.is_eid_fitr_week, d.is_eid_adha_week
FROM fact_national_weekly f
JOIN dim_date d USING (week_start)
WINDOW w AS (ORDER BY f.week_start)
ORDER BY f.week_start;

-- name: national_yearly
-- Full calendar years only (>= 52 week-starts); YoY on average weekly value and count
WITH y AS (
    SELECT
        year(week_start)                     AS year,
        count(*)                             AS weeks,
        sum(txn_value_k_sar) / 1e6           AS value_bn_sar,
        sum(txn_count_k) / 1e6               AS txn_bn,
        avg(txn_value_k_sar) / 1e6           AS avg_weekly_value_bn_sar,
        avg(txn_count_k) / 1e3               AS avg_weekly_txn_mn,
        sum(txn_value_k_sar) / sum(txn_count_k) AS avg_ticket_sar
    FROM fact_national_weekly
    GROUP BY 1
)
SELECT *,
    100 * (avg_weekly_value_bn_sar / lag(avg_weekly_value_bn_sar) OVER (ORDER BY year) - 1) AS value_yoy_pct,
    100 * (avg_weekly_txn_mn       / lag(avg_weekly_txn_mn)       OVER (ORDER BY year) - 1) AS txn_yoy_pct,
    100 * (avg_ticket_sar          / lag(avg_ticket_sar)          OVER (ORDER BY year) - 1) AS ticket_yoy_pct
FROM y
WHERE weeks >= 52
ORDER BY year;

-- name: latest_ytd
-- Latest weeks of the newest year vs the same week numbers 52 weeks earlier
WITH latest AS (SELECT max(week_start) AS max_wk FROM fact_national_weekly),
cur AS (
    SELECT f.* FROM fact_national_weekly f, latest
    WHERE year(f.week_start) = year(latest.max_wk)
),
prev AS (
    SELECT f.* FROM fact_national_weekly f
    WHERE f.week_start IN (SELECT week_start - INTERVAL 364 DAY FROM cur)
)
SELECT
    (SELECT min(week_start) FROM cur)                AS cur_from,
    (SELECT max(week_start) FROM cur)                AS cur_to,
    (SELECT count(*) FROM cur)                       AS weeks,
    (SELECT sum(txn_value_k_sar) FROM cur) / 1e6     AS cur_value_bn_sar,
    (SELECT sum(txn_value_k_sar) FROM prev) / 1e6    AS prev_value_bn_sar,
    100 * ((SELECT sum(txn_value_k_sar) FROM cur) / (SELECT sum(txn_value_k_sar) FROM prev) - 1) AS value_yoy_pct,
    100 * ((SELECT sum(txn_count_k) FROM cur) / (SELECT sum(txn_count_k) FROM prev) - 1)         AS txn_yoy_pct;

-- name: sector_mix
-- Sector share of national POS value in the last full sector year (2024) and growth since 2021
WITH sy AS (
    SELECT d.sector_name, year(f.week_start) AS year,
           avg(f.txn_value_k_sar) / 1e3 AS avg_weekly_value_mn_sar,
           sum(f.txn_value_k_sar) / sum(f.txn_count_k) AS avg_ticket_sar
    FROM fact_sector_weekly f JOIN dim_sector d USING (sector_key)
    WHERE year(f.week_start) IN (2021, 2024)
    GROUP BY ALL
),
w AS (
    PIVOT sy ON year IN (2021, 2024)
    USING first(avg_weekly_value_mn_sar) AS v, first(avg_ticket_sar) AS t
    GROUP BY sector_name
)
SELECT
    sector_name,
    "2024_v"                                                   AS avg_weekly_value_mn_sar_2024,
    100 * "2024_v" / sum("2024_v") OVER ()                     AS share_2024_pct,
    100 * (power("2024_v" / "2021_v", 1.0 / 3) - 1)            AS cagr_2021_2024_pct,
    "2024_t"                                                   AS avg_ticket_sar_2024,
    rank() OVER (ORDER BY "2024_v" DESC)                       AS rank_2024
FROM w
ORDER BY rank_2024;

-- name: city_share
-- Each named city's share of national POS value, first and last full years
WITH yrs AS (
    SELECT year(week_start) AS year FROM fact_national_weekly GROUP BY 1 HAVING count(*) >= 52
),
bounds AS (SELECT min(year) AS y0, max(year) AS y1 FROM yrs),
nat AS (
    SELECT year(week_start) AS year, sum(txn_value_k_sar) AS nat_value
    FROM fact_national_weekly GROUP BY 1
),
cy AS (
    SELECT d.city_name, d.admin_region, year(f.week_start) AS year, sum(f.txn_value_k_sar) AS city_value,
           count(*) AS weeks
    FROM fact_city_weekly f JOIN dim_city d USING (city_key)
    GROUP BY ALL
)
SELECT cy.city_name, cy.admin_region, cy.year, cy.weeks,
       cy.city_value / 1e6                          AS value_bn_sar,
       100 * cy.city_value / nat.nat_value          AS share_pct
FROM cy JOIN nat USING (year), bounds
WHERE cy.year IN (bounds.y0, bounds.y1)
ORDER BY cy.year, share_pct DESC;

-- name: ramadan_effect
-- For each Gregorian year: average Ramadan week, PEAK week in the Ramadan-to-Eid window
-- (pre-Eid shopping lands in the last Ramadan week or the Eid week depending on the weekday of Eid),
-- and the week after the Eid week, each indexed to the average of the 4 weeks before Ramadan (= 100).
WITH s AS (
    SELECT f.week_start, f.txn_value_k_sar AS v, d.is_ramadan_week, d.is_eid_fitr_week,
           d.ramadan_days_in_week,
           row_number() OVER (ORDER BY f.week_start) AS rn
    FROM fact_national_weekly f JOIN dim_date d USING (week_start)
),
marks AS (
    SELECT year(week_start) AS year,
           min(CASE WHEN ramadan_days_in_week > 0 THEN rn END) AS rn_first,
           min(CASE WHEN is_eid_fitr_week THEN rn END)        AS rn_eid
    FROM s GROUP BY 1
),
calc AS (
    SELECT m.year,
        avg(CASE WHEN s.rn BETWEEN m.rn_first - 4 AND m.rn_first - 1 THEN s.v END) AS base,
        avg(CASE WHEN s.is_ramadan_week AND s.rn BETWEEN m.rn_first AND m.rn_eid THEN s.v END) AS ram_avg,
        max(CASE WHEN s.rn BETWEEN m.rn_first AND m.rn_eid THEN s.v END)           AS peak,
        arg_max(CASE WHEN s.rn BETWEEN m.rn_first AND m.rn_eid THEN s.week_start END,
                CASE WHEN s.rn BETWEEN m.rn_first AND m.rn_eid THEN s.v END)       AS peak_week_start,
        max(CASE WHEN s.rn = m.rn_eid + 1 THEN s.v END)                            AS post_eid
    FROM marks m CROSS JOIN s
    WHERE m.rn_first > 4 AND m.rn_eid IS NOT NULL
    GROUP BY m.year
)
SELECT year,
       base / 1e6                  AS baseline_bn_sar,
       100 * ram_avg / base        AS ramadan_avg_index,
       100 * peak / base           AS peak_week_index,
       peak_week_start,
       100 * post_eid / base       AS post_eid_week_index
FROM calc
ORDER BY year;

-- name: ramadan_sector_lift
-- Peak week in the Ramadan-to-Eid window vs each sector's own 4-week pre-Ramadan baseline,
-- averaged over the years covered by dataset A (index, baseline = 100)
WITH s AS (
    SELECT f.week_start, f.sector_key, f.txn_value_k_sar AS v, d.ramadan_days_in_week, d.is_eid_fitr_week,
           dense_rank() OVER (ORDER BY f.week_start) AS rn
    FROM fact_sector_weekly f JOIN dim_date d USING (week_start)
),
marks AS (
    SELECT year(week_start) AS year,
           min(CASE WHEN ramadan_days_in_week > 0 THEN rn END) AS rn_first,
           min(CASE WHEN is_eid_fitr_week THEN rn END)        AS rn_eid
    FROM s GROUP BY 1
),
per_year AS (
    SELECT m.year, s.sector_key,
           avg(CASE WHEN s.rn BETWEEN m.rn_first - 4 AND m.rn_first - 1 THEN s.v END) AS base,
           max(CASE WHEN s.rn BETWEEN m.rn_first AND m.rn_eid THEN s.v END)           AS peak
    FROM marks m CROSS JOIN s
    WHERE m.rn_first > 4 AND m.rn_eid IS NOT NULL
    GROUP BY ALL
)
SELECT d.sector_name,
       count(*)                           AS years,
       min(year)                          AS first_year,
       max(year)                          AS last_year,
       100 * avg(peak / base)             AS peak_index_avg
FROM per_year JOIN dim_sector d USING (sector_key)
WHERE base IS NOT NULL AND peak IS NOT NULL
GROUP BY d.sector_name
ORDER BY peak_index_avg DESC;

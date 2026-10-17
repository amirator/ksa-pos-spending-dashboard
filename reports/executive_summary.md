# Executive summary: Saudi Consumer Spending Pulse

*Data: SAMA weekly point-of-sale statistics, 2020-05-10 to 2026-03-22 (307 weeks). Generated 2026-10-17 by `python run.py`; every figure below is read from `data/processed/kpis.json`.*

## Headline KPIs

| KPI | Value | Context |
|---|---|---|
| POS spending 2025 | SAR 705 bn | +6.2% YoY (avg weekly) |
| Transactions 2025 | 11.52 bn | +11.6% YoY |
| Average ticket 2025 | SAR 61.2 | -33.1% vs 2021 |
| Riyadh share 2025 | 34.6% | Jeddah 14.0% |
| 2026 to date (12 wks) | SAR 177 bn | +3.4% vs same weeks |

## Key insights

**1. Spending keeps growing, but growth is slowing every year.** Average weekly POS spending rose from SAR 9.08 bn in 2021 to SAR 13.57 bn in 2025 (+49.3%). Year-on-year growth has slowed each year, from +18.0% in 2022 to +6.2% in 2025. The first 12 weeks of 2026 were +3.4% on the same weeks a year earlier.

*So what:* Forecasts and budgets for consumer-facing businesses should assume mid-single-digit market growth, not the post-2020 rebound rates.

**2. Cards are reaching smaller, everyday purchases.** Weekly transaction counts grew +123.1% between 2021 and 2025, 2.5x the growth in value. The average ticket fell from SAR 91.4 to SAR 61.2 (-33.1%). The biggest named sectors are everyday ones: Beverage and Food (15.3% of 2024 value, SAR 41 average ticket) and Restaurants & Café (14.4%, SAR 33).

*So what:* This is consistent with the national cashless agenda. Merchants need low-friction card and wallet acceptance for low-value baskets.

**3. Riyadh is gaining share; Jeddah is growing more slowly than the market.** Riyadh's share of national POS value rose from 31.0% (2021) to 34.6% (2025). Jeddah remains the second-largest city at SAR 98.6 bn in 2025, but its share fell from 16.1% to 14.0%: Jeddah grew +29.9% against +66.7% for Riyadh and +49.3% nationally. Makkah (+87.0%) and Madinah (+60.9%) also grew faster than the national total.

*So what:* When planning store openings or regional marketing, weight Riyadh and the two holy cities more heavily. Jeddah's absolute size still makes it the main market in the west.

**4. Ramadan and Eid bring a large, predictable spike and dip.** Across 2021-2026, the peak week of the Ramadan-to-Eid window ran between 4% and 45% above the four weeks before Ramadan (median 16%). The week after Eid fell to between 11% and 27% below that baseline. The national peak week in the series (w/c 2025-03-23, SAR 20.1 bn) was the run-up to Eid al-Fitr. Clothing and Footwear and Jewelry both reach about 2.7x their pre-Ramadan level in their peak week (average over 5 years).

*So what:* Stock, staffing and campaigns should follow the Hijri calendar: the peak moves about 11 days earlier each Gregorian year.

**5. Miscellaneous Goods and Services and Hotels grew fastest; Electronic & Electric Devices shrank.** Between 2021 and 2024 (the last full year in the older sector taxonomy), Miscellaneous Goods and Services grew 23.0% a year, Hotels grew 19.4% a year (compound). Electronic & Electric Devices declined 8.6% a year. The top three sectors, including SAMA's catch-all 'Other', made up 46.1% of 2024 value.

*So what:* Hotel card spending growth is consistent with the tourism push. A shrinking POS line can also mean purchases moved online; these figures cover in-store terminals only.

## Method and caveats

Method: the raw SAMA CSVs are loaded into DuckDB, cleaned and pivoted in SQL, and modelled as a star schema (dim_date with Umm al-Qura Ramadan/Eid flags, dim_city, dim_sector, three weekly fact tables). Years are compared on average weekly values because some calendar years hold 53 week-starts. The newer SAMA release is appended only for national and city totals, which match the older release in the overlapping weeks; sector trends stop in July 2025 because the sector taxonomy changed. Figures cover card POS terminals only (no cash, no e-commerce).

Source: Saudi Central Bank (SAMA) weekly POS statistics via KAPSARC Data Portal (datasets: point-of-sale-transactions-by-sector-and-city; detailed-point-of-sale-transactions-by-sector-and-city). Values are card POS transactions only; analysis by the author.

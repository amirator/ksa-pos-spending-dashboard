# Data sources and license

| Key | Dataset | Original publisher | Download (public API, no key) | Landing page | Coverage | License |
|---|---|---|---|---|---|---|
| A | Point of Sale Transactions by Sector and City | Saudi Central Bank (SAMA), weekly POS statistics | https://datasource.kapsarc.org/api/explore/v2.1/catalog/datasets/point-of-sale-transactions-by-sector-and-city/exports/csv?delimiter=%2C | https://datasource.kapsarc.org/explore/dataset/point-of-sale-transactions-by-sector-and-city/ | Weekly, 2020-05-10 to 2025-07-06; 17 sectors (national) and 11 cities (all sectors) | Labelled **Public Domain** on the KAPSARC Data Portal; source copyright SAMA (http://www.sama.gov.sa/en-us/pages/privacypolicy.aspx) |
| B | Detailed Point of Sale Transactions by Sector and City | Saudi Central Bank (SAMA) | https://datasource.kapsarc.org/api/explore/v2.1/catalog/datasets/detailed-point-of-sale-transactions-by-sector-and-city/exports/csv?delimiter=%2C | https://datasource.kapsarc.org/explore/dataset/detailed-point-of-sale-transactions-by-sector-and-city/ | Weekly, 2025-06-29 to 2026-03-22; 32 sub-sectors and 61 cities | Labelled **Public Domain** on the KAPSARC Data Portal; source copyright SAMA |

KAPSARC (King Abdullah Petroleum Studies and Research Center) republishes SAMA's weekly POS bulletin in machine-readable form. `manifest.json` records the exact URL, byte size, SHA-256 and UTC download time of the files used for the published results. SAMA updates the series weekly, so a fresh `make data` can change the numbers slightly.

Units: values are in **SAR thousands** and transaction counts are in **thousands**. The rows marked "Change %" are SAMA's week-on-week changes. The pipeline does not use them for analysis, but a test checks that our recomputed week-on-week changes reproduce them.

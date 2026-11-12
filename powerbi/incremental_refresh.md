# Power Query incremental refresh notes

This model is **307 weeks** of national facts (about 3,070 city rows and 4,590 sector rows). That is small enough to **refresh in full** every time, which is what I recommend. Incremental refresh is documented here because mid-level KSA analyst JDs often ask for it, and so the pattern is ready if the series grows.

## What Power BI requires

1. Two **DateTime** parameters named exactly `RangeStart` and `RangeEnd` (Power BI will not detect Date-typed parameters).
2. A filter on the fact table(s) that uses both parameters, in the Power Query `Table.SelectRows` step, not in DAX.
3. The policy is set in Power BI Desktop (right-click the table → Incremental refresh) and only takes effect after publishing to a Premium, PPU or Fabric capacity. It does **not** run on Desktop itself.

## Filter snippet (add as the last step of each fact query)

```powerquery
Filtered = Table.SelectRows(
    Typed,
    each [week_start] >= Date.From(RangeStart)
     and [week_start] <  Date.From(RangeEnd)
)
```

Then change the query's `in` clause to `Filtered`.

## Lookback for period-variance measures

These DAX measures need rows **outside** the current week:

| Measure | Historical rows required |
|---|---|
| WoW % | previous 1 week |
| vs 4-week average | previous 4 weeks |
| vs 52 weeks ago / YoY | previous 52 weeks |
| YTD vs prior-year YTD | the prior calendar year |

If you turn incremental refresh on, set:

- **Filter out** rows only older than you will ever query (for example, weeks before 2020-05-10, which this extract does not have anyway).
- **Incremental period** of 1 month, with a **refresh window** that includes at least **13 months** of history stored (not archived) so the 52-week lag still resolves.
- Do **not** archive the prior year, or YoY and "vs 52 weeks ago" will go blank.

## Incremental refresh vs this repo

This repository does not contain a `.pbix`, and incremental refresh has not been executed against a Power BI service. The M snippets above are the standard pattern; they have been reviewed against Microsoft's incremental-refresh documentation, not run on a tenant.

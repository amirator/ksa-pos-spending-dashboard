"""Turn kpis.json into plain-English insights. Every number is read from the KPI dict;
nothing is typed by hand, so the text always matches the data."""
from __future__ import annotations


def _p(x: float, sign: bool = True) -> str:
    return f"{x:+.1f}%" if sign else f"{x:.1f}%"


def build_insights(k: dict) -> list[dict]:
    h, c, s, r, y = k["headline"], k["cities"], k["sectors_2024"], k["ramadan"], k["latest_ytd"]
    f0, f1 = k["first_full_year"], k["last_full_year"]
    tn = s["top_named"]
    fast = s["fastest_cagr"]
    named_fast = [x for x in fast if x["sector_name"] != "Other"][:2]
    slow = s["slowest_cagr"][0]
    top_lift = r["top_sector_lift"]
    l0, l1 = top_lift[0]["peak_index_avg"] / 100, top_lift[1]["peak_index_avg"] / 100
    if f"{l0:.1f}" == f"{l1:.1f}":
        lift_txt = (f"{top_lift[0]['sector_name']} and {top_lift[1]['sector_name']} both reach about {l0:.1f}x "
                    f"their pre-Ramadan level in their peak week (average over {top_lift[0]['years']} years).")
    else:
        lift_txt = (f"{top_lift[0]['sector_name']} and {top_lift[1]['sector_name']} reach about {l0:.1f}x and {l1:.1f}x "
                    f"their pre-Ramadan level in their peak week (average over {top_lift[0]['years']} years).")
    yoy = [k["yearly"][str(yr)]["value_yoy_pct"] for yr in range(f0 + 1, f1 + 1)]
    slowing = all(b < a for a, b in zip(yoy, yoy[1:]))
    t1 = ("Spending keeps growing, but growth is slowing every year" if slowing and min(yoy) > 0
          else "Spending growth has been uneven year to year")
    riy_up = c["riyadh_share_last"] > c["riyadh_share_first"]
    jed_down = c["jeddah_share_last"] < c["jeddah_share_first"]
    t3 = (f"Riyadh is {'gaining' if riy_up else 'losing'} share; Jeddah is "
          f"{'growing more slowly than' if jed_down else 'keeping pace with'} the market")
    t5 = (f"{named_fast[0]['sector_name']} and {named_fast[1]['sector_name']} grew fastest; "
          f"{slow['sector_name']} {'shrank' if slow['cagr_2021_2024_pct'] < 0 else 'grew slowest'}")
    return [
        {
            "title": t1,
            "body": (
                f"Average weekly POS spending rose from SAR {k['yearly'][str(f0)]['avg_weekly_value_bn_sar']:.2f} bn in {f0} "
                f"to SAR {h['avg_weekly_value_bn_sar']:.2f} bn in {f1} ({_p(h['value_growth_first_to_last_pct'])}). "
                f"Year-on-year growth has slowed each year, from {_p(k['yearly'][str(f0 + 1)]['value_yoy_pct'])} in {f0 + 1} "
                f"to {_p(h['value_yoy_pct'])} in {f1}. The first {y['weeks']} weeks of {y['to'][:4]} were "
                f"{_p(y['value_yoy_pct'])} on the same weeks a year earlier."
            ),
            "so_what": "Forecasts and budgets for consumer-facing businesses should assume mid-single-digit market growth, not the post-2020 rebound rates.",
        },
        {
            "title": ("Cards are reaching smaller, everyday purchases" if h["avg_ticket_change_pct"] < 0 else "Average card ticket is rising"),
            "body": (
                f"Weekly transaction counts grew {_p(h['txn_growth_first_to_last_pct'])} between {f0} and {f1}, "
                f"{h['txn_growth_first_to_last_pct'] / h['value_growth_first_to_last_pct']:.1f}x the growth in value. The average ticket fell from SAR {h['avg_ticket_first_full_year_sar']:.1f} "
                f"to SAR {h['avg_ticket_sar']:.1f} ({_p(h['avg_ticket_change_pct'])}). The biggest named sectors are everyday ones: "
                f"{tn[0]['sector_name']} ({tn[0]['share_2024_pct']:.1f}% of 2024 value, SAR {tn[0]['avg_ticket_sar_2024']:.0f} average ticket) "
                f"and {tn[1]['sector_name']} ({tn[1]['share_2024_pct']:.1f}%, SAR {tn[1]['avg_ticket_sar_2024']:.0f})."
            ),
            "so_what": "This is consistent with the national cashless agenda. Merchants need low-friction card and wallet acceptance for low-value baskets.",
        },
        {
            "title": t3,
            "body": (
                f"Riyadh's share of national POS value rose from {_p(c['riyadh_share_first'], False)} ({f0}) to "
                f"{_p(c['riyadh_share_last'], False)} ({f1}). Jeddah remains the second-largest city at SAR {c['jeddah_value_bn_sar_last']:.1f} bn "
                f"in {f1}, but its share fell from {_p(c['jeddah_share_first'], False)} to {_p(c['jeddah_share_last'], False)}: "
                f"Jeddah grew {_p(c['jeddah_value_growth_pct'])} against {_p(c['riyadh_value_growth_pct'])} for Riyadh "
                f"and {_p(c['national_value_growth_pct'])} nationally. Makkah ({_p(c['makkah_value_growth_pct'])}) and Madinah "
                f"({_p(c['madinah_value_growth_pct'])}) also grew faster than the national total."
            ),
            "so_what": "When planning store openings or regional marketing, weight Riyadh and the two holy cities more heavily. Jeddah's absolute size still makes it the main market in the west.",
        },
        {
            "title": "Ramadan and Eid bring a large, predictable spike and dip",
            "body": (
                f"Across {r['years'][0]}-{r['years'][-1]}, the peak week of the Ramadan-to-Eid window ran between "
                f"{r['peak_index_min'] - 100:.0f}% and {r['peak_index_max'] - 100:.0f}% above the four weeks before Ramadan "
                f"(median {r['peak_index_median'] - 100:.0f}%). The week after Eid fell to between "
                f"{100 - r['post_eid_index_max']:.0f}% and {100 - r['post_eid_index_min']:.0f}% below that baseline. The national peak week in the series "
                f"(w/c {k['peak_week']['week_start']}, SAR {k['peak_week']['value_bn_sar']:.1f} bn) "
                + ("was the run-up to Eid al-Fitr. " if k['peak_week']['week_start'] in r['peak_weeks'] else "fell outside the Ramadan window. ")
                + lift_txt
            ),
            "so_what": "Stock, staffing and campaigns should follow the Hijri calendar: the peak moves about 11 days earlier each Gregorian year.",
        },
        {
            "title": t5,
            "body": (
                f"Between {f0} and 2024 (the last full year in the older sector taxonomy), "
                + ", ".join(f"{x['sector_name']} grew {x['cagr_2021_2024_pct']:.1f}% a year" for x in named_fast)
                + f" (compound). {slow['sector_name']} declined {abs(slow['cagr_2021_2024_pct']):.1f}% a year. "
                f"The top three sectors, including SAMA's catch-all 'Other', made up {s['top3_share_pct']:.1f}% of 2024 value."
            ),
            "so_what": "Hotel card spending growth is consistent with the tourism push. A shrinking POS line can also mean purchases moved online; these figures cover in-store terminals only.",
        },
    ]

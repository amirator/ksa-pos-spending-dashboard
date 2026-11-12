// Query name in Power BI: dim_date
// Source: data/processed/dim_date.csv
// Paste into Advanced Editor after creating the FolderPath parameter (see parameters.m).
let
    SourcePath = FolderPath & "dim_date.csv",
    Source = Csv.Document(
        File.Contents(SourcePath),
        [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]
    ),
    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    Typed = Table.TransformColumnTypes(
        Promoted,
        {
            {"week_start", type date},
            {"week_end", type date},
            {"year", Int64.Type},
            {"quarter", Int64.Type},
            {"month", Int64.Type},
            {"month_name", type text},
            {"iso_week", Int64.Type},
            {"hijri_year", Int64.Type},
            {"hijri_month", Int64.Type},
            {"ramadan_days_in_week", Int64.Type},
            {"is_ramadan_week", type logical},
            {"is_eid_fitr_week", type logical},
            {"is_eid_adha_week", type logical},
            {"is_national_day_week", type logical},
            {"is_founding_day_week", type logical}
        }
    )
in
    Typed

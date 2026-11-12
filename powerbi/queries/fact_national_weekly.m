// Query name in Power BI: fact_national_weekly
// Source: data/processed/fact_national_weekly.csv
// Paste into Advanced Editor after creating the FolderPath parameter (see parameters.m).
let
    SourcePath = FolderPath & "fact_national_weekly.csv",
    Source = Csv.Document(
        File.Contents(SourcePath),
        [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]
    ),
    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    Typed = Table.TransformColumnTypes(
        Promoted,
        {
            {"week_start", type date},
            {"source", type text},
            {"txn_count_k", type number},
            {"txn_value_k_sar", type number}
        }
    )
in
    Typed

// Query name in Power BI: fact_sector_weekly
// Source: data/processed/fact_sector_weekly.csv
// Paste into Advanced Editor after creating the FolderPath parameter (see parameters.m).
let
    SourcePath = FolderPath & "fact_sector_weekly.csv",
    Source = Csv.Document(
        File.Contents(SourcePath),
        [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]
    ),
    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    Typed = Table.TransformColumnTypes(
        Promoted,
        {
            {"week_start", type date},
            {"sector_key", Int64.Type},
            {"txn_count_k", type number},
            {"txn_value_k_sar", type number}
        }
    )
in
    Typed

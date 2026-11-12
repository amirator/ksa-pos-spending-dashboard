// Query name in Power BI: dim_city
// Source: data/processed/dim_city.csv
// Paste into Advanced Editor after creating the FolderPath parameter (see parameters.m).
let
    SourcePath = FolderPath & "dim_city.csv",
    Source = Csv.Document(
        File.Contents(SourcePath),
        [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]
    ),
    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    Typed = Table.TransformColumnTypes(
        Promoted,
        {
            {"city_key", Int64.Type},
            {"city_name", type text},
            {"admin_region", type text}
        }
    )
in
    Typed

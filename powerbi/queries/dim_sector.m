// Query name in Power BI: dim_sector
// Source: data/processed/dim_sector.csv
// Paste into Advanced Editor after creating the FolderPath parameter (see parameters.m).
let
    SourcePath = FolderPath & "dim_sector.csv",
    Source = Csv.Document(
        File.Contents(SourcePath),
        [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]
    ),
    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    Typed = Table.TransformColumnTypes(
        Promoted,
        {
            {"sector_key", Int64.Type},
            {"sector_name", type text}
        }
    )
in
    Typed

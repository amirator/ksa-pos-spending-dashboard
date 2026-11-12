// Power BI parameters — create these in Power BI Desktop (Manage Parameters)
// before pasting the queries in queries/*.m.
//
// Name: FolderPath
// Type: Text
// Suggested value (edit to your local clone):
FolderPath = "C:\data\ksa-pos-spending-dashboard\data\processed\"

// Incremental refresh (DateTime, required by Power BI incremental refresh).
// See incremental_refresh.md before enabling. Leave unused if you load the
// full history (307 weeks — small enough to refresh in full every time).
//
// RangeStart = #datetime(2020, 5, 10, 0, 0, 0)
// RangeEnd   = #datetime(2026, 3, 23, 0, 0, 0)

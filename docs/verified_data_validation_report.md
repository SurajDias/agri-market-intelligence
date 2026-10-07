# Stage 4.9 verified-data validation status

## Gate result

- Verified source file found: **NO**
- Records imported: **0**
- Database changed: **NO**
- Source status: `unverified` for any future local candidate until exact official metadata is supplied and verified

## Workspace audit

The workspace was searched for CSV, XLSX, JSON, ZIP, and Parquet files in the
repository, including `data/`, `data/raw/`, `data/processed/`,
`data/snapshots/`, `uploads/`, and the project root. No candidate government
dataset was present. The `data/` directory contains no files.

Consequently there is no file metadata, discovered schema, date range, source
record count, commodity/market inventory, unit interpretation, dry-run result,
or post-import database count to report. No file was opened for import, no raw
snapshot was created, and no ingestion or data-quality run was created.

## Safe onboarding tooling

`python -m etl.import_official_file <path> --inspect` reads a CSV or JSON
candidate for metadata/schema inspection only. It reports columns, size, row
count, detected values, price/unit/provenance fields, and explicitly marks the
candidate `source_status=unverified`.

`--dry-run` and `--import` require exact official metadata:

- Provider: Ministry of Agriculture and Farmers Welfare / Directorate of Marketing and Inspection
- Dataset: Current Daily Price of Various Commodities from Various Markets (Mandi)
- Resource: `9ef84268-d588-465a-a308-a864a43d0070`
- Official data.gov.in source URL
- timezone-aware retrieval timestamp
- explicit `--confirm-official`

Dry-run reference matching uses existing commodities and markets and performs
no write. Import creates the existing raw snapshot, ingestion run, and data
quality run through the Stage 2 loader only after the verification gate passes.

## Blocker

An official export/API response must be supplied separately with independently
established resource identity before canonical `market_prices` can be changed.
No old data-ml dataset, synthetic data, undocumented endpoint output, or
unverified CSV is acceptable.

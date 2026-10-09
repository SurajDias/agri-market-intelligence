# Stage 5.1 — Official government dataset verification

## Decision

**NO-GO for import.** No candidate government dataset is present in the
repository. Therefore no record-level validation, dry run, database write, or
accepted/rejected estimate was performed. PostgreSQL was not accessed for
import and no records were imported.

## Dataset identity and provenance evidence

The intended canonical dataset is recorded by the existing onboarding code as:

- Dataset: `Current Daily Price of Various Commodities from Various Markets (Mandi)`
- Provider: `Ministry of Agriculture and Farmers Welfare / Directorate of Marketing and Inspection`
- Origin: AGMARKNET
- Resource ID: `9ef84268-d588-465a-a308-a864a43d0070`
- Catalog reference recorded in code: `https://www.data.gov.in/catalog/current-daily-price-various-commodities-various-markets-mandi`

These are the declared target identity and the repository's source metadata
constants, not provenance evidence for a local file. No downloaded response,
official export, checksum, retrieval manifest, or matching resource metadata
was available to independently bind a candidate file to that resource. A
read-only attempt to fetch the recorded catalog page timed out; no unofficial
endpoint was used. The target dataset is therefore **not verified for this
stage**.

## Inspected files and formats

The repository and expected data locations were inspected without searching
arbitrary private folders or uploading data:

- `data/`
- `data/raw/`
- `data/processed/`
- `data/snapshots/`
- `uploads/` (not present)
- repository candidate extensions, excluding virtual environments and dependency trees

No CSV, JSON, XLSX, XLS, ZIP, Parquet, JSONL, or NDJSON candidate was found.
The existing `data/` directories contain no files. Consequently there is no
actual file format, encoding, size, row count, header set, date range, or
missing-value profile to report.

The Stage 4.9 onboarding tool supports only:

- CSV with a header row, opened as UTF-8 with an optional UTF-8 BOM;
- JSON containing either a list of objects or an object with a `records` list.

XLSX/XLS, ZIP, Parquet, JSONL, and NDJSON are not supported by the current
tool and require an explicit adapter before inspection. No speculative adapter
was added.

## Schema and units assessment

This is a compatibility assessment of the existing code, not a claim about an
unseen dataset. The transformer recognizes aliases for:

- state, district, market/mandi;
- commodity, variety, and grade;
- arrival date;
- minimum, maximum, and modal price;
- price unit; and
- arrivals/arrival quantity/arrivals tonnes.

Required record-level facts are state, district, market, commodity, a parseable
arrival date, modal price, and an explicitly supported price unit. The canonical
record preserves source names and source date, variety, and grade where
provided. Reference matching requires exactly one active commodity and exactly
one active market matching normalized market, state, and district.

Price units are accepted only when explicitly represented as INR/kg or
INR/quintal (including the existing recognized spellings). INR/quintal is
converted to INR/kg by division by 100; INR/kg is converted to canonical
INR/quintal by multiplication by 100. Missing or unsupported units are
rejected. No unit may be inferred from a filename, column name alone, price
magnitude, or user assertion.

Arrivals are parsed as a numeric value and stored as `arrivals_tonnes`; the
current transformer does not establish or convert another arrivals unit. A
source file must therefore document that quantity as tonnes, or an explicit
adapter/mapping decision must be approved before import.

## Date coverage and record validation

No candidate means no date coverage, row-level missingness, duplicate count,
invalid-price count, future-date count, or accepted/rejected count was
calculated. The report must not treat zero observed files as a zero-row import
or as evidence that all records would be accepted.

If a candidate is supplied, the existing transformer will:

1. extract supported CSV/JSON records;
2. normalize field names and text;
3. accept ISO dates and unambiguous day-first government formats
   (`DD/MM/YYYY`, `DD-MM-YYYY`, and equivalent year-first forms);
4. reject missing/invalid/future dates, missing fields, malformed or negative
   prices, missing modal prices, unsupported units, and invalid
   min/modal/max relationships;
5. deduplicate by source ID and source record ID;
6. reject ambiguous or missing commodity/market reference matches; and
7. load only the remaining records through the existing loader.

Questionable records are counted by rejection reason by the transformer and
reference matcher; they are not silently discarded. No such counts exist for
this stage because no candidate exists.

## Compatibility and smallest next change

For a candidate that conforms to the supported CSV/JSON contract and supplies
explicit units and provenance metadata, no production ETL change is indicated.
The existing path is extraction/reading → normalization and validation →
reference matching → source-record deduplication → loader. The loader creates
source, ingestion, and data-quality records only during an explicit import and
does not create missing reference commodities or markets.

The smallest required next change depends on the supplied official artifact:

- supported CSV/JSON: provide the artifact and matching provenance manifest;
- XLSX/XLS/ZIP/Parquet/JSONL/NDJSON: stop and design an explicit adapter and
  tests before inspection; or
- undocumented/missing units or ambiguous market/commodity identifiers: stop
  and obtain source documentation or an approved mapping.

No adapter or production behavior was changed in Stage 5.1.

## Exact next steps

1. Acquire one official export or API response for resource
   `9ef84268-d588-465a-a308-a864a43d0070` through an independently confirmed
   official data.gov.in/AGMARKNET reference.
2. Place only the candidate and its provenance manifest in an expected project
   data directory; do not include credentials.
3. Record retrieval timestamp with timezone, exact URL/resource ID, provider,
   dataset name, file hash, byte size, encoding, and any official schema/unit
   documentation.
4. Run `python -m etl.import_official_file <path> --inspect` (using the
   project environment; `python3` alone lacks SQLAlchemy in this workspace).
5. Review all rejection reasons and run the explicit dry run with exact source
   metadata. Do not pass `--confirm-official` until provenance is independently
   supported.
6. Obtain review approval, then import only the reviewed artifact. Verify
   ingestion and data-quality results afterward.

## Tests

Focused existing ETL tests were run without database writes:

```text
backend/venv/bin/python -m unittest etl.tests.test_import_official_file etl.tests.test_transform etl.tests.test_extract
................
Ran 16 tests in 0.014s
OK
```

The same suite also passed with `venv/bin/python`. The system `python3`
interpreter ran 12 tests but could not import the onboarding module because
SQLAlchemy is not installed there; the project virtual environments are the
valid test environments used for the passing result. No test was added because
no concrete inspector defect was demonstrated.

## Files changed

- Created: `docs/stage_5_1_dataset_verification.md`

No ETL, frontend, database, test, or unrelated user files were modified.

## Files to stage later, after review

Only the following file should be considered for staging after human review:

- `docs/stage_5_1_dataset_verification.md`

Do not stage a candidate dataset, credentials, unrelated existing changes, or
any database/import output at this stage.

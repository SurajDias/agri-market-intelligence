# Stage 5.2 — Official data.gov.in source acquisition

## Decision

**NO-GO for acquisition and import.** This investigation did not acquire a
sample. Both approved hosts failed DNS resolution from this machine before any
HTTP request or authentication attempt, and no API key was configured in the
process environment. No database operation was performed.

## Official documentation verification

Official sources reviewed:

- Resource page: <https://www.data.gov.in/resource/current-daily-price-various-commodities-various-markets-mandi>
- Catalog page: <https://www.data.gov.in/catalog/current-daily-price-various-commodities-various-markets-mandi>
- Portal API/help documentation: <https://data.gov.in/help>

The official resource/catalog material identifies the mandi-price resource as
daily data generated through AGMARKNET and attributes it to the Ministry of
Agriculture and Farmers Welfare / Directorate of Marketing and Inspection. The
resource page exposes portal controls for CSV download, preview, and Data API,
but no credential-free downloadable URL was observed during this
investigation. The catalog page was not fetchable from the machine; its
availability in official search results is not runtime connectivity evidence.

The official portal help states that registered users can generate an API key
and access API URLs using that key. It also describes the portal as providing
machine-readable resources. The official resource page does not provide an
accessible resource-specific schema/API detail in the evidence available here,
so response fields, unit semantics, and resource-specific filters remain
unconfirmed until the page/API detail is reachable.

The existing repository adapter uses the documented data.gov.in resource
pattern with JSON, `limit`, `offset`, and `filters[...]` parameters. Its own
bounded limit is 1–1000 records per request, below the larger limits described
in generic data.gov.in resource guidance; no unbounded pagination is possible
through this adapter. That is an implementation fact, not proof that this
specific resource accepts every parameter.

Official documentation facts and observed runtime facts are intentionally kept
separate below.

## Configuration audit

- `DATA_GOV_IN_API_KEY`: **absent** from the process environment. Its value
  was not displayed or read from `.env`.
- `.env`: present, but not opened.
- Default resource ID in `etl/extract.py`: `9ef84268-d588-465a-a308-a864a43d0070`.
- Default API base in the adapter: `https://api.data.gov.in/resource`.
- Default timeout: 30 seconds; configured timeout must be positive.
- Adapter page-size bound: 1–1000 records; negative offsets are rejected.
- Request format: JSON is explicitly requested.
- Error handling: HTTP errors expose only status; request errors expose the
  exception type; neither includes the API key.
- Raw-store convention: `data/raw/<source_id>_<UTC timestamp>.json`, with
  `source`, `fetched_at`, `source_metadata`, and `records` fields.

The raw store can preserve source/retrieval metadata supplied by its caller,
but the current adapter does not itself acquire or write snapshots. It also
does not automatically record HTTP status, content type, request parameters,
or a checksum. No production change was made because no response was
acquired and no concrete defect needed fixing for this blocked stage.

## Network connectivity

Each host was checked once with bounded DNS resolution and a bounded HTTPS
request. No credential-bearing URL was used.

| Host | DNS | HTTPS result | Authentication reached? |
|---|---|---|---|
| `www.data.gov.in` | Failed to resolve | `curl` exit 6; HTTP `000`; no connection | No |
| `api.data.gov.in` | Failed to resolve | `curl` exit 6; HTTP `000`; no connection | No |

The failure category is local name resolution (`Could not resolve host`), not
an HTTP authentication rejection, TLS certificate failure, or API response.
No retries were made after the demonstrable DNS failure.

## Authentication and sample acquisition

Authentication was not attempted because:

1. no user-owned `DATA_GOV_IN_API_KEY` was present in the process environment;
   and
2. `api.data.gov.in` was not resolvable from this machine.

No shared, example, third-party, or online API key was used. No sample request
was made. Therefore:

- raw sample acquired: **NO**;
- raw snapshot path: **none**;
- checksum: **not applicable**;
- retrieval timestamp: **not applicable**;
- HTTP status/content type: **not applicable**;
- response record count: **not applicable**;
- pagination metadata: **not applicable**.

The operator must obtain a personal API key through the official data.gov.in
portal, configure it securely in the process/environment used for the next
run, and never place it in command-line arguments, shell history, logs, or
documentation.

## Schema and unit findings

No genuine response was obtained, so no response schema or records were
inspected. In particular, this stage establishes no observations about state,
district, market, commodity, variety, grade, arrival date, min/max/modal price,
missingness, date format, or price relationships.

The existing adapter only checks that a successful JSON payload has a
`records` array containing objects. It does not prove resource identity,
validate the resource title, calculate a checksum, inspect pagination metadata,
or establish price/arrival units. Those checks must be performed on a genuine
response before any sample can be considered import-ready. Units must not be
inferred from numeric magnitude. The existing project transformer rejects
missing or unsupported price units unless an explicitly documented source unit
is supplied.

No sample of up to five records exists, and no conclusion about full-dataset
quality or forecasting history is warranted.

## Database write verification

- PostgreSQL connection: not opened for this investigation.
- Migrations/seeds: not run.
- Production ETL/import: not run.
- `market_prices` writes: **0**.
- Raw snapshot writes: **0**.

The work was limited to read-only repository/configuration inspection, official
documentation lookup, bounded network probes, and tests using fakes/temp
directories. Existing working-tree changes were preserved.

## Tests

Relevant existing acquisition/transformation/raw-store tests:

```text
backend/venv/bin/python -m unittest etl.tests.test_extract etl.tests.test_import_official_file etl.tests.test_raw_store etl.tests.test_transform
.................
Ran 17 tests in 0.015s
OK
```

No tests were added or modified. No concrete security or acquisition defect
was demonstrated that required a code change.

## Recommended next action

Restore DNS/HTTPS access to both approved data.gov.in hosts, then configure a
personal API key through the official portal without exposing it. Re-run one
request of at most five JSON records through the existing adapter, preserving a
raw snapshot plus source URL without credentials, resource ID, timezone-aware
retrieval timestamp, non-secret parameters, HTTP status, content type,
checksum, and record count. Validate resource identity, fields, units, dates,
prices, and pagination metadata before considering Stage 5.3.

## Import readiness

**NO-GO.** No sample was acquired, provenance cannot be evaluated at record
level, and no import or database write is authorized by this stage.

## Files created/modified

- Created: `docs/stage_5_2_source_acquisition.md`
- No production ETL, frontend, schema, migration, database, or test files were
  modified.

## Files to stage after review

Only this documentation file should be considered for staging after review:

- `docs/stage_5_2_source_acquisition.md`

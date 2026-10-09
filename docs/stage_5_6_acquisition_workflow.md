# Stage 5.6 — Resilient operator-triggered acquisition workflow

## Implementation audit

The existing `etl/extract.py` adapter remains the only source adapter. Its
legacy `fetch_records` method was preserved. The new operator path adds a
bounded preflight and a separate validated-response method around that adapter;
it does not transform, load, forecast, or create recommendations.

The existing `etl/raw_store.py` helper remains the storage convention. A new
raw-response helper writes original response bytes unchanged and a JSON
provenance sidecar. It uses exclusive body-file creation and therefore does not
overwrite an existing artifact.

No XML adapter was added. The page-state XML filename is not sufficient
evidence that the resource returns XML or that XML contains market-price
records.

## Operator commands

Use the project environment from the repository root:

```text
backend/venv/bin/python -m etl.acquire_official --preflight
```

This performs one DNS resolution and, only if DNS succeeds, one unauthenticated
HTTPS check against the configured official API base. It never sends an API
key.

After preflight succeeds and a personal key is configured only in the process
environment:

After setting `DATA_GOV_IN_API_KEY` through a secure operator environment/session
mechanism, run:

```text
backend/venv/bin/python -m etl.acquire_official --acquire --limit 5 --offset 0
```

The key must not be put in shell history, logs, documentation, or command-line
arguments. `--limit` is restricted to 1–5 by the
operator command. `--offset` is nonnegative and the adapter enforces the
existing 1–1000 bound.

The command can write to an alternate review directory without changing the
database:

```text
backend/venv/bin/python -m etl.acquire_official --acquire --limit 5 --output-dir /path/to/review/raw
```

## Required configuration

- `DATA_GOV_IN_API_KEY`: personal data.gov.in key, environment-only for
  acquisition; absent keys stop before authenticated acquisition.
- `DATA_GOV_IN_RESOURCE_ID`: must remain
  `9ef84268-d588-465a-a308-a864a43d0070`.
- `DATA_GOV_IN_API_URL`: must be HTTPS `api.data.gov.in/resource`; unofficial
  host/path overrides are rejected by the operator workflow.
- `DATA_GOV_IN_TIMEOUT_SECONDS`: positive timeout, default 30 seconds.
- `RAW_DATA_DIR`: optional raw output directory, default `data/raw`.

## Preflight behavior

Preflight is DNS-first and bounded:

1. Validate the official HTTPS API host, resource ID, and `/resource` path.
2. Resolve the configured official hostname once.
3. Stop immediately with `dns_failure` if resolution fails.
4. If DNS succeeds, make one unauthenticated HTTPS request with the configured
   timeout and no redirects.
5. Classify the result as `success`, `http_error`, `connection_refused`,
   `timeout`, `tls_failure`, or a general connection failure.

It does not treat a successful `www.data.gov.in` page request as proof that the
API host works. It does not retry or switch endpoints. Nonzero command status
(`2`) means the source is unavailable or configuration/acquisition was refused.

## Acquisition safety

The acquisition path stops before an authenticated request when the API key is
missing. With a key, it uses the existing adapter and makes one bounded request
with JSON format, explicit limit/offset, optional filters support in the
adapter, and redirects disabled. It does not paginate automatically or retry.

Before accepting records it validates:

- HTTP status through `raise_for_status`;
- a JSON content type, rejecting HTML/login/access-denied responses;
- a JSON object payload;
- optional response resource identity when supplied, rejecting mismatches;
- a `records` array; and
- object type for every record.

The API key is included only in the in-memory request parameter map. Returned
reports and errors exclude it. The source URL recorded in metadata has no query
string or credential.

This stage does not validate commodity mappings, price units, dates, or
min/modal/max relationships. Those remain subsequent review/ETL validation
steps. A successful bounded response is not proof that the full dataset is
complete or import-ready.

## Raw artifact format

For a validated JSON response, `write_raw_response` writes:

- `<source_id>_<UTC timestamp>[optional suffix].json`: exact response bytes,
  unchanged;
- matching `.metadata.json` sidecar containing retrieval timestamp, source URL
  without credentials, resource ID, non-secret request parameters, HTTP status,
  content type, record count, downloaded byte count, SHA-256, the artifact
  filename, and `publication_status: complete`.

Temporary files are written in the destination directory, flushed and
`fsync`ed, then published with exclusive hard links, so neither final file can
overwrite an existing path. A lock file reserves the candidate name against
competing writers. Each lock contains a unique owner token; cleanup removes a
lock only when its token still matches the writer, so a replaced lock is never
removed by the original writer. Stale locks are not automatically removed;
they conservatively cause the candidate suffix to be skipped and require
manual operator review. The two-file publication is not atomic: a crash after body
publication and before sidecar publication can leave an orphan body (and a
lock file if the process crashed). Subsequent runs skip existing body,
sidecar, or lock paths and publish a new suffixed pair; they never delete or
replace the orphan. Only a body with a matching complete sidecar is a
successful artifact. A later run must review or clean orphan files manually.
An OS crash can also leave same-directory temporary `.tmp` files; they are
never treated as artifacts and require manual review/cleanup.

Body-write, metadata-write, publication, and sidecar failures return failure
without reporting success. Temporary files are cleaned on handled failures;
already-published body files are deliberately retained rather than replaced.

HTML, malformed JSON, invalid identity, invalid shape, HTTP errors, and
unsupported content types are rejected and are not stored as accepted official
artifacts. Metadata containing obvious API-key, token, authorization,
password, credential, secret, or cookie fields/values is rejected.

## Dry-run and database guarantee

`etl.acquire_official` imports only `etl.extract` and `etl.raw_store`. It does
not import `backend`, `etl.load`, SQLAlchemy, migrations, seed code, or
analytics. The command stops after raw acquisition and prints
`database_writes: 0`. No PostgreSQL connection is opened by this workflow.

No source records were acquired during this implementation stage, and no raw
artifact was created.

## Failure behavior and limitations

- DNS/HTTPS failure: stop immediately; no retry or alternate endpoint.
- Missing API key: stop without an authenticated request.
- Every internal HTTP session is configured with zero retries and every request
  sets `allow_redirects=False`; failed HTTP acquisition makes one attempt. The
  legacy compatibility shim omits that keyword only for injected test doubles
  whose `get` signature cannot accept it; the real `requests.Session` path
  always receives the explicit false value.
- Interactive login/CAPTCHA/contact form: stop for manual operator action;
  no bypass or automation is provided.
- XML page-state URL: not implemented or requested.
- Resource-level units, schema completeness, and full-dataset quality: remain
  unresolved until a genuine response is reviewed.
- The current environment's DNS/API failures remain external blockers.

The CLI returns exit code `0` only for a successful preflight or completed raw
acquisition. Source unavailability, missing credentials, validation failures,
and handled raw-publication failures print a sanitized JSON failure report and
return exit code `2`; unexpected argument errors are handled by `argparse`.

## Tests

Focused existing and new ETL tests:

```text
backend/venv/bin/python -m unittest etl.tests.test_extract etl.tests.test_import_official_file etl.tests.test_raw_store etl.tests.test_transform etl.tests.test_acquisition_workflow
..................................
Ran 34 tests
OK
```

The tests use only fake sessions/responses and temporary directories. They do
not contact data.gov.in, use real market data, access PostgreSQL, or run the
loader.

## Files created/modified

- Created: `etl/acquire_official.py`
- Created: `etl/tests/test_acquisition_workflow.py`
- Created: `docs/stage_5_6_acquisition_workflow.md`
- Modified: `etl/extract.py` — added bounded preflight and validated-response
  support while preserving `fetch_records`.
- Modified: `etl/raw_store.py` — added unchanged-response and provenance-sidecar
-  storage, crash-safe exclusive publication, and metadata secret rejection.

No frontend, database schema, migration, loader, transformer, or business
formula was modified. Existing unrelated working-tree changes were preserved.

## Files to stage after review

- `etl/acquire_official.py`
- `etl/tests/test_acquisition_workflow.py`
- `etl/extract.py`
- `etl/raw_store.py`
- `docs/stage_5_6_acquisition_workflow.md`

# Stage 5.3 — Official data.gov.in download workflow investigation

## Outcome

**No download was attempted and no sample was acquired.** The approved
data.gov.in hosts were already shown in Stage 5.2 to fail DNS resolution from
this machine. This stage therefore distinguishes official portal evidence from
unverified runtime behavior and does not retry the failed hosts.

## Official URLs and evidence

- Resource page: <https://www.data.gov.in/resource/current-daily-price-various-commodities-various-markets-mandi>
- Catalog page: <https://www.data.gov.in/catalog/current-daily-price-various-commodities-various-markets-mandi>
- Portal help/API access guidance: <https://data.gov.in/help>
- API base used by the existing adapter: `https://api.data.gov.in/resource`

Official catalog/search evidence identifies this resource as AGMARKNET mandi
data owned by the Ministry of Agriculture and Farmers Welfare / Directorate of
Marketing and Inspection. It displays controls labelled **CSV Download**,
**Export in Other Format**, and **Data API**. The portal help states that
registered users can generate an API key and access API URLs using that key.

The official resource page was not reachable from this machine during Stage
5.2, and no resource-specific API-detail URL, direct CSV URL, export URL, or
download form HTML was obtained. The labels above are official indexed-page
evidence, not proof that a download route currently works.

## Workflow findings

| Option | Result | Evidence/limitation |
|---|---|---|
| Resource-page CSV download | Unverified | Official page exposes the control, but the page/form could not be reached. No direct URL or form fields were observed. |
| CSV authentication requirement | Unverified | No evidence establishes whether login, an API key, a session, contact details, or CAPTCHA is required. Do not automate or bypass any such control. |
| Official Data API | Documented in principle; not runtime-tested | Portal help documents API-key access; no resource-specific API detail was reachable. |
| Existing adapter | Compatible in principle | Uses the official resource ID, JSON, bounded `limit`/`offset`, optional `filters[...]`, and an environment-only API key. |
| Official bulk/ZIP export | Not confirmed | No verified resource-specific bulk URL or ZIP route was found. Do not infer one from other data.gov.in resources. |
| Unofficial/alternate endpoint | Not permitted | Not investigated or used. |

The CSV download form requirements are therefore **not observed**. If the
official UI later presents an interactive login, CAPTCHA, contact form, or
other access control, the minimum legitimate action is for an authorized
operator to complete it manually and save the resulting official file and
provenance metadata. No automation or bypass is authorized by this stage.

## Existing adapter compatibility

`etl/extract.py` already targets resource ID
`9ef84268-d588-465a-a308-a864a43d0070` and the official API base. It:

- reads `DATA_GOV_IN_API_KEY` only from the environment;
- requests JSON;
- bounds each request to 1–1000 records;
- rejects negative offsets;
- supports `filters[...]` parameters;
- uses a positive bounded timeout; and
- avoids exposing the key in its error messages.

It validates only that the response is JSON with a `records` list of objects.
It does not itself verify resource title/identity, capture HTTP metadata,
calculate a checksum, persist a raw snapshot, or validate price/date/unit
semantics. Those remain required after a genuine response is obtained.

The existing raw-store helper can preserve caller-supplied source metadata and
records under `data/raw/`, but it was not invoked. No production adapter or
raw-store behavior was changed.

## Network limitation

Stage 5.2 performed one bounded check per approved host:

- `www.data.gov.in`: DNS failure; HTTPS not reached; `curl` exit 6 and HTTP
  status `000`.
- `api.data.gov.in`: DNS failure; HTTPS not reached; `curl` exit 6 and HTTP
  status `000`.

The failures occur before HTTP authentication. No repeated retry was made in
Stage 5.3. This prevents testing the CSV form, direct export, API response,
or any authentication behavior from this machine.

## Best next action

Restore DNS/HTTPS access to `www.data.gov.in` and `api.data.gov.in`, then have
an authorized operator use the resource page to determine whether the CSV
control yields a direct official file or an interactive form. If an API route
is exposed and a personal API key is configured securely, use the existing
adapter for at most five JSON records and preserve a provenance-bearing raw
snapshot. If the UI requires CAPTCHA or interactive contact details, complete
that step manually; do not automate or bypass it.

Do not import the resulting file or sample until resource identity, schema,
units, dates, prices, and provenance have been reviewed.

## Safety and change control

- PostgreSQL was not accessed; no records were created or changed.
- No import, migration, seed, frontend, schema, or production ETL change was
  made.
- No credentials or third-party API keys were used or recorded.
- No sample file or raw snapshot was created.
- Existing working-tree changes were preserved.

## Tests

Relevant existing acquisition, importer, raw-store, and transformation tests
were run with the project virtual environment:

```text
backend/venv/bin/python -m unittest etl.tests.test_extract etl.tests.test_import_official_file etl.tests.test_raw_store etl.tests.test_transform
.................
Ran 17 tests in 0.015s
OK
```

No tests were added or modified.

## Files changed

- Created: `docs/stage_5_3_download_workflow.md`

No production code or unrelated working-tree files were modified.

## Readiness

**NO-GO.** Programmatic API access and the resource-page download workflow
remain unverified because network resolution fails before either route can be
tested. No file is authorized for import.

## Files to stage after review

- `docs/stage_5_3_download_workflow.md`

# Stage 5.5 — Official XML download verification

## Result

**NO-GO.** The exact official URL was recovered and passed hostname
validation, but the single permitted GET failed before HTTP at DNS resolution.
No XML bytes were downloaded, no raw artifact was saved, and no database or
ETL operation occurred.

## Exact URL recovery

The URL was recovered without reconstruction from:

- `/tmp/mandi-resource.html`
- `window.__NUXT__.data[0].post.field_datafile`

Recovered URL:

```text
https://www.data.gov.in/files/ogdpv2dms/s3fs-public/Date-Wise-Prices-all-Commodity.xml
```

The Stage 5.4 report also records this same published `field_datafile` URL.
No credential-bearing `field_datafile_url` value was used or reproduced.

## Host verification

- Scheme: `https`
- Host: `www.data.gov.in`
- Host classification: official data.gov.in government domain
- Redirect policy: automatic redirects disabled

The URL passed the required scheme and hostname checks. No unrelated host was
contacted.

## Single bounded request

One GET request was made to the exact URL with:

- connection timeout: 10 seconds;
- total timeout: 30 seconds;
- redirects: disabled;
- retries: none.

Observed result:

| Field | Result |
|---|---|
| Request exit | `6` |
| HTTP status | `000` |
| Content type | unavailable |
| Content-Length | unavailable |
| Downloaded bytes | `0` |
| Redirect destination | none observed |
| Failure stage | DNS resolution before HTTP |
| Error category | `Could not resolve host: www.data.gov.in` |

Because no HTTP response was received, XML declaration and root-element
inspection was not possible.

## Artifact and data status

- Valid XML artifact saved: **No**
- Artifact path: none
- SHA-256: not applicable
- Retrieval timestamp: not applicable because no response was received
- Content classification: not applicable
- Price-data determination: not possible

No misleading empty, error-page, or partial artifact was retained. The
existing `data/raw/` convention was not invoked.

## Database and change control

- PostgreSQL connection: not opened.
- Database writes: `0`.
- Migrations/seeds/imports: not run.
- Production ETL/frontend: unchanged.
- Credentials/cookies/sensitive headers: not printed or used.
- No staging, commit, or push performed.

## Remaining blockers and next action

The remaining blocker is DNS/network availability for `www.data.gov.in`. The
exact URL is known and validly hosted, but accessibility is unverified because
the request failed before HTTP. Do not retry until DNS/network service is
known to be restored. Then repeat the bounded verification under the same
redirect and TLS rules before retaining any artifact.

Import readiness remains **NO-GO**.

## Tests

No project tests were run because no project code changed.

## Files created/modified

- Created: `docs/stage_5_5_xml_download_verification.md`
- No production code, frontend, database, migration, test, or raw-data files
  were modified.

## File to stage after review

- `docs/stage_5_5_xml_download_verification.md`

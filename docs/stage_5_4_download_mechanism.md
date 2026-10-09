# Stage 5.4 — Official resource download mechanism

## Outcome

This was a read-only inspection. No dataset, sample, API response, raw
snapshot, or database record was acquired or created. The local HTML contains
an official file URL and an API URL field, but neither was invoked.

## Resource page inspected

- Local file: `/tmp/mandi-resource.html`
- Official page: <https://www.data.gov.in/resource/current-daily-price-various-commodities-various-markets-mandi>
- Resource ID found in page state: `9ef84268-d588-465a-a308-a864a43d0070`
- Size: 1,015,233 bytes

The page is a Nuxt server-rendered shell. The visible resource-detail body is
not present in the downloaded HTML; the page state is embedded in
`window.__NUXT__` and is intended to be completed by client-side bundles.

Relevant non-secret fields from that state are:

```text
field_datafile: "https://www.data.gov.in/files/ogdpv2dms/s3fs-public/Date-Wise-Prices-all-Commodity.xml"
field_file_format: "text/csv"
field_is_api_available: true
field_show_export: true
field_show_request_api: true
uuid: "9ef84268-d588-465a-a308-a864a43d0070"
```

The page state also contains a separate credential-bearing `field_datafile_url`
API value. Its credential was not printed, copied into this report, or used.

## Download-control implementation findings

The HTML contains no resource-specific `<form>` action, direct `<a>` element,
or visible button markup for CSV/export/API controls. The only ordinary form
observed is the global site-search form. The resource controls are therefore
client-rendered or client-bound rather than ordinary static HTML links.

The page references these official Nuxt bundles:

```text
/_nuxt/c963a90.js  /_nuxt/5f5dc85.js  /_nuxt/6f8a3d9.js
/_nuxt/d96b352.js  /_nuxt/5579f05.js  /_nuxt/dc3a541.js
/_nuxt/df1d3a9.js  /_nuxt/4a81ae4.js  /_nuxt/a2b0dd9.js
/_nuxt/7bff415.js  /_nuxt/6d18089.js
```

One bounded, read-only fetch was attempted for each referenced official bundle
using the same `www.data.gov.in` host. All failed before HTTP at DNS
resolution. Consequently, no bundle implementation was inspected and no
claim is made about whether the controls use a GET link, JavaScript request,
form submission, login, CAPTCHA, or export service.

## Official API findings

The downloaded official page state provides this redacted API structure:

```text
https://api.data.gov.in/resource/{resource-id}?api-key=<redacted>&offset=0&limit=all
```

This is evidence of a published page-state field, not a successful API test or
an independent API documentation page. The HTML contains navigation to the
official `/apis` area, but no resource-specific API documentation or API-detail
URL was present in the downloaded page. The portal help URL previously reviewed
is <https://data.gov.in/help>; it describes API-key generation/access for
registered users, but it does not establish that this resource endpoint is
currently reachable.

The existing adapter is structurally compatible with the observed API pattern:
it uses the same resource ID and API base, requests JSON, accepts bounded
`limit`/`offset`, supports `filters[...]`, reads the key only from the
environment, and does not expose the key in errors. It intentionally does not
use the page's unbounded `limit=all` value.

## Direct downloadable URL assessment

**Published URL found: yes. Usable download verified: no.**

The official page state publishes an absolute `field_datafile` URL ending in
`Date-Wise-Prices-all-Commodity.xml`. It was not requested because this stage
forbids data acquisition. Its `.xml` path also conflicts with the page state's
`text/csv` format value, so the file type and contents remain unverified. No
direct CSV, JSON, or ZIP URL was verified as working.

The page state's API field is not treated as a safe credential-free download
URL. Its embedded credential was not used or exposed.

## Connectivity findings

Previously recorded control/runtime evidence:

- Resource page: HTTP 200 over IPv4; local HTML was saved successfully.
- `api.data.gov.in`: DNS resolves to `164.100.61.198`, but TCP 443 is refused;
  no HTTP response or authentication result was obtained.

During this stage, the distinct official Nuxt bundle requests failed earlier at
DNS resolution for `www.data.gov.in`; no retries were made after that failure.
No API request, resource-file request, form submission, CAPTCHA interaction,
or download was attempted.

## Confirmed versus unverified

Confirmed:

- The local HTML belongs to the requested official resource ID.
- The page state advertises a data-file URL, API availability, export visibility,
  and request-API visibility.
- The existing adapter targets the same resource ID and official API base.
- No data or credentials were acquired or written by this stage.

Unverified:

- Whether the data-file URL returns XML, CSV, an error, or an access-control
  response.
- Whether the visible CSV/export controls require login, CAPTCHA, contact
  details, or a session/form token.
- The actual JavaScript request path and parameters used by the controls.
- Whether the API endpoint accepts the published page-state request.
- Resource schema, units, pagination behavior, and record validity.

## Next action

The single best next action is to restore reliable DNS/HTTPS access to
`www.data.gov.in` and `api.data.gov.in`, then have an authorized operator use
the official page interactively to inspect the CSV control. If it presents
CAPTCHA, login, or contact details, the operator must complete that step
manually; no automation or bypass should be attempted. Only after that should
the existing adapter be used with a personal API key for a bounded request.

## Safety and change control

- PostgreSQL: unchanged; no connection, migration, seed, or import performed.
- Production ETL/frontend: unchanged.
- Raw snapshots: none created.
- Credentials: not printed, used, or documented.
- No staging, commit, or push performed.
- Existing working-tree changes preserved.

## Tests

No project tests were run because no project code was changed. The investigation
was limited to local HTML inspection and bounded official-asset diagnostics.

## Files created/modified

- Created: `docs/stage_5_4_download_mechanism.md`
- No production code, frontend, database, migration, or test files modified.

## Files to stage after review

- `docs/stage_5_4_download_mechanism.md`

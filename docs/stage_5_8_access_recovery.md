# Stage 5.8 — Official Data Access Recovery and Next-Step Decision

## Investigation

- Timestamp: `2026-10-09T14:14:12+05:30` (Asia/Kolkata)
- Repository root: `/home/suraj/Desktop/agri-market-intelligence`
- Branch: `main`
- Initial Git status: 10 modified tracked paths and 31 untracked paths.
- Final Git status: the same pre-existing paths plus this report; no existing
  files were staged, reset, cleaned, restored, or discarded.

The investigation reused the Stage 5.6 operator workflow and reviewed the
Stage 5.7 report plus the Stage 5.3–5.5 official download investigations.

## Configuration

`DATA_GOV_IN_API_KEY` was absent from the current process environment. Only
presence was checked; its value was not inspected or printed. No authenticated
API request was attempted.

## Connectivity recovery check

One bounded command was run from the repository root:

```text
backend/venv/bin/python -m etl.acquire_official --preflight
```

Sanitized result:

```json
{
  "source_availability": {
    "hostname": "api.data.gov.in",
    "dns_status": "dns_failure",
    "https_status": "not_attempted",
    "http_status": null,
    "detail": "DNS resolution failed"
  },
  "database_writes": 0
}
```

Exit status: `2`.

The failure occurred during DNS resolution, before TCP, TLS, HTTP, or API-key
authentication. No retry, endpoint fallback, or alternate host was used.
This result does not establish permanent unavailability; it establishes only
that the API host was not reachable from this machine at this attempt.

## Official alternatives reviewed

The existing local Stage 5.3–5.5 evidence confirms:

- the official resource page advertises CSV Download, Export in Other Format,
  and Data API controls;
- the page state contained an official `field_datafile` URL ending in
  `Date-Wise-Prices-all-Commodity.xml`; and
- the portal documents API-key access in principle.

No resource-specific CSV/export form, downloadable file response, browser
workflow, or usable direct download URL has been verified. The page-state XML
URL was not requested in this stage and remains unverified; its XML suffix also
conflicts with the recorded `text/csv` format. No documented bulk/ZIP route was
confirmed. Therefore there is no actionable manual export route that can be
recommended as verified evidence at this time.

## Decision

**Outcome C — BLOCKED.**

Evidence:

1. The official API preflight failed at DNS resolution.
2. No personal API key is configured in the process environment.
3. The official browser/export controls and page-state file URL remain
   unverified and were not automated or bypassed.

## Exact next action

Restore reliable DNS/HTTPS access to `api.data.gov.in` and configure a personal
`DATA_GOV_IN_API_KEY` securely in the process environment. Then run the
existing bounded `--preflight` command once. Only after a successful preflight
should the operator make the single permitted `--acquire --limit 5 --offset 0`
attempt. If the official resource page becomes reachable first, an authorized
operator may manually inspect its CSV/export control; CAPTCHA, login, or
contact workflows must be completed manually and must not be bypassed.

## Safety and change control

- PostgreSQL was not accessed.
- No imports, raw artifacts, loader, migrations, seeds, forecasting, or
  recommendations were run.
- No application source code or frontend files were modified.
- No credentials were printed or recorded.
- No staging, commit, push, reset, clean, or restore operation was performed.
- Pre-existing working-tree changes remain untouched.

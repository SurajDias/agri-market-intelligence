# Stage 4.10 — Full System Integration, Architecture Audit & Hardening

Audit date: 2026-10-07

## Executive result

The backend imports successfully and all registered API routes are present in
OpenAPI. Domain engines and ETL tests pass, and two concrete integration fixes
were applied: POST was added to CORS methods, and unified decision intelligence
now retrieves candidate-market history in one bounded query.

The system cannot be declared fully integrated because PostgreSQL is not
reachable, the FastAPI `TestClient` dependency (`httpx2`) is absent, no real
government data is available, and the frontend source files are empty. The
architecture is integration-ready but database-backed end-to-end validation is
incomplete.

## 1. Architecture overview

```text
FastAPI route
  -> Pydantic schema validation
  -> service/orchestration
  -> domain engine
  -> SQLAlchemy/PostgreSQL where required

Official source adapter
  -> raw snapshot
  -> transform/validation/deduplication
  -> reference matching
  -> loader
  -> ingestion/data-quality runs
  -> historical analytics/forecasting
  -> evidence/recommendation/simulation/decision intelligence
```

The system has a clear separation between economic calculations, evidence,
confidence, robustness, and data quality. API routes still perform some
reference validation and orchestration, which is consistent with the current
small application but is a future refactoring boundary.

## 2. Component inventory

### API routes

- `markets.py`: commodities, markets, market prices
- `historical_prices.py`: historical observations and coverage
- `historical_analytics.py`: descriptive analytics
- `baseline_forecasts.py`: naive baseline forecasts
- `forecasts.py`: walk-forward evaluation
- `transport.py`: transport economics
- `shelf_life.py`: spoilage/shelf-life calculation
- `decision.py`: expected net value
- `recommendations.py`: economic ranking/opportunity
- `evidence.py`: evidence quality/confidence
- `simulator.py`: counterfactual/sensitivity/robustness
- `decision_intelligence.py`: unified orchestration
- `data_quality.py`: data-quality/readiness summary

`decision_simulator.py` is an empty unused route module and is not registered;
the active simulator route is `simulator.py`.

### Engines

- `transport_cost.py`
- `shelf_life.py`
- `decision_engine.py`
- `recommendation.py`
- `evidence.py`
- `simulator.py`
- `decision_intelligence.py`

### Services

- Historical price retrieval
- Historical analytics
- Forecast preparation/evaluation
- Data-quality/readiness orchestration

### Models

- `commodities`
- `markets`
- `data_sources`
- `market_prices`
- `ingestion_runs`
- `data_quality_runs`

### ETL

- `extract.py`
- `raw_store.py`
- `transform.py`
- `load.py`
- `data_quality.py`
- `scheduler.py`
- `import_official_file.py`

### Migrations

- `001_initial_foundation`
- `002_market_price_provenance`

Current Alembic head is `002_market_price_provenance`.

## 3. API route inventory

| Method | Path | Response | Database |
| --- | --- | --- | --- |
| GET | `/api/health` | health object | connection check |
| GET | `/api/commodities` | commodity list | yes |
| GET | `/api/markets` | market list | yes |
| GET | `/api/markets/{market_id}` | market | yes |
| GET | `/api/markets/{market_id}/prices` | price list | yes |
| GET | `/api/historical-prices` | historical prices | yes |
| GET | `/api/historical-prices/coverage` | coverage | yes |
| GET | `/api/historical-prices/analytics` | analytics | yes |
| GET | `/api/forecasts/baseline` | baseline forecast | yes |
| GET | `/api/forecasts/evaluate` | evaluation | yes |
| POST | `/api/transport/calculate` | transport result | reference validation |
| POST | `/api/shelf-life/estimate` | shelf-life result | no |
| POST | `/api/decision/calculate` | decision result | no |
| POST | `/api/recommendations/analyze` | ranked recommendation | reference validation |
| POST | `/api/evidence/assess` | evidence/confidence | yes |
| POST | `/api/simulator/analyze` | scenarios/robustness | reference validation |
| POST | `/api/decision-intelligence/analyze` | unified decision | yes |
| GET | `/api/data-quality/summary` | quality/readiness | yes |

No duplicate OpenAPI paths or conflicting registered routes were found.

## 4. Database/schema/migration audit

The SQLAlchemy models, `database/schema.sql`, and the two migrations describe
the same six-table foundation and provenance additions. Constraints and indexes
are aligned, including the market-price source-record uniqueness constraint,
foreign keys, date/commodity/market indexes, and the `data_quality_runs.metrics`
JSON column.

No schema migration was required or added.

Database-dependent verification was blocked by unavailable PostgreSQL.

## 5. ETL pipeline audit

The connected path is:

```text
DataGovInAgmarknetAdapter
  -> write_raw_snapshot
  -> transform_records
  -> reference matching in load_records
  -> source-record/database deduplication
  -> market_prices
  -> ingestion_runs
  -> data_quality_runs
```

The verified-file onboarding tool uses the same loader and does not create a
parallel canonical loader. Unit conversion, date validation, provenance, and
rejection reasons survive through the existing report structures.

No real source batch was available, so database persistence could not be
verified end to end.

## 6. Historical/forecast audit

Historical queries are chronologically ordered and do not gap-fill. Analytics
reports missing dates. Forecast preparation filters invalid values and sorts
chronologically. Walk-forward evaluation uses prior observations only and the
naive-last-value strategy remains the benchmark.

Unit tests cover chronological ordering, gaps, insufficient history, metrics,
and no-data behavior.

## 7. Economic engine audit

The formula ownership is coherent:

- Transport: `distance × quantity × rate` in `transport_cost.py`
- Decision: saleable quantity, gross revenue, spoilage loss, and net value in
  `decision_engine.py`
- Recommendation: ranking, relative opportunity score, and labels in
  `recommendation.py`
- Simulator: scenario economics, break-even, sensitivity, and robustness in
  `simulator.py`
- Evidence: evidence-quality score and confidence gates in `evidence.py`
- Data quality: readiness score and gates in `services/data_quality.py`

Recommendation calls the transport and decision engines rather than copying
their formulas. Simulator calls recommendation rather than duplicating ranking
logic.

## 8. Recommendation/evidence/simulator integration

The unified decision engine preserves separate fields for:

- economic opportunity
- evidence quality
- confidence classification
- robustness classification
- assumptions and limitations

Existing tests verify economic ranking independence from confidence and
deterministic simulator traces. The decision-intelligence route was hardened to
fetch all candidate histories in one query instead of issuing one historical
query per candidate.

## 9. Data-quality integration

The data-quality service reads `market_prices`, source metadata, ingestion runs,
and data-quality runs. It reports quality score/readiness separately from Stage
4 evidence/confidence. Empty-data behavior is explicit and does not fabricate
freshness, forecasts, or recommendations.

Real database integration could not be executed because PostgreSQL was
unavailable.

## 10. Frontend/backend contract audit

See [frontend_backend_contract_audit.md](frontend_backend_contract_audit.md).

The frontend files are all zero bytes in the audited workspace, so no actual
frontend API calls or response contracts exist to compare. Frontend integration
is therefore not validated.

## 11. Test-suite audit

Available runner: Python `unittest` discovery through the project virtualenv.

Results:

- Backend: 117 passed, 1 PostgreSQL integration test skipped
- ETL: 17 passed
- Total: 134 passed, 1 skipped

The suite contains substantial domain and ETL behavior tests. Existing API
coverage is primarily OpenAPI registration and direct route-function tests;
full HTTP TestClient checks could not run because the installed Starlette build
requires the missing `httpx2` package.

## 12. Security audit

Positive findings:

- `.env` is ignored and API keys are read from environment variables.
- Extract errors avoid exposing API keys.
- SQLAlchemy statements are parameterized.
- Official-file import requires explicit metadata and confirmation.
- Unknown references are rejected rather than created.

Finding `SEC-001` — LOW — A local ignored `.env` contains a database password.
It is not tracked or printed by this audit, but local secret rotation remains
the operator's responsibility.

## 13. Performance audit

Finding `PERF-001` — FIXED — Unified decision intelligence previously queried
historical prices once per candidate. It now performs one bounded multi-market
query and groups results in memory.

Remaining considerations:

- Data-quality summary intentionally scans selected market-price rows and
  reference tables for auditability.
- Large scenario grids are bounded by existing `MAX_SCENARIOS` controls.
- ORM relationship access can still issue lazy-load queries while formatting
  historical responses; this was not changed without a live database profile.

## 14. Configuration audit

Configuration names are consistent across `.env.example`, runtime settings,
ETL extraction, raw storage, and Alembic. No committed credential was found.
The local `.env` is ignored. PostgreSQL URL is loaded through `DATABASE_URL`.

The Alembic environment was hardened to load the same ignored `.env` file as
the application when available. Finding `CFG-001` — MEDIUM — PostgreSQL is
configured locally but unreachable, so runtime DB behavior and migration state
could not be verified against a live database.

## 15. Documentation audit

Stage documentation generally matches implementation, including explicit
no-data behavior, naive forecasting, provenance, simulator separation, and
data-quality/readiness distinctions.

The new audit documentation records the frontend gap and database-validation
blocker. No claims of real-government-data validation are made.

## 16. Critical findings

None found from static inspection and available tests.

## 17. High findings

`INT-001` — HIGH — End-to-end database integration is unverified because
PostgreSQL is unavailable. Impact: migrations, table counts, API DB paths, and
real ingestion persistence cannot be certified. Not fixed; requires a running
configured development PostgreSQL instance.

`INT-002` — HIGH — Frontend source files are empty. Impact: frontend/backend
contract compatibility cannot be demonstrated. Not fixed because frontend
modification is explicitly out of scope.

## 18. Medium findings

`CFG-001` — MEDIUM — Database connectivity unavailable. Not fixed.

`API-001` — MEDIUM — Full HTTP contract tests are unavailable because
`httpx2` is not installed. Direct import/OpenAPI/route tests pass. Not fixed;
environment dependency installation is outside the code change scope.

## 19. Low findings

`SEC-001` — LOW — Local ignored `.env` contains a password. Not fixed; no
secret was exposed or committed.

`API-002` — LOW — `decision_simulator.py` is an empty unused module while the
active route is `simulator.py`. Not fixed because removing or renaming it could
affect existing consumers.

## 20. Fixes performed

- Added `POST` to CORS allowed methods.
- Replaced per-candidate historical queries in unified decision intelligence
  with one multi-market query.
- Made Alembic load the same environment file used by the application.
- Added this system audit report.
- Added the frontend/backend contract audit report.

## 21. Remaining risks

- No live PostgreSQL verification.
- No real verified government data in the workspace.
- No real-data forecast or decision smoke test.
- No executable frontend contract.
- Full HTTP TestClient checks unavailable in the current environment.
- Local environment secret requires operator hygiene.

## 22. Recommended next steps

1. Start the intended development PostgreSQL instance.
2. Run Alembic current/upgrade checks against that explicitly identified
   development database.
3. Seed only reference commodities/markets.
4. Supply a verified AGMARKNET export and execute dry-run first.
5. Import only after dry-run approval, then run post-import quality,
   historical, forecast, and decision smoke tests.
6. Restore the frontend source and define its API contract.
7. Install the supported HTTP test client dependency in the development test
   environment.

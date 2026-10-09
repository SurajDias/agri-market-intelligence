# Stage 4.12 — Runtime Integration

## Scope and integrity rules

This stage connects the recovered React client to the existing FastAPI and
PostgreSQL runtime. No market-price rows, government records, CSV data, mock
API responses, or new ML/AI features were added.

## PostgreSQL and Alembic

| Check | Result | Evidence |
| --- | --- | --- |
| PostgreSQL cluster | GREEN | `16/main`, port 5432, online; `pg_isready -h localhost -p 5432` accepts connections |
| Application connection | GREEN | SQLAlchemy connected using the existing `.env`; metadata only was inspected, no credentials printed |
| Database | GREEN | `agri_market_db` |
| PostgreSQL version | GREEN | PostgreSQL 16.15 |
| SQL smoke checks | GREEN | `SELECT 1` succeeded |
| Alembic head | GREEN | `002_market_price_provenance` |
| Alembic upgrade | GREEN | `alembic upgrade head` completed with no pending migration |

The restricted non-elevated shell could not inspect the cluster data directory
or service manager, but the permitted local runtime context confirmed the
cluster online and accessible. No application fallback to SQLite was added.

Expected tables exist: `commodities`, `markets`, `market_prices`,
`data_sources`, `ingestion_runs`, and `data_quality_runs`.

Reference data is present:

- Commodities: Banana, Onion, Potato, Tomato
- Markets: Kolar, Mandya, Mysuru, Ramanagara
- `market_prices`: **0 rows**
- `data_sources`, `ingestion_runs`, `data_quality_runs`: 0 rows

No government data was imported.

## Live API verification

FastAPI started with `backend/venv/bin/uvicorn backend.main:app --host
127.0.0.1 --port 8000`. Real HTTP requests were executed against the running
server.

| Request | Status | Empty-data result |
| --- | ---: | --- |
| `GET /api/health` | 200 | Database connected |
| `GET /api/commodities` | 200 | Four reference commodities |
| `GET /api/markets` | 200 | Four reference markets |
| `GET /api/markets/{market_id}` | 200 | Reference market returned |
| `GET /api/markets/{market_id}/prices` | 200 | `[]` |
| `GET /api/historical-prices` | 200 | `[]` |
| `GET /api/historical-prices/coverage` | 200 | Zero observations and missing coverage dates |
| `GET /api/historical-prices/analytics` | 200 | Valid zero/insufficient-data analytics |
| `GET /api/forecasts/baseline` | 200 | `status: no_data`, empty forecast |
| `GET /api/forecasts/evaluate` | 200 | `status: insufficient_data`, null metrics |
| `GET /api/data-quality/summary` | 200 | `readiness: insufficient_data`, score 0 |
| `POST /api/transport/calculate` | 200 | Deterministic caller-supplied calculation |
| `POST /api/shelf-life/estimate` | 200 | Deterministic assumption-based calculation |
| `POST /api/decision/calculate` | 200 | Deterministic caller-supplied calculation |
| `POST /api/recommendations/analyze` | 200 | Uses only caller-supplied economics; not represented as measured market intelligence |
| `POST /api/evidence/assess` | 200 | `insufficient_evidence`, no observations |
| `POST /api/simulator/analyze` | 200 | Caller-supplied counterfactual; no historical data implied |
| `POST /api/decision-intelligence/analyze` | 200 | `final_decision.decision_status: insufficient_evidence`; historical availability false |

Validation requests for the POST routes also returned the expected 422 errors
for invalid or incomplete bodies. No price rows were created to make any
request pass.

## Frontend/backend contract alignment

The service layer uses canonical backend routes:

| Frontend request | Backend endpoint | Parameters/body | Response consumed | Status |
| --- | --- | --- | --- | --- |
| Market directory | `GET /api/markets` | optional state/district filters | market array | GREEN |
| Market prices | `GET /api/markets/{id}/prices` | `commodity_id`, `days` | price-record array | GREEN |
| Forecast | `GET /api/forecasts/baseline` | `commodity_id`, `market_id`, `horizon` | baseline response; no-data maps to `null` | GREEN |
| Data quality | `GET /api/data-quality/summary` | `reference_datetime` | summary transformed to UI type | GREEN |
| Simulator | `POST /api/simulator/analyze` | backend scenario request | simulator response | YELLOW: old UI input does not supply candidate economics; failed calls remain empty |
| Market comparison | no canonical endpoint | none | service returns `[]` | YELLOW: page remains honest empty state |

The obsolete frontend paths `/api/forecasts` and `/api/data-quality` were not
retained as duplicate backend aliases. The comparison page does not fabricate
prices, arrivals, transport costs, or forecast values. Existing backend
historical-price and analytics routes are sufficient for raw history and
coverage, but no existing route provides the page's complete aggregated
comparison/economics contract.

## Mock fallback audit

Removed or disabled from market-intelligence display paths:

- generated tomato history and random forecast points;
- static dashboard KPIs, recommendation cards, report insights, and trend data;
- synthetic simulator, comparison, forecast, and data-quality results.

The existing `frontend/src/services/mockData.ts` remains for static profile and
filter UI fixtures. Those values are not used as backend market observations.
The recovered pages preserve their visual structure and use the existing empty
state component when verified data is unavailable. The frontend therefore does
not claim actionable real-data intelligence in the empty database state.

## Build and runtime smoke checks

| Check | Result |
| --- | --- |
| Backend import/compile | GREEN (`compileall`) |
| Backend HTTP startup | GREEN |
| Frontend build | GREEN (`npm run build`; existing Vite bundle-size warning only) |
| Frontend dev server | GREEN; `/`, `/dashboard`, `/markets`, `/forecasts`, `/data-quality`, `/simulator`, `/opportunity-map`, and `/reports` served HTTP 200 |
| Browser-level interaction | YELLOW; no browser automation tool was available |

## Tests

Executed in the PostgreSQL-enabled runtime:

- Backend tests: **120 passed, 0 skipped**
- ETL tests: **17 passed, 0 skipped**
- Combined: **137 passed, 0 skipped**
- Frontend build: passed

A focused defect found during live integration was fixed in `etl/load.py`:
normalized lowercase state/district values are now matched case-insensitively
against canonical reference rows. The integration tests then passed in a
temporary PostgreSQL schema. The canonical database was rechecked afterward
and still contains zero market-price rows.

## Security and remaining limitations

- `.env` is ignored; credentials were not printed or added to frontend code.
- No API keys or database credentials are present in frontend source.
- SQLAlchemy queries remain parameterized; no unofficial government API was called.
- CORS remains restricted to the existing local frontend origins.
- No response exposed secrets during runtime checks.

Remaining limitations are the missing canonical market-comparison aggregation
contract, the simulator input-shape gap, and the absence of browser automation.
These are documented rather than bridged with duplicate routes or fabricated
data.

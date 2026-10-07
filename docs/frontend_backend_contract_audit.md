# Frontend/backend contract audit

## Result

The frontend source files exist but are empty in the audited workspace:

- `frontend/src/App.tsx`: 0 bytes
- `frontend/src/pages/CommodityTrends.tsx`: 0 bytes
- `frontend/src/pages/DataQuality.tsx`: 0 bytes
- `frontend/src/pages/DecisionSimulator.tsx`: 0 bytes
- `frontend/src/pages/ExecutiveOverview.tsx`: 0 bytes
- `frontend/src/pages/Forecasting.tsx`: 0 bytes
- `frontend/src/pages/MarketComparison.tsx`: 0 bytes
- `frontend/src/pages/OpportunityMap.tsx`: 0 bytes
- `frontend/src/pages/Reports.tsx`: 0 bytes
- `frontend/package.json`: 0 bytes

No frontend API calls, response assumptions, mock fallbacks, or query
parameters could therefore be discovered. There is no executable frontend
contract to validate.

| Frontend expectation | Backend implementation | Compatible? | Required future change |
| --- | --- | --- | --- |
| No source-level expectation available | `GET /api/commodities` | PARTIAL | Restore/implement frontend client before UI integration |
| No source-level expectation available | `GET /api/markets` | PARTIAL | Restore/implement frontend client before UI integration |
| No source-level expectation available | `GET /api/historical-prices` | PARTIAL | Restore/implement frontend client before UI integration |
| No source-level expectation available | `GET /api/forecasts/baseline` | PARTIAL | Restore/implement frontend client before UI integration |
| No source-level expectation available | `GET /api/data-quality/summary` | PARTIAL | Restore/implement frontend client with required `reference_datetime` |
| No source-level expectation available | Decision/recommendation/evidence/simulator endpoints | PARTIAL | Define frontend request/response contract |

Frontend files were not modified during this audit.

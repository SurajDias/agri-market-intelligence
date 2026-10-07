# Government price-data ingestion

The intended source is the official data.gov.in AGMARKNET resource
`9ef84268-d588-465a-a308-a864a43d0070`.

The current environment cannot reach `api.data.gov.in`, and no real government
market-price records have been imported into PostgreSQL. The API key must be
provided through `DATA_GOV_IN_API_KEY`; it must never be committed to the
repository.

Price units must be explicitly verified before ingestion. Set
`DATA_GOV_IN_PRICE_UNIT` only when the source unit is known. The transformer
rejects records with missing or unsupported units instead of assuming a unit.

## Historical price queries

The backend exposes `GET /api/historical-prices` for observed historical
records. It requires `commodity_id` and supports optional `market_id`, repeated
`market_ids`, `start_date`, and `end_date` filters. Results use canonical
INR/kg fields and are ordered by date, market, and record ID. The endpoint
queries PostgreSQL directly and returns no fabricated observations.

`GET /api/historical-prices/coverage` reports the requested range, observed
range, observation counts, expected calendar days, and missing calendar dates
using the same filters. Missing dates are reported, never gap-filled.

## Historical analytics

`GET /api/historical-prices/analytics` provides descriptive analytics for a
commodity with optional market and date filters. It reports coverage,
missing/invalid price quality counts, modal-price descriptive statistics,
percentage-change volatility, deterministic rising/falling/stable trend
classification, and per-market comparisons. These are historical descriptive
measurements only; they are not forecasts and do not train or load ML models.
When no observations exist, the endpoint returns null statistics, empty market
comparisons, and an `insufficient_data` trend.

## Baseline forecasting

`GET /api/forecasts/baseline` provides a transparent seven-day baseline using
the `naive_last_value` strategy. It uses the latest valid historical modal
price for each future date and accepts commodity, market, date-range, and
horizon filters. At least two valid observations are required; otherwise the
response is `no_data` or `insufficient_history` with an empty forecast.
Missing dates are reported and never filled. Confidence is not fabricated.

The forecasting service also provides MAE, RMSE, MAPE, and walk-forward
evaluation utilities. `GET /api/forecasts/evaluate` compares the registered
strategies for horizons from 1 to 30 days, including 1-, 3-, and 7-day
evaluation. Each prediction uses only observations before its chronological
evaluation origin; random splitting and missing-date filling are not used.

The only registered strategy is `naive_last_value`, which repeats the last
valid observed modal price. Results report observation counts, missing dates,
evaluated prediction counts, and metrics. MAPE excludes zero actual values and
is `null` when all actual values are zero. `best_strategy` is returned only
with sufficient evaluation data; otherwise the result is `insufficient_data`
and `best_strategy` is `null`.

No forecasting model has been validated against real government historical
data yet; the database currently contains no verified government market-price
records.

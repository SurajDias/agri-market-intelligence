# Evidence-backed confidence and auditable decision trace

`POST /api/evidence/assess` evaluates evidence quality for one commodity and
market. It is an evidence/readiness assessment, not a probability, statistical
confidence estimate, or opportunity score. The Stage 4.4 opportunity score is
not reused as confidence.

## Evidence flow

The API retrieves historical observations through the existing historical-price
service and passes them to the existing historical analytics service. The
engine records coverage, missing dates, price change, volatility, trend,
freshness, and optional evaluated forecast evidence. It accepts an explicit
reference datetime so freshness is reproducible and never uses the machine
clock in the core engine.

## Evidence-quality formula

The score is bounded from 0 to 100:

```text
score = historical_observations
      + calendar_coverage
      + freshness
      + forecast_evaluation
      + assumption_reliability
```

Component contributions are:

- Historical observations, maximum 25: 0 observations = 0; 1 = 5; 2–29 =
  15; 30 or more = 25.
- Calendar coverage, maximum 25: actual observed calendar coverage percentage
  multiplied by 25/100.
- Freshness, maximum 20: age 0–2 days = 20; 3–7 = 15; 8–30 = 8; older or
  unavailable = 0.
- Forecast evaluation, maximum 20: evaluated MAPE <=10 = 20; MAPE 10–25 =
  15; MAPE >25 = 5; evaluated with unavailable MAPE = 10; not evaluated = 0.
- Assumption reliability, maximum 10: starts at 10, with 2.5 points deducted
  for each recognized caller-supplied price, distance, transport-rate, or
  spoilage assumption flag.

These are transparent readiness rules, not calibrated probabilities.

## Critical gates and classification

`insufficient_evidence` overrides the numeric score when there are no
observations, fewer than two observations, no usable latest price, or calendar
coverage is unavailable or below 50%.

Otherwise classifications are:

- `high_confidence`: score >= 75
- `moderate_confidence`: score >= 50 and < 75
- `low_confidence`: score < 50
- `insufficient_evidence`: any critical gate fails

The word confidence here means evidence readiness only. It is not a
statistically calibrated probability.

## Provenance

Every evidence category is marked as one of:

- `measured_from_database`
- `calculated_from_database`
- `supplied_by_caller`
- `derived_from_forecast_evaluation`
- `unavailable`

Caller-provided economic context and assumptions cannot masquerade as measured
government data.

## Reasons, limitations, and trace

Reasons use deterministic codes including `strong_historical_coverage`,
`weak_historical_coverage`, `recent_observation`, `stale_observation`,
`forecast_evaluated`, `forecast_not_evaluated`, `low_forecast_error`,
`high_forecast_error`, `missing_dates`, `insufficient_history`,
`price_assumption`, `distance_assumption`, `transport_rate_assumption`,
`spoilage_assumption`, `negative_net_value`, `near_expiry`, and `expired`.

Limitations are returned explicitly, including stale data, missing dates,
unavailable forecast evaluation, caller assumptions, expired products, and
negative expected net value.

The decision trace contains decision context, supplied economic context,
historical evidence, freshness, forecast context, component scores, gates,
assumptions, limitations, and a deterministic explanation. Repeating the same
request with the same observations and reference datetime produces the same
trace.

## Relationship to Stage 4.4

Stage 4.4 economic ranking and opportunity scoring remain unchanged. This
endpoint is intentionally decoupled and can enrich recommendation candidates
later. A high opportunity score does not imply high evidence confidence.

No synthetic prices, forecasts, distances, or biological assumptions are
created. No external API, ML model, or LLM is used.

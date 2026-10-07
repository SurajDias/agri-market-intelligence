# Unified evidence-backed decision intelligence

`POST /api/decision-intelligence/analyze` composes the existing economic,
recommendation, evidence, and counterfactual engines into one stateless,
auditable pipeline.

## Architecture

```text
Request validation
      ↓
Historical observations from PostgreSQL
      ↓
Existing historical analytics + freshness
      ↓
Existing Stage 4.4 economic recommendation
      ↓
Existing Stage 4.5 evidence assessment per market
      ↓
Existing Stage 4.6 sensitivity and break-even simulation
      ↓
Unified candidates + data-quality summary
      ↓
Deterministic final decision + trace
```

The pipeline does not rewrite the underlying transport, decision, ranking,
opportunity, evidence, or simulator formulas.

## Decision hierarchy

1. Economic feasibility
2. Economic ranking by expected net value
3. Evidence availability
4. Evidence quality
5. Sensitivity and robustness
6. Final decision status

Opportunity, confidence, and robustness remain separate:

- Opportunity measures economic attractiveness.
- Confidence measures evidence/readiness.
- Robustness measures sensitivity to controlled assumption changes.

Confidence does not reorder economic candidates.

## Final decision statuses

- `no_opportunity`: no candidate markets were supplied.
- `economically_unfavorable`: candidates exist, but none has positive expected
  net value.
- `insufficient_evidence`: the economically recommended market fails a Stage
  4.5 critical evidence gate.
- `actionable`: positive economics, no critical evidence gate, and robustness
  is `robust` or `highly_robust`.
- `actionable_with_caution`: positive economics with low confidence or
  sensitive/indeterminate robustness.
- `evidence_limited`: reserved for positive economics that do not meet the
  stronger actionable rules.

## Evidence and forecast integration

Historical observations are retrieved server-side for every candidate and
passed to the existing historical analytics and Stage 4.5 evidence engine.
Freshness uses the explicit request `reference_datetime`.

Forecast evidence is optional. When evaluated forecast context is supplied,
strategy, horizon, MAE, RMSE, MAPE, evaluation count, and evaluation period are
returned. Otherwise `forecast_evidence_available` is false and
`forecast_not_evaluated` is surfaced as a limitation.

## Sensitivity and robustness integration

The existing Stage 4.6 simulator is called with the same candidate inputs.
Its scenario results, break-even thresholds, sensitivity summary, preservation
rate, margin ratio, and robustness classification are included without
changing their meaning.

## Provenance and trace

Major fields identify one of:

- `measured_from_database`
- `calculated_from_database`
- `supplied_by_caller`
- `derived_from_forecast_evaluation`
- `unavailable`

The unified trace contains request context, data evidence, economic analysis,
market ranking, confidence analysis, sensitivity analysis, robustness analysis,
final decision, assumptions, limitations, and provenance.

Reason codes include:

- Economic: `highest_expected_net_value`, `positive_expected_net_value`,
  `negative_expected_net_value`
- Evidence: `strong_historical_coverage`, `weak_historical_coverage`,
  `recent_observation`, `stale_observation`, `forecast_evaluated`,
  `forecast_not_evaluated`, `missing_dates`, `insufficient_history`
- Robustness: `recommendation_preserved`, `recommendation_changed`,
  `wide_net_margin`, `narrow_net_margin`, `robust_to_sensitivity`,
  `sensitive_to_price`
- Assumptions: `caller_supplied_price`, `caller_supplied_distance`,
  `caller_supplied_transport_rate`, `caller_supplied_spoilage`

Reasons are emitted only when supported by calculated values.

## Limitations

Prices, distances, transport rates, and spoilage values remain caller-supplied
assumptions. No external APIs, synthetic data, ML, or LLM explanations are
used. Empty PostgreSQL evidence produces explicit insufficient-evidence states;
it never fabricates confidence or completeness. Unified decisions are not
persisted yet.

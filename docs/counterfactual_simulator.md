# Counterfactual decision simulator

`POST /api/simulator/analyze` is a deterministic, stateless sensitivity layer
for the Stage 4.4 scenario-based recommendation engine. It answers controlled
questions such as “what if price falls 10%?” without changing the submitted
baseline.

## Reused engines and baseline

For the baseline and every scenario, the simulator calls the existing
recommendation engine. That engine calls the existing transport-cost and
decision-value engines. Transport, shelf-life, decision, ranking, and
opportunity-score formulas are not duplicated here. Caller-provided spoilage
and shelf-life status remain assumptions; the simulator does not invent them.

## Scenario formulas

For a percentage change:

```text
scenario_value = baseline_value × (1 + change_percent / 100)
```

Absolute overrides replace percentage changes. Supplying both forms for the
same variable is rejected. Supported variables are selling price, transport
rate, distance, and estimated spoilage. A scenario recalculates every
candidate, then compares rankings and recommendations with the immutable
baseline.

## Break-even formulas

For best market A versus competitor B, using baseline saleable quantity and
transport values:

```text
minimum_price_A = (net_B + transport_cost_A) / saleable_quantity_A
maximum_transport_cost_A = price_A × saleable_quantity_A - net_B
maximum_distance_A = maximum_transport_cost_A / (quantity × transport_rate_A)
maximum_spoilage_A = quantity - (net_B + transport_cost_A) / price_A
```

Thresholds are marked unavailable when a required denominator is zero or when
there is no positive baseline recommendation or competitor. They are
analytical equalization thresholds, not forecasts.

## Sensitivity and scenario grid

Sensitivity changes one absolute variable at a time and reports each value,
the resulting recommendation, net value, and first observed transition. An
optional `target_market_id` makes the change market-specific; without it the
same controlled value is applied to every candidate.
Scenario grids evaluate an explicitly requested Cartesian product. The maximum
is 100 scenarios; each grid or sensitivity variable accepts at most 20 values.
Random simulation and Monte Carlo are not used.

## Robustness

Robustness uses scenario recommendation preservation and baseline net-value
margin. Preservation rate is the percentage of requested scenarios retaining
the baseline recommendation. Baseline margin ratio is:

```text
(best_net_value - second_best_net_value) / abs(best_net_value)
```

Classification:

- `highly_robust`: preservation >=80% and margin >=20% (or no second market)
- `robust`: preservation >=60% or margin >=10%
- `sensitive`: preservation >0% but does not meet robust criteria
- `highly_sensitive`: preservation is 0%
- `indeterminate`: no positive baseline recommendation exists

These are economic sensitivity labels, not confidence classifications.

## Explanation and trace

Each scenario includes baseline/scenario inputs, changed variables, candidate
economic snapshots, absolute and percentage deltas, ranking before/after,
recommendation before/after, break-even analysis, robustness analysis,
assumptions, limitations, and a deterministic trace. Explanation codes include
`recommendation_preserved`, `recommendation_changed`,
`price_is_primary_driver`, `transport_is_primary_driver`, and
`spoilage_is_primary_driver`.

Forecasts, recommendations, sensitivity, break-even, robustness, and
confidence are distinct concepts. This endpoint does not alter Stage 4.5
evidence quality or confidence and does not claim statistical certainty.

## Limitations

All prices, distances, transport rates, and spoilage inputs are caller-supplied
scenario assumptions. No market price, distance, rate, forecast, or biological
value is fabricated. Results are temporary calculations and are not persisted.

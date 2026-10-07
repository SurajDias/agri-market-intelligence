# Explainable market opportunity and recommendation engine

`POST /api/recommendations/analyze` is a stateless, scenario-based market
recommendation calculation. It ranks caller-supplied destination markets for a
commodity and quantity. It is not an AI prediction, a probability, a
confidence score, or a validated guarantee of profit.

## Inputs and assumptions

The caller supplies the expected selling price, distance, transport rate, and
estimated spoilage for every candidate. An optional origin expected price is
accepted only to calculate price advantage; no origin price is invented. The
API validates the commodity, origin market, and candidate market identifiers,
but it does not retrieve prices or distances.

## Calculation basis

For every candidate, the engine reuses the existing transport-cost and
decision-value engines. Expected net value is based on:

```text
saleable quantity = quantity - estimated spoilage
gross revenue = expected price × saleable quantity
expected net value = gross revenue - transport cost
```

The candidate with the highest expected net value ranks first. Tie-breaking is
deterministic: expected net value descending, expected price descending,
transport cost ascending, then market ID ascending.

## Opportunity score

The score is a relative 0–100 reporting metric, not a probability or
confidence score. It is the equal-weight average of four transparent scores:

```text
net-value score = candidate net value / best positive net value × 100
price score = candidate price / highest candidate price × 100
transport score = 100 when all candidate transport costs are equal; otherwise
                  100 - candidate transport cost / highest transport cost × 100
spoilage score = 100 - spoilage percentage
opportunity score = average of the four scores
```

Scores are bounded to 0–100. With no positive net value, net-value scores are
0 for negative values and 100 for exactly zero; all candidates receive the
`avoid` label and no market is recommended.

## Recommendation labels

These are explicit decision-support heuristics, not scientifically validated
thresholds:

- `strong_opportunity`: score >= 80
- `opportunity`: score >= 60 and < 80
- `neutral`: score >= 40 and < 60
- `weak_opportunity`: score >= 20 and < 40
- `avoid`: score < 20, or all candidate net values are negative/non-positive
- `no_opportunity`: no candidates were supplied

## Explanations and flags

Each candidate receives deterministic positive and negative factors, a primary
reason, and assumption flags. Flags identify `price_assumption`,
`distance_assumption`, `transport_rate_assumption`, and `spoilage_assumption`,
plus `near_expiry`, `expired`, or `negative_net_value` where applicable.

The primary recommendation reason is based on calculated ranking, for example:
“Highest expected net value after transport and estimated spoilage.” No LLM or
natural-language generation is involved.

## Data categories and limitations

- Measured data: currently only the existence and names of validated database
  commodity/market references.
- User/scenario assumptions: prices, distances, transport rates, spoilage, and
  optional origin price.
- Derived metrics: transport cost, saleable quantity, revenue, spoilage loss,
  expected net value, ranking, and opportunity score.
- Heuristic decision labels: recommendation classifications and thresholds.

Real government market-price data is not currently available. The engine does
not retrieve forecasts, calculate distances, persist results, or claim that
recommendations have been validated against government data.

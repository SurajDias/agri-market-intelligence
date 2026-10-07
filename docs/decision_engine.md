# Decision-value calculation foundation

`POST /api/decision/calculate` is a stateless, deterministic calculation of
expected net value. It accepts the expected selling price from the caller and
does not retrieve prices, forecasts, transport distances, or shelf-life data.

The formulas are:

```text
saleable_quantity_kg = quantity_kg - estimated_spoilage_kg
gross_revenue = expected_selling_price_per_kg × saleable_quantity_kg
estimated_spoilage_loss_inr = estimated_spoilage_kg × expected_selling_price_per_kg
Expected Net Value = Expected Selling Price × Saleable Quantity − Transport Cost
```

Spoilage loss is reported for auditability but is not subtracted separately
from gross revenue because the saleable quantity already accounts for it. This
avoids subtracting spoilage twice.

All monetary calculations use Decimal arithmetic and are rounded only at the
final response boundary to two INR decimal places. Negative expected net value
is preserved and means the modeled sale is expected to lose money under the
provided assumptions.

Expected selling price is caller-provided because verified government market
price data is not currently available. No price or forecast is invented.

Example request:

```json
{
  "quantity_kg": 1000,
  "expected_selling_price_per_kg": 25,
  "transport_cost": 1200,
  "estimated_spoilage_kg": 50,
  "shelf_life_status": "viable"
}
```

This is a deterministic decision-value calculation, not a recommendation or
ranking engine. It does not implement risk, confidence, forecasting, market
ranking, or database persistence.

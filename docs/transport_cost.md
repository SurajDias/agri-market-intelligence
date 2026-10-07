# Transport cost foundation

`POST /api/transport/calculate` returns a transparent estimated transport cost
for a quantity moved between two existing market identifiers.

The exact formula is:

```text
transport_cost = distance_km × quantity_kg × transport_rate_per_km_per_kg
```

Units are kilometres, kilograms, and INR per kilometre per kilogram. The
caller must provide both `distance_km` and `transport_rate_per_km_per_kg`.
Distance is therefore an assumption supplied by the caller, not a value
calculated by this service. No Google Maps, OpenStreetMap, routing API, or
other external routing service is used. This is an estimated transport cost,
not a live logistics quotation.

Example request:

```json
{
  "origin_market_id": "origin",
  "destination_market_id": "destination",
  "quantity_kg": 1000,
  "distance_km": 50,
  "transport_rate_per_km_per_kg": 0.05
}
```

Example response:

```json
{
  "origin": "origin",
  "destination": "destination",
  "quantity_kg": 1000,
  "distance_km": 50,
  "transport_rate_per_km_per_kg": 0.05,
  "transport_cost": 2500.00,
  "currency": "INR"
}
```

Quantity must be greater than zero. Distance and rate may be zero but may not
be negative. The calculation uses Decimal arithmetic and rounds only the final
cost to two INR decimal places.

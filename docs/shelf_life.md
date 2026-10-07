# Shelf-life and spoilage estimation foundation

`POST /api/shelf-life/estimate` provides a deterministic, assumption-based
estimate for a quantity of produce during a caller-supplied transit window.
It does not require a commodity ID because the project does not currently have
a verified commodity-specific shelf-life or spoilage dataset.

Inputs use kilograms and days:

- `quantity_kg`: quantity being considered; must be greater than zero.
- `remaining_shelf_life_days`: estimated usable shelf life remaining at the
  time of the decision; must be non-negative.
- `transit_time_days`: estimated time before arrival at the destination or sale
  point; must be non-negative.
- `baseline_spoilage_rate_per_day`: caller-provided fractional loss per day,
  from 0 through 1.
- `handling_buffer_days`: optional non-negative input reserved for future
  handling assumptions; it is currently reported as an accepted input but does
  not alter the calculation.

The remaining shelf life is calculated as:

```text
remaining_after_transit = remaining_shelf_life_days - transit_time_days
```

Status rules are decision-support thresholds:

- `expired` when remaining after transit is less than 0.
- `near_expiry` when remaining after transit is between 0 and 1 day inclusive.
- `viable` when remaining after transit is greater than 1 day.

Estimated spoilage uses the transparent linear assumption:

```text
spoilage_fraction = baseline_spoilage_rate_per_day × transit_time_days
estimated_spoilage_kg = quantity_kg × min(spoilage_fraction, 1)
estimated_remaining_quantity_kg = quantity_kg - estimated_spoilage_kg
```

The current implementation is an assumption-based decision-support estimate,
not a validated biological spoilage model. It does not claim to model real
biological spoilage kinetics, and it does not hardcode commodity-specific
values.

Example request:

```json
{
  "quantity_kg": 1000,
  "remaining_shelf_life_days": 5,
  "transit_time_days": 2,
  "baseline_spoilage_rate_per_day": 0.03
}
```

Example response:

```json
{
  "quantity_kg": 1000,
  "remaining_shelf_life_days": 5,
  "transit_time_days": 2,
  "remaining_shelf_life_after_transit_days": 3,
  "baseline_spoilage_rate_per_day": 0.03,
  "estimated_spoilage_fraction": 0.06,
  "estimated_spoilage_kg": 60,
  "estimated_remaining_quantity_kg": 940,
  "shelf_life_status": "viable",
  "assumption_note": "Spoilage is an assumption-based linear estimate..."
}
```

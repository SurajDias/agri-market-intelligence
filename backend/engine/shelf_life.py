from decimal import Decimal
from typing import Literal


ShelfLifeStatus = Literal["viable", "near_expiry", "expired"]
ASSUMPTION_NOTE = (
    "Spoilage is an assumption-based linear estimate using caller-provided "
    "shelf-life, transit-time, and baseline spoilage-rate inputs; it is not a "
    "validated biological spoilage model."
)


def estimate_shelf_life(
    quantity_kg: Decimal,
    remaining_shelf_life_days: Decimal,
    transit_time_days: Decimal,
    baseline_spoilage_rate_per_day: Decimal,
    handling_buffer_days: Decimal | None = None,
) -> dict[str, Decimal | str]:
    """Estimate usable quantity and shelf-life status from caller assumptions."""
    if quantity_kg <= 0:
        raise ValueError("quantity_kg must be greater than zero")
    if remaining_shelf_life_days < 0:
        raise ValueError("remaining_shelf_life_days must be non-negative")
    if transit_time_days < 0:
        raise ValueError("transit_time_days must be non-negative")
    if baseline_spoilage_rate_per_day < 0 or baseline_spoilage_rate_per_day > 1:
        raise ValueError("baseline_spoilage_rate_per_day must be between 0 and 1")
    if handling_buffer_days is not None and handling_buffer_days < 0:
        raise ValueError("handling_buffer_days must be non-negative")

    remaining_after_transit = remaining_shelf_life_days - transit_time_days
    if remaining_after_transit < 0:
        status: ShelfLifeStatus = "expired"
    elif remaining_after_transit <= 1:
        status = "near_expiry"
    else:
        status = "viable"

    spoilage_fraction = baseline_spoilage_rate_per_day * transit_time_days
    if spoilage_fraction > 1:
        spoilage_fraction = Decimal("1")
    estimated_spoilage = quantity_kg * spoilage_fraction

    result: dict[str, Decimal | str] = {
        "quantity_kg": quantity_kg,
        "remaining_shelf_life_days": remaining_shelf_life_days,
        "transit_time_days": transit_time_days,
        "remaining_shelf_life_after_transit_days": remaining_after_transit,
        "baseline_spoilage_rate_per_day": baseline_spoilage_rate_per_day,
        "estimated_spoilage_fraction": spoilage_fraction,
        "estimated_spoilage_kg": estimated_spoilage,
        "estimated_remaining_quantity_kg": quantity_kg - estimated_spoilage,
        "shelf_life_status": status,
        "assumption_note": ASSUMPTION_NOTE,
    }
    return result

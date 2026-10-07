from decimal import Decimal, ROUND_HALF_UP
from typing import Literal


MONEY_QUANTUM = Decimal("0.01")
FORMULA = "Expected Net Value = Expected Price × Saleable Quantity − Transport Cost"
ShelfLifeStatus = Literal["viable", "near_expiry", "expired"]


def _money(value: Decimal) -> Decimal:
    """Round only final monetary values to INR paise."""
    return value.quantize(MONEY_QUANTUM, rounding=ROUND_HALF_UP)


def calculate_expected_net_value(
    quantity_kg: Decimal,
    expected_selling_price_per_kg: Decimal,
    transport_cost: Decimal,
    estimated_spoilage_kg: Decimal,
    shelf_life_status: ShelfLifeStatus | None = None,
) -> dict[str, object]:
    """Calculate expected net value from caller-provided decision inputs."""
    if quantity_kg <= 0:
        raise ValueError("quantity_kg must be greater than zero")
    if expected_selling_price_per_kg < 0:
        raise ValueError("expected_selling_price_per_kg must be non-negative")
    if transport_cost < 0:
        raise ValueError("transport_cost must be non-negative")
    if estimated_spoilage_kg < 0:
        raise ValueError("estimated_spoilage_kg must be non-negative")
    if estimated_spoilage_kg > quantity_kg:
        raise ValueError("estimated_spoilage_kg must not exceed quantity_kg")

    saleable_quantity = quantity_kg - estimated_spoilage_kg
    gross_revenue = _money(expected_selling_price_per_kg * saleable_quantity)
    spoilage_loss = _money(expected_selling_price_per_kg * estimated_spoilage_kg)
    expected_net_value = _money(gross_revenue - transport_cost)
    net_value_per_original_kg = _money(expected_net_value / quantity_kg)
    spoilage_percentage = (estimated_spoilage_kg / quantity_kg) * Decimal("100")

    explanation = {
        "original_quantity_kg": quantity_kg,
        "spoilage_quantity_kg": estimated_spoilage_kg,
        "saleable_quantity_kg": saleable_quantity,
        "expected_price_per_kg": expected_selling_price_per_kg,
        "gross_revenue": gross_revenue,
        "transport_cost": _money(transport_cost),
        "estimated_spoilage_loss_inr": spoilage_loss,
        "expected_net_value": expected_net_value,
        "formula": FORMULA,
    }
    return {
        "quantity_kg": quantity_kg,
        "estimated_spoilage_kg": estimated_spoilage_kg,
        "saleable_quantity_kg": saleable_quantity,
        "expected_selling_price_per_kg": expected_selling_price_per_kg,
        "gross_revenue": gross_revenue,
        "estimated_spoilage_loss_inr": spoilage_loss,
        "transport_cost": _money(transport_cost),
        "expected_net_value": expected_net_value,
        "net_value_per_original_kg": net_value_per_original_kg,
        "spoilage_percentage": spoilage_percentage,
        "shelf_life_status": shelf_life_status,
        "explanation": explanation,
    }

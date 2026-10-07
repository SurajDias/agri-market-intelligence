from decimal import Decimal, ROUND_HALF_UP


MONEY_QUANTUM = Decimal("0.01")


def calculate_transport_cost(
    origin: str,
    destination: str,
    quantity_kg: Decimal,
    distance_km: Decimal,
    transport_rate_per_km_per_kg: Decimal,
) -> dict[str, Decimal | str]:
    """Calculate an estimated transport cost from caller-provided inputs.

    Distance is an assumed distance in kilometres, not a routed road distance.
    The final cost is expressed to the nearest INR paise; intermediate
    multiplication remains Decimal arithmetic without rounding.
    """
    if quantity_kg <= 0:
        raise ValueError("quantity_kg must be greater than zero")
    if distance_km < 0:
        raise ValueError("distance_km must be non-negative")
    if transport_rate_per_km_per_kg < 0:
        raise ValueError("transport_rate_per_km_per_kg must be non-negative")

    cost = (
        distance_km * quantity_kg * transport_rate_per_km_per_kg
    ).quantize(MONEY_QUANTUM, rounding=ROUND_HALF_UP)
    return {
        "origin": origin,
        "destination": destination,
        "quantity_kg": quantity_kg,
        "distance_km": distance_km,
        "transport_rate_per_km_per_kg": transport_rate_per_km_per_kg,
        "transport_cost": cost,
        "currency": "INR",
    }

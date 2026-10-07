from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class TransportCostRequest(BaseModel):
    origin_market_id: str
    destination_market_id: str
    quantity_kg: Decimal = Field(gt=0)
    distance_km: Decimal = Field(ge=0)
    transport_rate_per_km_per_kg: Decimal = Field(ge=0)


class TransportCostResponse(BaseModel):
    origin: str
    destination: str
    quantity_kg: Decimal
    distance_km: Decimal
    transport_rate_per_km_per_kg: Decimal
    transport_cost: Decimal
    currency: Literal["INR"] = "INR"

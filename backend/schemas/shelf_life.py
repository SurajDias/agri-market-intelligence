from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class ShelfLifeEstimateRequest(BaseModel):
    quantity_kg: Decimal = Field(gt=0)
    remaining_shelf_life_days: Decimal = Field(ge=0)
    transit_time_days: Decimal = Field(ge=0)
    baseline_spoilage_rate_per_day: Decimal = Field(ge=0, le=1)
    handling_buffer_days: Decimal | None = Field(default=None, ge=0)


class ShelfLifeEstimateResponse(BaseModel):
    quantity_kg: Decimal
    remaining_shelf_life_days: Decimal
    transit_time_days: Decimal
    remaining_shelf_life_after_transit_days: Decimal
    baseline_spoilage_rate_per_day: Decimal
    estimated_spoilage_fraction: Decimal
    estimated_spoilage_kg: Decimal
    estimated_remaining_quantity_kg: Decimal
    shelf_life_status: Literal["viable", "near_expiry", "expired"]
    assumption_note: str

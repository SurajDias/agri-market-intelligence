from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, model_validator


ShelfLifeStatus = Literal["viable", "near_expiry", "expired"]


class DecisionValueRequest(BaseModel):
    quantity_kg: Decimal = Field(gt=0)
    expected_selling_price_per_kg: Decimal = Field(ge=0)
    transport_cost: Decimal = Field(ge=0)
    estimated_spoilage_kg: Decimal = Field(ge=0)
    shelf_life_status: ShelfLifeStatus | None = None

    @model_validator(mode="after")
    def validate_spoilage_quantity(self):
        if self.estimated_spoilage_kg > self.quantity_kg:
            raise ValueError("estimated_spoilage_kg must not exceed quantity_kg")
        return self


class DecisionExplanation(BaseModel):
    original_quantity_kg: Decimal
    spoilage_quantity_kg: Decimal
    saleable_quantity_kg: Decimal
    expected_price_per_kg: Decimal
    gross_revenue: Decimal
    transport_cost: Decimal
    estimated_spoilage_loss_inr: Decimal
    expected_net_value: Decimal
    formula: str


class DecisionValueResponse(BaseModel):
    quantity_kg: Decimal
    estimated_spoilage_kg: Decimal
    saleable_quantity_kg: Decimal
    expected_selling_price_per_kg: Decimal
    gross_revenue: Decimal
    estimated_spoilage_loss_inr: Decimal
    transport_cost: Decimal
    expected_net_value: Decimal
    net_value_per_original_kg: Decimal
    spoilage_percentage: Decimal
    shelf_life_status: ShelfLifeStatus | None
    explanation: DecisionExplanation

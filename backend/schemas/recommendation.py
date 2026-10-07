from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, model_validator


ShelfLifeStatus = Literal["viable", "near_expiry", "expired"]
RecommendationLabel = Literal[
    "strong_opportunity", "opportunity", "neutral", "weak_opportunity", "avoid", "no_opportunity"
]


class RecommendationCandidateRequest(BaseModel):
    market_id: str
    expected_selling_price_per_kg: Decimal = Field(ge=0)
    distance_km: Decimal = Field(ge=0)
    transport_rate_per_km_per_kg: Decimal = Field(ge=0)
    estimated_spoilage_kg: Decimal = Field(ge=0)
    shelf_life_status: ShelfLifeStatus | None = None


class RecommendationRequest(BaseModel):
    commodity_id: str
    origin_market_id: str
    quantity_kg: Decimal = Field(gt=0)
    origin_expected_selling_price_per_kg: Decimal | None = Field(default=None, ge=0)
    candidates: list[RecommendationCandidateRequest]

    @model_validator(mode="after")
    def validate_candidates(self):
        market_ids = [candidate.market_id for candidate in self.candidates]
        if len(market_ids) != len(set(market_ids)):
            raise ValueError("candidate market IDs must be unique")
        for candidate in self.candidates:
            if candidate.estimated_spoilage_kg > self.quantity_kg:
                raise ValueError("estimated_spoilage_kg must not exceed quantity_kg")
        return self


class RecommendationExplanation(BaseModel):
    positive_factors: list[str]
    negative_factors: list[str]
    primary_reason: str


class RankedCandidate(BaseModel):
    rank: int
    market_id: str
    market_name: str
    expected_selling_price_per_kg: Decimal
    quantity_kg: Decimal
    transport_cost: Decimal
    estimated_spoilage_kg: Decimal
    saleable_quantity_kg: Decimal
    gross_revenue: Decimal
    estimated_spoilage_loss_inr: Decimal
    expected_net_value: Decimal
    net_value_per_original_kg: Decimal
    spoilage_percentage: Decimal
    price_advantage_vs_origin: Decimal | None
    shelf_life_status: ShelfLifeStatus | None
    opportunity_score: Decimal
    recommendation_label: RecommendationLabel
    positive_factors: list[str]
    negative_factors: list[str]
    primary_reason: str
    assumption_flags: list[str]
    explanation: RecommendationExplanation


class RecommendationResponse(BaseModel):
    commodity_id: str
    origin_market_id: str
    quantity_kg: Decimal
    recommended_market_id: str | None
    recommended_market_name: str | None
    recommendation_label: RecommendationLabel
    opportunity_score: Decimal | None
    expected_net_value: Decimal | None
    primary_reason: str
    ranked_candidates: list[RankedCandidate]

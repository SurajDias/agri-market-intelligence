from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from backend.schemas.evidence import ForecastEvaluationContext
from backend.schemas.simulator import (
    ScenarioGrid,
    ScenarioDefinition,
    SensitivityConfig,
)


class IntelligenceCandidateRequest(BaseModel):
    market_id: str
    expected_selling_price_per_kg: Decimal = Field(ge=0)
    distance_km: Decimal = Field(ge=0)
    transport_rate_per_km_per_kg: Decimal = Field(ge=0)
    estimated_spoilage_kg: Decimal = Field(ge=0)
    shelf_life_status: Literal["viable", "near_expiry", "expired"] | None = None
    forecast_evaluation: ForecastEvaluationContext | None = None


class DecisionIntelligenceRequest(BaseModel):
    commodity_id: str
    origin_market_id: str
    quantity_kg: Decimal = Field(gt=0)
    start_date: date
    end_date: date
    reference_datetime: datetime
    candidates: list[IntelligenceCandidateRequest]
    forecast_evaluation: ForecastEvaluationContext | None = None
    scenario: ScenarioDefinition | None = None
    scenario_grid: ScenarioGrid | None = None
    sensitivity: SensitivityConfig | None = None

    @model_validator(mode="after")
    def validate_request(self):
        if self.start_date > self.end_date:
            raise ValueError("start_date must not be after end_date")
        market_ids = [candidate.market_id for candidate in self.candidates]
        if len(market_ids) != len(set(market_ids)):
            raise ValueError("candidate market IDs must be unique")
        if self.scenario is not None and self.scenario_grid is not None:
            raise ValueError("scenario and scenario_grid cannot both be supplied")
        for candidate in self.candidates:
            if candidate.estimated_spoilage_kg > self.quantity_kg:
                raise ValueError("estimated_spoilage_kg must not exceed quantity_kg")
        return self


class UnifiedCandidate(BaseModel):
    market_id: str
    market_name: str
    commodity_id: str
    expected_selling_price_per_kg: Decimal
    quantity_kg: Decimal
    transport_cost: Decimal
    estimated_spoilage_kg: Decimal
    saleable_quantity_kg: Decimal
    gross_revenue: Decimal
    estimated_spoilage_loss_inr: Decimal
    expected_net_value: Decimal
    net_value_per_original_kg: Decimal
    opportunity_score: Decimal
    recommendation_label: str
    ranking_position: int
    observation_count: int
    first_observation_date: date | None
    last_observation_date: date | None
    coverage_percent: Decimal | None
    missing_date_count: int
    freshness_age_days: int | None
    historical_trend: str
    volatility: Decimal | None
    forecast_evidence_available: bool
    forecast_strategy: str | None
    forecast_horizon: int | None
    forecast_mae: Decimal | None
    forecast_rmse: Decimal | None
    forecast_mape: Decimal | None
    forecast_evaluation_observations: int
    evidence_quality_score: Decimal
    confidence_classification: str
    evidence_reasons: list[dict]
    limitations: list[str]
    robustness_classification: str
    preservation_rate: Decimal | None
    margin_ratio: Decimal | None
    break_even_analysis: dict
    sensitivity_summary: dict
    shelf_life_status: str | None
    provenance: dict[str, str]


class DataQualitySummary(BaseModel):
    historical_data_available: bool
    observation_count: int
    coverage_percent: Decimal | None
    missing_date_count: int
    latest_observation_date: date | None
    freshness_age_days: int | None
    forecast_evidence_available: bool
    critical_data_issues: list[str]
    assumptions_count: int
    limitations_count: int


class FinalDecision(BaseModel):
    recommended_market: str | None
    economic_recommendation: str | None
    opportunity_score: Decimal | None
    confidence_classification: str
    robustness_classification: str
    decision_status: Literal[
        "actionable",
        "actionable_with_caution",
        "evidence_limited",
        "economically_unfavorable",
        "no_opportunity",
        "insufficient_evidence",
    ]
    expected_net_value: Decimal | None
    decision_reasons: list[str]


class DecisionIntelligenceResponse(BaseModel):
    request_context: dict
    candidates: list[UnifiedCandidate]
    ranking: list[str]
    data_quality_summary: DataQualitySummary
    final_decision: FinalDecision
    assumptions: list[str]
    limitations: list[str]
    provenance: dict[str, str]
    decision_trace: dict

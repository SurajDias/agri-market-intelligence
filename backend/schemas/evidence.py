from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, model_validator


Provenance = Literal[
    "measured_from_database",
    "calculated_from_database",
    "supplied_by_caller",
    "derived_from_forecast_evaluation",
    "unavailable",
]


class ForecastEvaluationContext(BaseModel):
    strategy_name: str | None = None
    horizon: int | None = Field(default=None, ge=1)
    evaluated: bool = False
    mae: Decimal | None = Field(default=None, ge=0)
    rmse: Decimal | None = Field(default=None, ge=0)
    mape: Decimal | None = Field(default=None, ge=0)
    evaluation_observation_count: int = Field(default=0, ge=0)
    evaluation_start_date: date | None = None
    evaluation_end_date: date | None = None

    @model_validator(mode="after")
    def validate_evaluation(self):
        if self.evaluated and (not self.strategy_name or self.evaluation_observation_count < 1):
            raise ValueError("evaluated forecast evidence requires strategy_name and observations")
        return self


class DecisionEvidenceContext(BaseModel):
    origin_market_id: str | None = None
    destination_market_id: str | None = None
    quantity_kg: Decimal | None = Field(default=None, gt=0)
    expected_selling_price_per_kg: Decimal | None = Field(default=None, ge=0)
    transport_cost: Decimal | None = Field(default=None, ge=0)
    estimated_spoilage_kg: Decimal | None = Field(default=None, ge=0)
    expected_net_value: Decimal | None = None
    opportunity_score: Decimal | None = Field(default=None, ge=0, le=100)
    shelf_life_status: Literal["viable", "near_expiry", "expired"] | None = None
    assumption_flags: list[str] = Field(default_factory=list)


class EvidenceAssessmentRequest(BaseModel):
    commodity_id: str
    market_id: str
    start_date: date
    end_date: date
    reference_datetime: datetime
    forecast_evaluation: ForecastEvaluationContext | None = None
    decision_context: DecisionEvidenceContext | None = None

    @model_validator(mode="after")
    def validate_dates(self):
        if self.start_date > self.end_date:
            raise ValueError("start_date must not be after end_date")
        return self


class EvidenceComponent(BaseModel):
    name: str
    value: Decimal
    maximum_contribution: Decimal
    explanation: str


class EvidenceReason(BaseModel):
    code: str
    severity: Literal["positive", "negative", "limitation"]
    message: str


class EvidenceAssessmentResponse(BaseModel):
    commodity_id: str
    market_id: str
    first_observation_date: date | None
    last_observation_date: date | None
    observation_count: int
    calendar_coverage_percent: Decimal | None
    missing_date_count: int
    missing_dates: list[date]
    price_change_percent: Decimal | None
    price_volatility_measure: Decimal | None
    trend: str
    freshness_age_days: int | None
    forecast_evidence_available: bool
    forecast_strategy_name: str | None
    forecast_horizon: int | None
    forecast_mae: Decimal | None
    forecast_rmse: Decimal | None
    forecast_mape: Decimal | None
    forecast_evaluation_observation_count: int
    evidence_quality_score: Decimal
    confidence_classification: Literal[
        "high_confidence", "moderate_confidence", "low_confidence", "insufficient_evidence"
    ]
    critical_gates: list[str]
    components: list[EvidenceComponent]
    evidence_reasons: list[EvidenceReason]
    limitations: list[str]
    provenance: dict[str, Provenance]
    decision_trace: dict

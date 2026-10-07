from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, model_validator


MAX_SCENARIOS = 100
MAX_SENSITIVITY_VALUES = 20


class SimulatorCandidateRequest(BaseModel):
    market_id: str
    expected_selling_price_per_kg: Decimal = Field(ge=0)
    distance_km: Decimal = Field(ge=0)
    transport_rate_per_km_per_kg: Decimal = Field(ge=0)
    estimated_spoilage_kg: Decimal = Field(ge=0)
    shelf_life_status: Literal["viable", "near_expiry", "expired"] | None = None


class ScenarioDefinition(BaseModel):
    scenario_id: str | None = None
    scenario_description: str | None = None
    target_market_id: str | None = None
    price_change_percent: Decimal | None = None
    transport_rate_change_percent: Decimal | None = None
    distance_change_percent: Decimal | None = None
    spoilage_change_percent: Decimal | None = None
    expected_selling_price_per_kg: Decimal | None = Field(default=None, ge=0)
    distance_km: Decimal | None = Field(default=None, ge=0)
    transport_rate_per_km_per_kg: Decimal | None = Field(default=None, ge=0)
    estimated_spoilage_kg: Decimal | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_overrides(self):
        pairs = (
            ("price_change_percent", "expected_selling_price_per_kg"),
            ("distance_change_percent", "distance_km"),
            ("transport_rate_change_percent", "transport_rate_per_km_per_kg"),
            ("spoilage_change_percent", "estimated_spoilage_kg"),
        )
        for percentage, absolute in pairs:
            percentage_value = getattr(self, percentage)
            if percentage_value is not None and not Decimal("-100") <= percentage_value <= Decimal("1000"):
                raise ValueError(f"{percentage} must be between -100 and 1000")
            if percentage_value is not None and getattr(self, absolute) is not None:
                raise ValueError(f"{percentage} and {absolute} cannot both be supplied")
        return self


class ScenarioGrid(BaseModel):
    price_change_percent: list[Decimal] = Field(default_factory=list)
    transport_rate_change_percent: list[Decimal] = Field(default_factory=list)
    distance_change_percent: list[Decimal] = Field(default_factory=list)
    spoilage_change_percent: list[Decimal] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_grid(self):
        for field in type(self).model_fields:
            values = getattr(self, field)
            if len(values) > MAX_SENSITIVITY_VALUES:
                raise ValueError(f"{field} cannot contain more than {MAX_SENSITIVITY_VALUES} values")
            if any(value < -100 or value > 1000 for value in values):
                raise ValueError(f"{field} values must be between -100 and 1000")
        return self


class SensitivityConfig(BaseModel):
    target_market_id: str | None = None
    price_values: list[Decimal] = Field(default_factory=list)
    transport_rate_values: list[Decimal] = Field(default_factory=list)
    distance_values: list[Decimal] = Field(default_factory=list)
    spoilage_values: list[Decimal] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_values(self):
        for field in ("price_values", "transport_rate_values", "distance_values", "spoilage_values"):
            values = getattr(self, field)
            if len(values) > MAX_SENSITIVITY_VALUES:
                raise ValueError(f"{field} cannot contain more than {MAX_SENSITIVITY_VALUES} values")
            if any(value < 0 for value in values):
                raise ValueError(f"{field} values cannot be negative")
        return self


class SimulatorRequest(BaseModel):
    commodity_id: str
    origin_market_id: str
    quantity_kg: Decimal = Field(gt=0)
    candidates: list[SimulatorCandidateRequest]
    scenario: ScenarioDefinition | None = None
    scenario_grid: ScenarioGrid | None = None
    sensitivity: SensitivityConfig | None = None

    @model_validator(mode="after")
    def validate_request(self):
        market_ids = [candidate.market_id for candidate in self.candidates]
        if len(market_ids) != len(set(market_ids)):
            raise ValueError("candidate market IDs must be unique")
        for candidate in self.candidates:
            if candidate.estimated_spoilage_kg > self.quantity_kg:
                raise ValueError("estimated_spoilage_kg must not exceed quantity_kg")
        if self.scenario is not None and self.scenario_grid is not None:
            raise ValueError("scenario and scenario_grid cannot both be supplied")
        if self.scenario is not None and self.scenario.target_market_id is not None and self.scenario.target_market_id not in market_ids:
            raise ValueError("scenario target_market_id must identify a candidate market")
        if self.sensitivity is not None and self.sensitivity.target_market_id is not None and self.sensitivity.target_market_id not in market_ids:
            raise ValueError("sensitivity target_market_id must identify a candidate market")
        return self


class EconomicSnapshot(BaseModel):
    market_id: str
    market_name: str
    expected_selling_price_per_kg: Decimal
    distance_km: Decimal
    transport_rate_per_km_per_kg: Decimal
    quantity_kg: Decimal
    transport_cost: Decimal
    estimated_spoilage_kg: Decimal
    saleable_quantity_kg: Decimal
    gross_revenue: Decimal
    estimated_spoilage_loss_inr: Decimal
    expected_net_value: Decimal
    net_value_per_original_kg: Decimal
    spoilage_percentage: Decimal
    shelf_life_status: str | None


class ScenarioCandidateResult(BaseModel):
    market_id: str
    market_name: str
    baseline: EconomicSnapshot
    scenario: EconomicSnapshot
    absolute_changes: dict[str, Decimal]
    percentage_changes: dict[str, Decimal | None]


class ScenarioResult(BaseModel):
    scenario_id: str
    scenario_description: str
    baseline_recommended_market: str | None
    scenario_recommended_market: str | None
    recommendation_changed: bool
    ranking_before: list[str]
    ranking_after: list[str]
    candidates: list[ScenarioCandidateResult]
    break_even_analysis: dict
    robustness_analysis: dict
    explanations: list[str]
    assumptions: list[str]
    limitations: list[str]
    trace: dict


class SimulatorResponse(BaseModel):
    commodity_id: str
    origin_market_id: str
    quantity_kg: Decimal
    baseline_recommended_market: str | None
    baseline_ranking: list[str]
    scenarios: list[ScenarioResult]
    sensitivity: dict
    robustness_analysis: dict

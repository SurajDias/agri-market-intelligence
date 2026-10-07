from datetime import date
from typing import Literal

from pydantic import BaseModel


ForecastStatus = Literal["sufficient_history", "insufficient_history", "no_data"]


class ForecastPoint(BaseModel):
    forecast_date: date
    predicted_price_per_kg: float


class BaselineForecastResponse(BaseModel):
    commodity_id: str
    market_id: str
    model: str
    status: ForecastStatus
    reason: str | None
    confidence: float | None
    forecast: list[ForecastPoint]
    historical_observation_count: int
    training_start_date: date | None
    training_end_date: date | None
    latest_observed_price_per_kg: float | None
    historical_gap_dates: list[date]


class EvaluationMetrics(BaseModel):
    status: Literal["sufficient_data", "insufficient_data"]
    observation_count: int
    mae: float | None
    rmse: float | None
    mape: float | None


class WalkForwardEvaluationResponse(BaseModel):
    status: Literal["sufficient_data", "insufficient_data"]
    evaluation_count: int
    metrics: EvaluationMetrics


class StrategyEvaluationResponse(BaseModel):
    model: str
    status: Literal["sufficient_data", "insufficient_data"]
    evaluation_count: int
    metrics: EvaluationMetrics


class EvaluationDateRangeResponse(BaseModel):
    start_date: date
    end_date: date


class ForecastEvaluationResponse(BaseModel):
    commodity: str
    market: str
    evaluation_date_range: EvaluationDateRangeResponse
    horizon: int
    strategies: list[StrategyEvaluationResponse]
    best_strategy: str | None
    status: Literal["sufficient_data", "insufficient_data"]
    insufficient_data: bool
    observation_count: int
    valid_observation_count: int
    invalid_price_count: int
    missing_dates: list[date]
    evaluated_prediction_count: int

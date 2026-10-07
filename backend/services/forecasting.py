from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from math import isnan, sqrt
from statistics import mean, pstdev
from typing import Any, Callable, Iterable, Protocol, Sequence

from sqlalchemy.orm import Session

from backend.services.historical_prices import get_historical_prices


MODEL_NAME = "naive_last_value"
MIN_HISTORY_OBSERVATIONS = 2


@dataclass(frozen=True)
class PreparedObservation:
    observation_date: date
    price_per_kg: float


@dataclass(frozen=True)
class PreparedHistory:
    observations: list[PreparedObservation]
    raw_observation_count: int
    invalid_price_count: int
    missing_dates: list[date]


@dataclass(frozen=True)
class StrategyForecast:
    """Common result returned by a forecasting strategy."""

    values: list[float]
    model_name: str
    status: str


class ForecastStrategy(Protocol):
    model_name: str

    def forecast(self, observations: Sequence[float], horizon: int) -> StrategyForecast:
        """Forecast the next ``horizon`` values from chronological observations."""


class NaiveLastValueStrategy:
    model_name = MODEL_NAME

    def forecast(self, observations: Sequence[float], horizon: int) -> StrategyForecast:
        if not observations:
            return StrategyForecast([], self.model_name, "no_data")
        if len(observations) < MIN_HISTORY_OBSERVATIONS:
            return StrategyForecast([], self.model_name, "insufficient_history")
        return StrategyForecast([float(observations[-1])] * horizon, self.model_name, "sufficient_history")


REGISTERED_STRATEGIES: dict[str, ForecastStrategy] = {
    MODEL_NAME: NaiveLastValueStrategy(),
}


def _numeric_price(observation: Any) -> float | None:
    value = getattr(observation, "modal_price_inr_per_kg", None)
    if value is None:
        return None
    try:
        converted = float(value)
    except (TypeError, ValueError):
        return None
    if isnan(converted) or converted < 0:
        return None
    return converted


def prepare_history(observations: Iterable[Any]) -> PreparedHistory:
    """Sort observations and retain only valid modal prices explicitly."""
    ordered = sorted(
        observations,
        key=lambda item: (
            item.arrival_date,
            getattr(item, "id", 0),
        ),
    )
    prepared: list[PreparedObservation] = []
    invalid_count = 0
    for observation in ordered:
        price = _numeric_price(observation)
        if price is None:
            invalid_count += 1
            continue
        prepared.append(PreparedObservation(observation.arrival_date, price))

    observed_dates = {item.observation_date for item in prepared}
    missing_dates: list[date] = []
    if prepared:
        current = prepared[0].observation_date
        end = prepared[-1].observation_date
        while current <= end:
            if current not in observed_dates:
                missing_dates.append(current)
            current += timedelta(days=1)
    return PreparedHistory(
        observations=prepared,
        raw_observation_count=len(ordered),
        invalid_price_count=invalid_count,
        missing_dates=missing_dates,
    )


def build_naive_last_value_forecast(
    prepared: PreparedHistory,
    commodity_id: str,
    market_id: str,
    horizon: int = 7,
) -> dict[str, Any]:
    """Forecast every future day at the last valid observed price."""
    if not prepared.observations:
        return {
            "commodity_id": commodity_id,
            "market_id": market_id,
            "model": MODEL_NAME,
            "status": "no_data",
            "reason": "No valid historical modal-price observations were found.",
            "confidence": None,
            "forecast": [],
            "historical_observation_count": 0,
            "training_start_date": None,
            "training_end_date": None,
            "latest_observed_price_per_kg": None,
            "historical_gap_dates": [],
        }

    start = prepared.observations[0].observation_date
    end = prepared.observations[-1].observation_date
    latest_price = prepared.observations[-1].price_per_kg
    if len(prepared.observations) < MIN_HISTORY_OBSERVATIONS:
        return {
            "commodity_id": commodity_id,
            "market_id": market_id,
            "model": MODEL_NAME,
            "status": "insufficient_history",
            "reason": f"At least {MIN_HISTORY_OBSERVATIONS} valid observations are required.",
            "confidence": None,
            "forecast": [],
            "historical_observation_count": len(prepared.observations),
            "training_start_date": start,
            "training_end_date": end,
            "latest_observed_price_per_kg": latest_price,
            "historical_gap_dates": prepared.missing_dates,
        }

    return {
        "commodity_id": commodity_id,
        "market_id": market_id,
        "model": MODEL_NAME,
        "status": "sufficient_history",
        "reason": None,
        "confidence": None,
        "forecast": [
            {
                "forecast_date": end + timedelta(days=offset),
                "predicted_price_per_kg": latest_price,
            }
            for offset in range(1, horizon + 1)
        ],
        "historical_observation_count": len(prepared.observations),
        "training_start_date": start,
        "training_end_date": end,
        "latest_observed_price_per_kg": latest_price,
        "historical_gap_dates": prepared.missing_dates,
    }


def baseline_forecast(
    db: Session,
    commodity_id: str,
    market_id: str,
    start_date: date | None = None,
    end_date: date | None = None,
    horizon: int = 7,
) -> dict[str, Any]:
    observations = get_historical_prices(
        db=db,
        commodity_id=commodity_id,
        market_id=market_id,
        start_date=start_date,
        end_date=end_date,
    )
    return build_naive_last_value_forecast(
        prepare_history(observations), commodity_id, market_id, horizon
    )


def evaluate_metrics(actual: Iterable[float], predicted: Iterable[float]) -> dict[str, Any]:
    actual_values = [float(value) for value in actual]
    predicted_values = [float(value) for value in predicted]
    if len(actual_values) != len(predicted_values):
        raise ValueError("actual and predicted must have equal lengths")
    if not actual_values:
        return {
            "status": "insufficient_data",
            "observation_count": 0,
            "evaluated_prediction_count": 0,
            "mae": None,
            "rmse": None,
            "mape": None,
        }

    errors = [prediction - observed for observed, prediction in zip(actual_values, predicted_values)]
    non_zero_actuals = [
        abs(error) / abs(observed) * 100
        for observed, error in zip(actual_values, errors)
        if observed != 0
    ]
    return {
        "status": "sufficient_data",
        "observation_count": len(actual_values),
        "evaluated_prediction_count": len(actual_values),
        "mae": mean(abs(error) for error in errors),
        "rmse": sqrt(mean(error * error for error in errors)),
        "mape": mean(non_zero_actuals) if non_zero_actuals else None,
    }


def walk_forward_evaluate(
    values: Iterable[float],
    strategy: ForecastStrategy | Callable[[list[float]], float] | None = None,
    min_history: int = MIN_HISTORY_OBSERVATIONS,
    horizon: int = 1,
) -> dict[str, Any]:
    """Evaluate chronologically, using only observations before each origin."""
    if horizon < 1:
        raise ValueError("horizon must be at least 1")
    actual_values = [float(value) for value in values]
    if len(actual_values) <= min_history + horizon - 1:
        metrics = evaluate_metrics([], [])
        return {"status": "insufficient_data", "evaluation_count": 0, "metrics": metrics}

    selected_strategy = strategy or REGISTERED_STRATEGIES[MODEL_NAME]
    predictions: list[float] = []
    actual: list[float] = []
    for index in range(min_history, len(actual_values) - horizon + 1):
        history = actual_values[:index]
        if callable(selected_strategy) and not hasattr(selected_strategy, "forecast"):
            prediction = float(selected_strategy(history))
        else:
            forecast = selected_strategy.forecast(history, horizon)
            if len(forecast.values) < horizon:
                continue
            prediction = float(forecast.values[horizon - 1])
        predictions.append(prediction)
        actual.append(actual_values[index + horizon - 1])
    metrics = evaluate_metrics(actual, predictions)
    status = "sufficient_data" if actual else "insufficient_data"
    return {"status": status, "evaluation_count": len(actual), "metrics": metrics}


def compare_strategies(
    values: Iterable[float],
    horizon: int,
    strategies: dict[str, ForecastStrategy] | None = None,
    min_history: int = MIN_HISTORY_OBSERVATIONS,
) -> dict[str, Any]:
    """Evaluate each registered strategy and select a best strategy only when valid."""
    selected = strategies or REGISTERED_STRATEGIES
    chronological_values = [float(value) for value in values]
    results: dict[str, Any] = {}
    for name, strategy in selected.items():
        evaluation = walk_forward_evaluate(
            chronological_values, strategy=strategy, min_history=min_history, horizon=horizon
        )
        results[name] = {
            "model": name,
            "status": evaluation["status"],
            "evaluation_count": evaluation["evaluation_count"],
            "metrics": evaluation["metrics"],
        }
    sufficient = [
        item for item in results.values()
        if item["status"] == "sufficient_data" and item["metrics"]["mae"] is not None
    ]
    return {
        "strategies": results,
        "best_strategy": min(sufficient, key=lambda item: item["metrics"]["mae"])["model"]
        if sufficient else None,
        "status": "sufficient_data" if sufficient else "insufficient_data",
    }


def evaluate_history(
    prepared: PreparedHistory,
    commodity_id: str,
    market_id: str,
    start_date: date,
    end_date: date,
    horizon: int,
) -> dict[str, Any]:
    """Build the API-shaped comparison result from observed prices only."""
    comparison = compare_strategies(
        [item.price_per_kg for item in prepared.observations], horizon=horizon
    )
    expected = {
        start_date + timedelta(days=offset)
        for offset in range((end_date - start_date).days + 1)
    }
    observed = {item.observation_date for item in prepared.observations}
    missing_dates = sorted(expected - observed)
    return {
        "commodity": commodity_id,
        "market": market_id,
        "evaluation_date_range": {"start_date": start_date, "end_date": end_date},
        "horizon": horizon,
        "strategies": list(comparison["strategies"].values()),
        "best_strategy": comparison["best_strategy"],
        "status": comparison["status"],
        "insufficient_data": comparison["status"] == "insufficient_data",
        "observation_count": prepared.raw_observation_count,
        "valid_observation_count": len(prepared.observations),
        "invalid_price_count": prepared.invalid_price_count,
        "missing_dates": missing_dates,
        "evaluated_prediction_count": sum(
            item["evaluation_count"] for item in comparison["strategies"].values()
        ),
    }

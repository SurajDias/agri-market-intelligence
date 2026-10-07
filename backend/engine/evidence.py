from datetime import date, datetime
from decimal import Decimal
from typing import Any

from backend.schemas.evidence import (
    DecisionEvidenceContext,
    EvidenceAssessmentRequest,
    EvidenceAssessmentResponse,
    EvidenceComponent,
    EvidenceReason,
)
from backend.services.historical_analytics import analyze_historical_prices


def _decimal(value: Any) -> Decimal | None:
    return Decimal(str(value)) if value is not None else None


def _historical_component(count: int) -> Decimal:
    if count == 0:
        return Decimal("0")
    if count < 2:
        return Decimal("5")
    if count < 30:
        return Decimal("15")
    return Decimal("25")


def _freshness_component(age: int | None) -> Decimal:
    if age is None:
        return Decimal("0")
    if age <= 2:
        return Decimal("20")
    if age <= 7:
        return Decimal("15")
    if age <= 30:
        return Decimal("8")
    return Decimal("0")


def _forecast_component(context) -> tuple[Decimal, str]:
    if context is None or not context.evaluated:
        return Decimal("0"), "Forecast evaluation is unavailable or was not performed."
    if context.mape is None:
        return Decimal("10"), "Forecast was evaluated, but MAPE is unavailable."
    if context.mape <= 10:
        return Decimal("20"), "Evaluated forecast MAPE is at or below 10 percent."
    if context.mape <= 25:
        return Decimal("15"), "Evaluated forecast MAPE is between 10 and 25 percent."
    return Decimal("5"), "Evaluated forecast MAPE is above 25 percent."


def _assumption_penalty(context: DecisionEvidenceContext | None) -> tuple[Decimal, list[str]]:
    if context is None:
        return Decimal("0"), []
    recognized = {
        "price_assumption": "Caller supplied the expected selling price.",
        "distance_assumption": "Caller supplied the transport distance.",
        "transport_rate_assumption": "Caller supplied the transport rate.",
        "spoilage_assumption": "Caller supplied the spoilage estimate.",
    }
    flags = [flag for flag in context.assumption_flags if flag in recognized]
    return Decimal("2.5") * len(flags), flags


def _reason(code: str, severity: str, message: str) -> EvidenceReason:
    return EvidenceReason(code=code, severity=severity, message=message)


def _decision_trace(request, analytics, age, forecast, components, classification, gates, limitations):
    context = request.decision_context
    economics = {
        "quantity_kg": context.quantity_kg if context else None,
        "expected_selling_price_per_kg": context.expected_selling_price_per_kg if context else None,
        "transport_cost": context.transport_cost if context else None,
        "estimated_spoilage_kg": context.estimated_spoilage_kg if context else None,
        "expected_net_value": context.expected_net_value if context else None,
        "opportunity_score": context.opportunity_score if context else None,
    }
    return {
        "decision_context": {
            "commodity_id": request.commodity_id,
            "market_id": request.market_id,
            "evaluation_start_date": request.start_date,
            "evaluation_end_date": request.end_date,
            "reference_datetime": request.reference_datetime,
        },
        "economic_calculation": economics,
        "evidence": {
            "observation_count": analytics["coverage"]["observation_count"],
            "first_observation_date": analytics["coverage"]["earliest_observed_date"],
            "last_observation_date": analytics["coverage"]["latest_observed_date"],
            "coverage_percent": analytics["coverage"]["coverage_percentage"],
            "missing_dates": analytics["coverage"]["missing_calendar_dates"],
            "freshness_age_days": age,
            "forecast": forecast,
        },
        "confidence": {
            "classification": classification,
            "critical_gates": gates,
            "components": [component.model_dump() for component in components],
        },
        "assumptions": context.assumption_flags if context else [],
        "limitations": limitations,
        "ranking_factors": [],
        "explanation": "Evidence/readiness assessment derived from the supplied historical and forecast evidence.",
    }


def assess_evidence(
    request: EvidenceAssessmentRequest,
    observations: list[Any],
) -> EvidenceAssessmentResponse:
    """Assess evidence without creating or inferring unavailable observations."""
    analytics = analyze_historical_prices(observations, request.start_date, request.end_date)
    coverage = analytics["coverage"]
    stats = analytics["descriptive_statistics"]
    volatility = analytics["volatility"]
    count = coverage["observation_count"]
    latest = coverage["latest_observed_date"]
    if latest is not None and request.reference_datetime.date() < latest:
        raise ValueError("reference_datetime must not precede the latest observation")
    age = (request.reference_datetime.date() - latest).days if latest else None

    forecast_context = request.forecast_evaluation
    forecast_score, forecast_explanation = _forecast_component(forecast_context)
    penalty, assumption_flags = _assumption_penalty(request.decision_context)
    assumption_score = Decimal("0") if count == 0 else Decimal("10") - penalty
    coverage_percent = _decimal(coverage["coverage_percentage"])
    coverage_score = (coverage_percent * Decimal("25") / Decimal("100")) if coverage_percent is not None else Decimal("0")
    components = [
        EvidenceComponent(name="historical_observations", value=_historical_component(count), maximum_contribution=Decimal("25"), explanation="30 or more observations receive the full historical-depth contribution."),
        EvidenceComponent(name="calendar_coverage", value=coverage_score, maximum_contribution=Decimal("25"), explanation="Calendar coverage contributes proportionally when an explicit date range is supplied."),
        EvidenceComponent(name="freshness", value=_freshness_component(age), maximum_contribution=Decimal("20"), explanation="Latest evidence age: 0–2 days full, 3–7 days 15, 8–30 days 8, older 0."),
        EvidenceComponent(name="forecast_evaluation", value=forecast_score, maximum_contribution=Decimal("20"), explanation=forecast_explanation),
        EvidenceComponent(name="assumption_reliability", value=assumption_score, maximum_contribution=Decimal("10"), explanation="Starts at 10 when historical evidence exists; 2.5 points are deducted for each recognized caller-supplied economic assumption flag."),
    ]
    score = max(Decimal("0"), min(Decimal("100"), sum(component.value for component in components)))

    gates: list[str] = []
    if count == 0:
        gates.append("no_historical_observations")
    if count < 2:
        gates.append("insufficient_history")
    if latest is None or stats["last_observed_price"] is None:
        gates.append("no_usable_latest_price")
    if coverage_percent is None or coverage_percent < 50:
        gates.append("insufficient_calendar_coverage")
    classification = (
        "insufficient_evidence" if gates else
        "high_confidence" if score >= 75 else
        "moderate_confidence" if score >= 50 else
        "low_confidence"
    )

    reasons: list[EvidenceReason] = []
    if count >= 30 and coverage_percent is not None and coverage_percent >= 90:
        reasons.append(_reason("strong_historical_coverage", "positive", f"The market has {count} observations with {coverage_percent:.1f}% calendar coverage."))
    else:
        reasons.append(_reason("weak_historical_coverage", "negative", f"The market has {count} observations and {coverage_percent if coverage_percent is not None else 'unavailable'}% calendar coverage."))
    if count < 2:
        reasons.append(_reason("insufficient_history", "limitation", "Fewer than two valid historical observations are available."))
    if latest is None or stats["last_observed_price"] is None:
        reasons.append(_reason("no_usable_latest_price", "limitation", "No usable latest historical price is available."))
    if age is not None and age <= 7:
        reasons.append(_reason("recent_observation", "positive", f"The latest observation is {age} day(s) before the supplied reference date."))
    elif age is not None:
        reasons.append(_reason("stale_observation", "negative", f"The latest observation is {age} day(s) old at the supplied reference date."))
    if coverage["missing_calendar_dates"]:
        reasons.append(_reason("missing_dates", "negative", f"{len(coverage['missing_calendar_dates'])} calendar date(s) are missing."))
    if forecast_context is not None and forecast_context.evaluated:
        reasons.append(_reason("forecast_evaluated", "positive", f"Strategy {forecast_context.strategy_name} was evaluated over {forecast_context.evaluation_observation_count} observation(s)."))
        if forecast_context.mape is not None:
            code = "low_forecast_error" if forecast_context.mape <= 10 else "high_forecast_error" if forecast_context.mape > 25 else "moderate_forecast_error"
            reasons.append(_reason(code, "positive" if forecast_context.mape <= 10 else "negative", f"Forecast MAPE is {forecast_context.mape}%."))
    else:
        reasons.append(_reason("forecast_not_evaluated", "limitation", "No evaluated forecast evidence was supplied."))
    for flag in assumption_flags:
        reasons.append(_reason(flag, "limitation", {
            "price_assumption": "Expected price was supplied by the caller.",
            "distance_assumption": "Transport distance was supplied by the caller.",
            "transport_rate_assumption": "Transport rate was supplied by the caller.",
            "spoilage_assumption": "Spoilage estimate was supplied by the caller.",
        }[flag]))
    if request.decision_context and request.decision_context.expected_net_value is not None and request.decision_context.expected_net_value < 0:
        reasons.append(_reason("negative_net_value", "negative", "The supplied economic context has a negative expected net value."))
    if request.decision_context and request.decision_context.shelf_life_status in {"near_expiry", "expired"}:
        reasons.append(_reason(request.decision_context.shelf_life_status, "negative", f"The supplied product status is {request.decision_context.shelf_life_status}."))

    limitations = list(gates)
    if age is not None and age > 30:
        limitations.append("stale_market_data")
    if not forecast_context or not forecast_context.evaluated:
        limitations.append("forecast_not_evaluated")
    if request.decision_context:
        limitations.extend(assumption_flags)
        if request.decision_context.shelf_life_status in {"near_expiry", "expired"}:
            limitations.append(f"{request.decision_context.shelf_life_status}_product")
        if request.decision_context.expected_net_value is not None and request.decision_context.expected_net_value < 0:
            limitations.append("negative_expected_net_value")
    limitations = list(dict.fromkeys(limitations))
    forecast_trace = forecast_context.model_dump() if forecast_context else None
    trace = _decision_trace(request, analytics, age, forecast_trace, components, classification, gates, limitations)
    provenance = {
        "observation_count": "measured_from_database",
        "first_observation_date": "measured_from_database",
        "last_observation_date": "measured_from_database",
        "calendar_coverage_percent": "calculated_from_database",
        "missing_date_count": "calculated_from_database",
        "missing_dates": "calculated_from_database",
        "price_change_percent": "calculated_from_database",
        "price_volatility_measure": "calculated_from_database",
        "trend": "calculated_from_database",
        "freshness_age_days": "calculated_from_database",
        "forecast_strategy_name": "derived_from_forecast_evaluation" if forecast_context and forecast_context.evaluated else "unavailable",
        "forecast_horizon": "derived_from_forecast_evaluation" if forecast_context and forecast_context.evaluated else "unavailable",
        "forecast_metrics": "derived_from_forecast_evaluation" if forecast_context and forecast_context.evaluated else "unavailable",
        "forecast_evaluation_observation_count": "derived_from_forecast_evaluation" if forecast_context and forecast_context.evaluated else "unavailable",
        "reference_datetime": "supplied_by_caller",
        "economic_context": "supplied_by_caller" if request.decision_context else "unavailable",
        "assumption_flags": "supplied_by_caller" if request.decision_context and request.decision_context.assumption_flags else "unavailable",
        "critical_gates": "calculated_from_database",
        "limitations": "calculated_from_database",
    }
    return EvidenceAssessmentResponse(
        commodity_id=request.commodity_id,
        market_id=request.market_id,
        first_observation_date=coverage["earliest_observed_date"],
        last_observation_date=latest,
        observation_count=count,
        calendar_coverage_percent=coverage_percent,
        missing_date_count=len(coverage["missing_calendar_dates"]),
        missing_dates=coverage["missing_calendar_dates"],
        price_change_percent=_decimal(stats["percentage_change"]),
        price_volatility_measure=_decimal(volatility["standard_deviation_of_percentage_changes"]),
        trend=analytics["trend"],
        freshness_age_days=age,
        forecast_evidence_available=bool(forecast_context and forecast_context.evaluated),
        forecast_strategy_name=forecast_context.strategy_name if forecast_context and forecast_context.evaluated else None,
        forecast_horizon=forecast_context.horizon if forecast_context and forecast_context.evaluated else None,
        forecast_mae=forecast_context.mae if forecast_context and forecast_context.evaluated else None,
        forecast_rmse=forecast_context.rmse if forecast_context and forecast_context.evaluated else None,
        forecast_mape=forecast_context.mape if forecast_context and forecast_context.evaluated else None,
        forecast_evaluation_observation_count=forecast_context.evaluation_observation_count if forecast_context and forecast_context.evaluated else 0,
        evidence_quality_score=score,
        confidence_classification=classification,
        critical_gates=gates,
        components=components,
        evidence_reasons=reasons,
        limitations=limitations,
        provenance=provenance,
        decision_trace=trace,
    )

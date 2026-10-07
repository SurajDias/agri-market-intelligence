from __future__ import annotations

from decimal import Decimal
from typing import Any

from backend.engine.evidence import assess_evidence
from backend.engine.recommendation import analyze_recommendation
from backend.engine.simulator import simulate
from backend.schemas.decision_intelligence import (
    DataQualitySummary,
    DecisionIntelligenceRequest,
    DecisionIntelligenceResponse,
    FinalDecision,
    UnifiedCandidate,
)
from backend.schemas.evidence import EvidenceAssessmentRequest
from backend.schemas.recommendation import RecommendationRequest
from backend.schemas.simulator import SimulatorRequest


def _recommendation_request(request: DecisionIntelligenceRequest) -> RecommendationRequest:
    return RecommendationRequest(
        commodity_id=request.commodity_id,
        origin_market_id=request.origin_market_id,
        quantity_kg=request.quantity_kg,
        candidates=[candidate.model_dump(exclude={"forecast_evaluation"}) for candidate in request.candidates],
    )


def _simulator_request(request: DecisionIntelligenceRequest) -> SimulatorRequest:
    return SimulatorRequest(
        commodity_id=request.commodity_id,
        origin_market_id=request.origin_market_id,
        quantity_kg=request.quantity_kg,
        candidates=[candidate.model_dump(exclude={"forecast_evaluation"}) for candidate in request.candidates],
        scenario=request.scenario,
        scenario_grid=request.scenario_grid,
        sensitivity=request.sensitivity,
    )


def _evidence_request(request, candidate, forecast) -> EvidenceAssessmentRequest:
    context = candidate.forecast_evaluation or forecast
    return EvidenceAssessmentRequest(
        commodity_id=request.commodity_id,
        market_id=candidate.market_id,
        start_date=request.start_date,
        end_date=request.end_date,
        reference_datetime=request.reference_datetime,
        forecast_evaluation=context,
        decision_context={
            "quantity_kg": request.quantity_kg,
            "expected_selling_price_per_kg": candidate.expected_selling_price_per_kg,
            "estimated_spoilage_kg": candidate.estimated_spoilage_kg,
            "shelf_life_status": candidate.shelf_life_status,
            "assumption_flags": [
                "price_assumption",
                "distance_assumption",
                "transport_rate_assumption",
                "spoilage_assumption",
            ],
        },
    )


def _decision_status(final_candidate, robustness: dict | None, candidate_count: int) -> str:
    if candidate_count == 0:
        return "no_opportunity"
    if final_candidate is None:
        return "economically_unfavorable"
    if final_candidate.confidence_classification == "insufficient_evidence":
        return "insufficient_evidence"
    if final_candidate.confidence_classification == "low_confidence":
        return "actionable_with_caution"
    if robustness is None or robustness.get("classification") in {"sensitive", "highly_sensitive", "indeterminate"}:
        return "actionable_with_caution"
    if robustness.get("classification") in {"robust", "highly_robust"}:
        return "actionable"
    return "evidence_limited"


def _candidate_assumptions(candidate) -> list[str]:
    return [
        "caller_supplied_price",
        "caller_supplied_distance",
        "caller_supplied_transport_rate",
        "caller_supplied_spoilage",
    ]


def analyze_decision_intelligence(
    request: DecisionIntelligenceRequest,
    observations_by_market: dict[str, list[Any]],
    market_names: dict[str, str] | None = None,
) -> DecisionIntelligenceResponse:
    """Compose existing economic, evidence, and counterfactual engines."""
    names = market_names or {}
    recommendation = analyze_recommendation(_recommendation_request(request), names)
    evidence_by_market = {}
    forecast = request.forecast_evaluation
    for candidate in request.candidates:
        evidence_by_market[candidate.market_id] = assess_evidence(
            _evidence_request(request, candidate, forecast),
            observations_by_market.get(candidate.market_id, []),
        )

    simulator = simulate(_simulator_request(request), names)
    robustness = simulator.robustness_analysis
    sensitivity = simulator.sensitivity
    simulation_by_market = {}
    if simulator.scenarios:
        for item in simulator.scenarios[0].candidates:
            simulation_by_market[item.market_id] = item

    unified: list[UnifiedCandidate] = []
    for ranked in recommendation.ranked_candidates:
        evidence = evidence_by_market[ranked.market_id]
        sim_item = simulation_by_market.get(ranked.market_id)
        unified.append(UnifiedCandidate(
            market_id=ranked.market_id,
            market_name=ranked.market_name,
            commodity_id=request.commodity_id,
            expected_selling_price_per_kg=ranked.expected_selling_price_per_kg,
            quantity_kg=ranked.quantity_kg,
            transport_cost=ranked.transport_cost,
            estimated_spoilage_kg=ranked.estimated_spoilage_kg,
            saleable_quantity_kg=ranked.saleable_quantity_kg,
            gross_revenue=ranked.gross_revenue,
            estimated_spoilage_loss_inr=ranked.estimated_spoilage_loss_inr,
            expected_net_value=ranked.expected_net_value,
            net_value_per_original_kg=ranked.net_value_per_original_kg,
            opportunity_score=ranked.opportunity_score,
            recommendation_label=ranked.recommendation_label,
            ranking_position=ranked.rank,
            observation_count=evidence.observation_count,
            first_observation_date=evidence.first_observation_date,
            last_observation_date=evidence.last_observation_date,
            coverage_percent=evidence.calendar_coverage_percent,
            missing_date_count=evidence.missing_date_count,
            freshness_age_days=evidence.freshness_age_days,
            historical_trend=evidence.trend,
            volatility=evidence.price_volatility_measure,
            forecast_evidence_available=evidence.forecast_evidence_available,
            forecast_strategy=evidence.forecast_strategy_name,
            forecast_horizon=evidence.forecast_horizon,
            forecast_mae=evidence.forecast_mae,
            forecast_rmse=evidence.forecast_rmse,
            forecast_mape=evidence.forecast_mape,
            forecast_evaluation_observations=evidence.forecast_evaluation_observation_count,
            evidence_quality_score=evidence.evidence_quality_score,
            confidence_classification=evidence.confidence_classification,
            evidence_reasons=[reason.model_dump() for reason in evidence.evidence_reasons],
            limitations=evidence.limitations,
            robustness_classification=robustness.get("classification", "indeterminate"),
            preservation_rate=robustness.get("preservation_rate"),
            margin_ratio=robustness.get("margin_ratio"),
            break_even_analysis=(simulator.scenarios[0].break_even_analysis if simulator.scenarios else {}),
            sensitivity_summary=sensitivity,
            shelf_life_status=ranked.shelf_life_status,
            provenance=evidence.provenance,
        ))

    recommended = next((candidate for candidate in unified if candidate.market_id == recommendation.recommended_market_id), None)
    reasons: list[str] = []
    if recommended:
        reasons.extend(["highest_expected_net_value", "positive_expected_net_value"] if recommended.expected_net_value > 0 else ["negative_expected_net_value"])
        reasons.extend(reason["code"] for reason in recommended.evidence_reasons if reason["severity"] in {"positive", "limitation"})
        if robustness.get("preservation_rate") is not None:
            reasons.append("recommendation_preserved" if robustness["preservation_rate"] >= 50 else "recommendation_changed")
        if robustness.get("margin_ratio") is not None:
            reasons.append("wide_net_margin" if robustness["margin_ratio"] >= Decimal("0.1") else "narrow_net_margin")
        if robustness.get("classification") in {"robust", "highly_robust"}:
            reasons.append("robust_to_sensitivity")
        elif robustness.get("classification") in {"sensitive", "highly_sensitive"}:
            reasons.append("sensitive_to_price")
        reasons.extend(_candidate_assumptions(request.candidates[request.candidates.index(next(c for c in request.candidates if c.market_id == recommended.market_id))]))
    elif request.candidates:
        reasons.append("negative_expected_net_value")

    limitations = list(dict.fromkeys(
        [limitation for candidate in unified for limitation in candidate.limitations]
        + (["no_candidates"] if not request.candidates else [])
    ))
    critical_issues = list(dict.fromkeys(
        [gate for candidate in unified for gate in candidate.limitations if gate in {"no_historical_observations", "insufficient_history", "no_usable_latest_price", "insufficient_calendar_coverage"}]
    ))
    final = FinalDecision(
        recommended_market=recommendation.recommended_market_id,
        economic_recommendation=(recommended.recommendation_label if recommended else None),
        opportunity_score=(recommended.opportunity_score if recommended else None),
        confidence_classification=(recommended.confidence_classification if recommended else "insufficient_evidence"),
        robustness_classification=(recommended.robustness_classification if recommended else "indeterminate"),
        decision_status=_decision_status(recommended, robustness, len(request.candidates)),
        expected_net_value=(recommended.expected_net_value if recommended else None),
        decision_reasons=list(dict.fromkeys(reasons)),
    )
    selected_evidence = evidence_by_market.get(recommendation.recommended_market_id) if recommendation.recommended_market_id else None
    summary = DataQualitySummary(
        historical_data_available=bool(selected_evidence and selected_evidence.observation_count > 0),
        observation_count=selected_evidence.observation_count if selected_evidence else 0,
        coverage_percent=selected_evidence.calendar_coverage_percent if selected_evidence else None,
        missing_date_count=selected_evidence.missing_date_count if selected_evidence else 0,
        latest_observation_date=selected_evidence.last_observation_date if selected_evidence else None,
        freshness_age_days=selected_evidence.freshness_age_days if selected_evidence else None,
        forecast_evidence_available=selected_evidence.forecast_evidence_available if selected_evidence else False,
        critical_data_issues=critical_issues,
        assumptions_count=len(_candidate_assumptions(request.candidates[0])) if request.candidates else 0,
        limitations_count=len(limitations),
    )
    trace = {
        "request_context": request.model_dump(exclude={"scenario", "scenario_grid", "sensitivity"}),
        "data_evidence": {candidate.market_id: evidence_by_market[candidate.market_id].model_dump() for candidate in request.candidates},
        "economic_analysis": recommendation.model_dump(),
        "market_ranking": [candidate.market_id for candidate in unified],
        "confidence_analysis": {candidate.market_id: {"score": candidate.evidence_quality_score, "classification": candidate.confidence_classification} for candidate in unified},
        "sensitivity_analysis": sensitivity,
        "robustness_analysis": robustness,
        "final_decision": final.model_dump(),
        "assumptions": _candidate_assumptions(request.candidates[0]) if request.candidates else [],
        "limitations": limitations,
        "provenance": {"economic_recommendation": "calculated_from_database", "economic_inputs": "supplied_by_caller", "historical_evidence": "calculated_from_database", "forecast_evidence": "derived_from_forecast_evaluation" if forecast else "unavailable", "sensitivity": "calculated_from_database"},
    }
    return DecisionIntelligenceResponse(
        request_context=request.model_dump(exclude={"scenario", "scenario_grid", "sensitivity"}),
        candidates=unified,
        ranking=[candidate.market_id for candidate in unified],
        data_quality_summary=summary,
        final_decision=final,
        assumptions=_candidate_assumptions(request.candidates[0]) if request.candidates else [],
        limitations=limitations,
        provenance=trace["provenance"],
        decision_trace=trace,
    )

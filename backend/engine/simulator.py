from __future__ import annotations

from itertools import product
from decimal import Decimal

from backend.engine.recommendation import analyze_recommendation
from backend.schemas.recommendation import RecommendationRequest
from backend.schemas.simulator import (
    MAX_SCENARIOS,
    EconomicSnapshot,
    ScenarioDefinition,
    ScenarioResult,
    SimulatorRequest,
    SimulatorResponse,
)


def _recommendation_request(request: SimulatorRequest, candidates: list[dict]) -> RecommendationRequest:
    return RecommendationRequest(
        commodity_id=request.commodity_id,
        origin_market_id=request.origin_market_id,
        quantity_kg=request.quantity_kg,
        candidates=candidates,
    )


def _candidate_dict(candidate, scenario: ScenarioDefinition | None, quantity: Decimal) -> dict:
    scenario = scenario or ScenarioDefinition()
    targeted = scenario.target_market_id is None or scenario.target_market_id == candidate.market_id
    def changed(percent_name, override_name, baseline):
        if not targeted:
            return baseline
        override = getattr(scenario, override_name)
        percent = getattr(scenario, percent_name)
        if override is not None:
            return override
        if percent is not None:
            return baseline * (Decimal("1") + percent / Decimal("100"))
        return baseline

    return {
        "market_id": candidate.market_id,
        "expected_selling_price_per_kg": changed("price_change_percent", "expected_selling_price_per_kg", candidate.expected_selling_price_per_kg),
        "distance_km": changed("distance_change_percent", "distance_km", candidate.distance_km),
        "transport_rate_per_km_per_kg": changed("transport_rate_change_percent", "transport_rate_per_km_per_kg", candidate.transport_rate_per_km_per_kg),
        "estimated_spoilage_kg": changed("spoilage_change_percent", "estimated_spoilage_kg", candidate.estimated_spoilage_kg),
        "shelf_life_status": candidate.shelf_life_status,
    }


def _ranked_snapshot(item, request_candidate, market_name: str) -> EconomicSnapshot:
    return EconomicSnapshot(
        market_id=item.market_id,
        market_name=market_name,
        expected_selling_price_per_kg=item.expected_selling_price_per_kg,
        distance_km=request_candidate["distance_km"],
        transport_rate_per_km_per_kg=request_candidate["transport_rate_per_km_per_kg"],
        quantity_kg=item.quantity_kg,
        transport_cost=item.transport_cost,
        estimated_spoilage_kg=item.estimated_spoilage_kg,
        saleable_quantity_kg=item.saleable_quantity_kg,
        gross_revenue=item.gross_revenue,
        estimated_spoilage_loss_inr=item.estimated_spoilage_loss_inr,
        expected_net_value=item.expected_net_value,
        net_value_per_original_kg=item.net_value_per_original_kg,
        spoilage_percentage=item.spoilage_percentage,
        shelf_life_status=item.shelf_life_status,
    )


def _delta(baseline: EconomicSnapshot, scenario: EconomicSnapshot) -> tuple[dict, dict]:
    fields = (
        "expected_selling_price_per_kg", "transport_cost", "estimated_spoilage_kg",
        "saleable_quantity_kg", "gross_revenue", "expected_net_value",
        "distance_km", "transport_rate_per_km_per_kg",
    )
    absolute = {field: getattr(scenario, field) - getattr(baseline, field) for field in fields}
    percentage = {
        field: (absolute[field] / getattr(baseline, field) * Decimal("100"))
        if getattr(baseline, field) != 0 else None
        for field in fields
    }
    return absolute, percentage


def _break_even(baseline, request: SimulatorRequest, baseline_candidates: dict[str, EconomicSnapshot]) -> dict:
    ranked = baseline.ranked_candidates
    if len(ranked) < 2 or baseline.recommended_market_id is None:
        return {"threshold_status": "not_available", "reason": "At least two candidates and a positive baseline recommendation are required."}
    best = baseline.recommended_market_id
    best_snapshot = baseline_candidates[best]
    results = []
    for competitor in ranked:
        if competitor.market_id == best:
            continue
        other = baseline_candidates[competitor.market_id]
        price = best_snapshot.expected_selling_price_per_kg
        saleable = best_snapshot.saleable_quantity_kg
        rate = best_snapshot.transport_rate_per_km_per_kg
        quantity = best_snapshot.quantity_kg
        thresholds = {}
        if saleable > 0:
            thresholds["minimum_price_for_best_market"] = (other.expected_net_value + best_snapshot.transport_cost) / saleable
        else:
            thresholds["minimum_price_for_best_market"] = None
        thresholds["maximum_transport_cost_for_best_market"] = price * saleable - other.expected_net_value
        if quantity > 0 and rate > 0:
            thresholds["maximum_distance_km_for_best_market"] = thresholds["maximum_transport_cost_for_best_market"] / (quantity * rate)
        else:
            thresholds["maximum_distance_km_for_best_market"] = None
        if price > 0:
            saleable_required = (other.expected_net_value + best_snapshot.transport_cost) / price
            thresholds["maximum_spoilage_kg_for_best_market"] = quantity - saleable_required
        else:
            thresholds["maximum_spoilage_kg_for_best_market"] = None
        results.append({"competitor_market_id": competitor.market_id, "threshold_status": "available", "thresholds": thresholds})
    return {"threshold_status": "available", "comparisons": results, "method": "analytical_net_value_equalization"}


def _robustness(results: list[ScenarioResult], baseline_net: Decimal | None, baseline_recommendation: str | None) -> dict:
    if baseline_recommendation is None or baseline_net is None or baseline_net <= 0:
        return {"classification": "indeterminate", "preservation_rate": None, "margin_ratio": None, "reason": "No positive baseline recommendation exists."}
    preserved = sum(not result.recommendation_changed for result in results)
    rate = Decimal(preserved) / Decimal(len(results)) if results else Decimal("1")
    margin_ratio = None
    if results and results[0].candidates:
        values = sorted((candidate.baseline.expected_net_value for candidate in results[0].candidates), reverse=True)
        if len(values) > 1 and values[0] != 0:
            margin_ratio = (values[0] - values[1]) / abs(values[0])
    if rate >= Decimal("0.8") and (margin_ratio is None or margin_ratio >= Decimal("0.2")):
        classification = "highly_robust"
    elif rate >= Decimal("0.6") or (margin_ratio is not None and margin_ratio >= Decimal("0.1")):
        classification = "robust"
    elif rate > 0:
        classification = "sensitive"
    else:
        classification = "highly_sensitive"
    return {"classification": classification, "preservation_rate": rate * Decimal("100"), "margin_ratio": margin_ratio, "method": "scenario_preservation_and_baseline_margin"}


def _scenario_id(scenario: ScenarioDefinition, index: int) -> str:
    if scenario.scenario_id:
        return scenario.scenario_id
    values = [
        scenario.price_change_percent, scenario.transport_rate_change_percent,
        scenario.distance_change_percent, scenario.spoilage_change_percent,
        scenario.expected_selling_price_per_kg, scenario.distance_km,
        scenario.transport_rate_per_km_per_kg, scenario.estimated_spoilage_kg,
        scenario.target_market_id,
    ]
    encoded = "_".join(str(value) if value is not None else "base" for value in values)
    return f"scenario_{index}_{encoded}"


def _scenario_description(scenario: ScenarioDefinition) -> str:
    return scenario.scenario_description or "Controlled counterfactual scenario."


def _make_scenarios(request: SimulatorRequest) -> list[ScenarioDefinition]:
    if request.scenario is not None:
        return [request.scenario]
    if request.scenario_grid is None:
        return [ScenarioDefinition(scenario_id="baseline_counterfactual", scenario_description="No controlled change; reproduces the baseline.")]
    grid = request.scenario_grid
    values = [
        grid.price_change_percent or [Decimal("0")],
        grid.transport_rate_change_percent or [Decimal("0")],
        grid.distance_change_percent or [Decimal("0")],
        grid.spoilage_change_percent or [Decimal("0")],
    ]
    count = 1
    for group in values:
        count *= len(group)
    if count > MAX_SCENARIOS:
        raise ValueError(f"scenario grid exceeds maximum of {MAX_SCENARIOS} scenarios")
    return [ScenarioDefinition(
        price_change_percent=price,
        transport_rate_change_percent=rate,
        distance_change_percent=distance,
        spoilage_change_percent=spoilage,
        scenario_description=f"Price {price}%, transport rate {rate}%, distance {distance}%, spoilage {spoilage}%.",
    ) for price, rate, distance, spoilage in product(*values)]


def _sensitivity(request: SimulatorRequest, baseline, market_names: dict[str, str]) -> dict:
    config = request.sensitivity
    if config is None:
        return {}
    outputs = {}
    fields = {
        "price": ("price_values", "expected_selling_price_per_kg"),
        "transport_rate": ("transport_rate_values", "transport_rate_per_km_per_kg"),
        "distance": ("distance_values", "distance_km"),
        "spoilage": ("spoilage_values", "estimated_spoilage_kg"),
    }
    for variable, (values_field, override_field) in fields.items():
        values = getattr(config, values_field)
        if not values:
            continue
        entries = []
        previous_market = None
        transition = None
        for value in values:
            scenario = ScenarioDefinition(target_market_id=config.target_market_id, **{override_field: value})
            candidates = [_candidate_dict(candidate, scenario, request.quantity_kg) for candidate in request.candidates]
            recommendation = analyze_recommendation(_recommendation_request(request, candidates), market_names)
            market = recommendation.recommended_market_id
            entries.append({"value": value, "recommended_market": market, "expected_net_value": recommendation.expected_net_value})
            if previous_market is not None and market != previous_market and transition is None:
                transition = value
            previous_market = market
        outputs[variable] = {"values": entries, "recommendation_change_at": transition}
    return outputs


def simulate(request: SimulatorRequest, market_names: dict[str, str] | None = None) -> SimulatorResponse:
    names = market_names or {}
    baseline_candidates = [_candidate_dict(candidate, None, request.quantity_kg) for candidate in request.candidates]
    baseline = analyze_recommendation(_recommendation_request(request, baseline_candidates), names)
    baseline_input_map = {candidate["market_id"]: candidate for candidate in baseline_candidates}
    baseline_map = {item.market_id: _ranked_snapshot(item, baseline_input_map[item.market_id], item.market_name) for item in baseline.ranked_candidates}
    scenarios = _make_scenarios(request)
    if len(scenarios) > MAX_SCENARIOS:
        raise ValueError(f"scenario count exceeds maximum of {MAX_SCENARIOS}")
    results: list[ScenarioResult] = []
    for index, scenario in enumerate(scenarios, start=1):
        scenario_candidates = [_candidate_dict(candidate, scenario, request.quantity_kg) for candidate in request.candidates]
        scenario_recommendation = analyze_recommendation(_recommendation_request(request, scenario_candidates), names)
        scenario_map = {item.market_id: _ranked_snapshot(item, scenario_candidates[next(i for i, c in enumerate(scenario_candidates) if c["market_id"] == item.market_id)], item.market_name) for item in scenario_recommendation.ranked_candidates}
        candidate_results = []
        for market_id in baseline_map:
            before = baseline_map[market_id]
            after = scenario_map[market_id]
            absolute, percentage = _delta(before, after)
            candidate_results.append({"market_id": market_id, "market_name": before.market_name, "baseline": before, "scenario": after, "absolute_changes": absolute, "percentage_changes": percentage})
        changed_variables = [name for name in ("price_change_percent", "transport_rate_change_percent", "distance_change_percent", "spoilage_change_percent", "expected_selling_price_per_kg", "distance_km", "transport_rate_per_km_per_kg", "estimated_spoilage_kg") if getattr(scenario, name) is not None]
        changed = baseline.recommended_market_id != scenario_recommendation.recommended_market_id
        explanations = ["recommendation_changed" if changed else "recommendation_preserved"]
        if scenario.price_change_percent is not None or scenario.expected_selling_price_per_kg is not None:
            explanations.append("price_is_primary_driver")
        if scenario.transport_rate_change_percent is not None or scenario.distance_change_percent is not None or scenario.transport_rate_per_km_per_kg is not None or scenario.distance_km is not None:
            explanations.append("transport_is_primary_driver")
        if scenario.spoilage_change_percent is not None or scenario.estimated_spoilage_kg is not None:
            explanations.append("spoilage_is_primary_driver")
        limitations = ["caller_supplied_scenario_inputs"]
        result = ScenarioResult(
            scenario_id=_scenario_id(scenario, index),
            scenario_description=_scenario_description(scenario),
            baseline_recommended_market=baseline.recommended_market_id,
            scenario_recommended_market=scenario_recommendation.recommended_market_id,
            recommendation_changed=changed,
            ranking_before=[item.market_id for item in baseline.ranked_candidates],
            ranking_after=[item.market_id for item in scenario_recommendation.ranked_candidates],
            candidates=candidate_results,
            break_even_analysis=_break_even(baseline, request, baseline_map),
            robustness_analysis={},
            explanations=explanations,
            assumptions=changed_variables,
            limitations=limitations,
            trace={"scenario_id": _scenario_id(scenario, index), "baseline_inputs": [candidate.model_dump() for candidate in request.candidates], "scenario_inputs": scenario.model_dump(), "changed_variables": changed_variables, "ranking_before": [item.market_id for item in baseline.ranked_candidates], "ranking_after": [item.market_id for item in scenario_recommendation.ranked_candidates]},
        )
        results.append(result)
    robustness = _robustness(results, baseline.expected_net_value, baseline.recommended_market_id)
    for result in results:
        result.robustness_analysis = robustness
        result.trace["robustness_analysis"] = robustness
    return SimulatorResponse(
        commodity_id=request.commodity_id,
        origin_market_id=request.origin_market_id,
        quantity_kg=request.quantity_kg,
        baseline_recommended_market=baseline.recommended_market_id,
        baseline_ranking=[item.market_id for item in baseline.ranked_candidates],
        scenarios=results,
        sensitivity=_sensitivity(request, baseline, names),
        robustness_analysis=robustness,
    )

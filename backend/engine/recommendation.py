from decimal import Decimal

from backend.engine.decision_engine import calculate_expected_net_value
from backend.engine.transport_cost import calculate_transport_cost
from backend.schemas.recommendation import (
    RankedCandidate,
    RecommendationCandidateRequest,
    RecommendationLabel,
    RecommendationRequest,
    RecommendationResponse,
)


def _relative_score(value: Decimal, maximum: Decimal) -> Decimal:
    if maximum <= 0:
        return Decimal("0")
    return (value / maximum) * Decimal("100")


def _bounded(value: Decimal) -> Decimal:
    return max(Decimal("0"), min(Decimal("100"), value))


def _label(score: Decimal) -> RecommendationLabel:
    if score >= 80:
        return "strong_opportunity"
    if score >= 60:
        return "opportunity"
    if score >= 40:
        return "neutral"
    if score >= 20:
        return "weak_opportunity"
    return "avoid"


def _assumption_flags(candidate: RecommendationCandidateRequest) -> list[str]:
    flags = [
        "price_assumption",
        "distance_assumption",
        "transport_rate_assumption",
        "spoilage_assumption",
    ]
    if candidate.shelf_life_status in {"near_expiry", "expired"}:
        flags.append(candidate.shelf_life_status)
    return flags


def _factors(
    candidate: dict,
    candidates: list[dict],
    best_net_value: Decimal,
) -> tuple[list[str], list[str]]:
    prices = [item["expected_selling_price_per_kg"] for item in candidates]
    costs = [item["transport_cost"] for item in candidates]
    spoilage = [item["estimated_spoilage_kg"] for item in candidates]
    positive: list[str] = []
    negative: list[str] = []
    if candidate["expected_selling_price_per_kg"] == max(prices):
        positive.append("higher expected selling price")
    elif candidate["expected_selling_price_per_kg"] < max(prices):
        negative.append("lower expected selling price")
    if candidate["transport_cost"] == min(costs):
        positive.append("lower transport cost")
    elif candidate["transport_cost"] == max(costs):
        negative.append("high transport cost")
    if candidate["estimated_spoilage_kg"] == min(spoilage):
        positive.append("lower estimated spoilage")
    elif candidate["estimated_spoilage_kg"] == max(spoilage):
        negative.append("high estimated spoilage")
    if candidate["expected_net_value"] == best_net_value:
        positive.append("higher expected net value")
    elif candidate["expected_net_value"] < best_net_value:
        negative.append("lower expected net value")
    if candidate["expected_net_value"] < 0:
        negative.append("negative expected net value")
    if candidate["shelf_life_status"] in {"near_expiry", "expired"}:
        negative.append(f"{candidate['shelf_life_status']} status")
    return positive, negative


def analyze_recommendation(
    request: RecommendationRequest,
    market_names: dict[str, str] | None = None,
) -> RecommendationResponse:
    """Rank a caller-supplied candidate set using existing calculation engines."""
    names = market_names or {}
    if not request.candidates:
        return RecommendationResponse(
            commodity_id=request.commodity_id,
            origin_market_id=request.origin_market_id,
            quantity_kg=request.quantity_kg,
            recommended_market_id=None,
            recommended_market_name=None,
            recommendation_label="no_opportunity",
            opportunity_score=None,
            expected_net_value=None,
            primary_reason="No candidate markets were supplied.",
            ranked_candidates=[],
        )

    calculated: list[dict] = []
    for candidate in request.candidates:
        transport = calculate_transport_cost(
            request.origin_market_id,
            candidate.market_id,
            request.quantity_kg,
            candidate.distance_km,
            candidate.transport_rate_per_km_per_kg,
        )
        decision = calculate_expected_net_value(
            quantity_kg=request.quantity_kg,
            expected_selling_price_per_kg=candidate.expected_selling_price_per_kg,
            transport_cost=transport["transport_cost"],
            estimated_spoilage_kg=candidate.estimated_spoilage_kg,
            shelf_life_status=candidate.shelf_life_status,
        )
        calculated.append({
            **decision,
            "market_id": candidate.market_id,
            "market_name": names.get(candidate.market_id, candidate.market_id),
            "distance_km": candidate.distance_km,
            "candidate": candidate,
            "price_advantage_vs_origin": (
                candidate.expected_selling_price_per_kg - request.origin_expected_selling_price_per_kg
                if request.origin_expected_selling_price_per_kg is not None else None
            ),
        })

    calculated.sort(key=lambda item: (
        -item["expected_net_value"],
        -item["expected_selling_price_per_kg"],
        item["transport_cost"],
        item["market_id"],
    ))
    best_net_value = max(item["expected_net_value"] for item in calculated)
    max_price = max(item["expected_selling_price_per_kg"] for item in calculated)
    max_transport = max(item["transport_cost"] for item in calculated)
    min_transport = min(item["transport_cost"] for item in calculated)

    ranked: list[RankedCandidate] = []
    for rank, item in enumerate(calculated, start=1):
        net_score = _bounded(_relative_score(item["expected_net_value"], best_net_value)) if best_net_value > 0 else (Decimal("100") if item["expected_net_value"] == 0 else Decimal("0"))
        price_score = _relative_score(item["expected_selling_price_per_kg"], max_price) if max_price > 0 else Decimal("0")
        transport_score = Decimal("100") if max_transport == min_transport else (Decimal("100") - item["transport_cost"] / max_transport * Decimal("100"))
        spoilage_score = Decimal("100") - item["spoilage_percentage"]
        score = (net_score + price_score + transport_score + spoilage_score) / Decimal("4")
        score = _bounded(score)
        positive, negative = _factors(item, calculated, best_net_value)
        label = _label(score) if best_net_value > 0 else "avoid"
        reason = (
            "Highest expected net value after transport and estimated spoilage."
            if rank == 1 and best_net_value > 0
            else "No candidate produces a positive expected net value under the supplied assumptions."
            if best_net_value <= 0 and rank == 1
            else "Lower expected net value than the leading candidate."
        )
        ranked.append(RankedCandidate(
            rank=rank,
            market_id=item["market_id"],
            market_name=item["market_name"],
            expected_selling_price_per_kg=item["expected_selling_price_per_kg"],
            quantity_kg=item["quantity_kg"],
            transport_cost=item["transport_cost"],
            estimated_spoilage_kg=item["estimated_spoilage_kg"],
            saleable_quantity_kg=item["saleable_quantity_kg"],
            gross_revenue=item["gross_revenue"],
            estimated_spoilage_loss_inr=item["estimated_spoilage_loss_inr"],
            expected_net_value=item["expected_net_value"],
            net_value_per_original_kg=item["net_value_per_original_kg"],
            spoilage_percentage=item["spoilage_percentage"],
            price_advantage_vs_origin=item["price_advantage_vs_origin"],
            shelf_life_status=item["shelf_life_status"],
            opportunity_score=score,
            recommendation_label=label,
            positive_factors=positive,
            negative_factors=negative,
            primary_reason=reason,
            assumption_flags=_assumption_flags(item["candidate"]),
            explanation={
                "positive_factors": positive,
                "negative_factors": negative,
                "primary_reason": reason,
            },
        ))

    recommended = ranked[0] if best_net_value > 0 else None
    overall_label: RecommendationLabel = ranked[0].recommendation_label if recommended else "avoid"
    return RecommendationResponse(
        commodity_id=request.commodity_id,
        origin_market_id=request.origin_market_id,
        quantity_kg=request.quantity_kg,
        recommended_market_id=recommended.market_id if recommended else None,
        recommended_market_name=recommended.market_name if recommended else None,
        recommendation_label=overall_label,
        opportunity_score=recommended.opportunity_score if recommended else None,
        expected_net_value=recommended.expected_net_value if recommended else None,
        primary_reason=ranked[0].primary_reason,
        ranked_candidates=ranked,
    )

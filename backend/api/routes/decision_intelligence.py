from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.api.dependencies import get_db
from backend.engine.decision_intelligence import analyze_decision_intelligence
from backend.models.commodity import Commodity
from backend.models.market import Market
from backend.schemas.decision_intelligence import DecisionIntelligenceRequest, DecisionIntelligenceResponse
from backend.services.historical_prices import get_historical_prices


router = APIRouter(prefix="/api/decision-intelligence", tags=["decision-intelligence"])


@router.post("/analyze", response_model=DecisionIntelligenceResponse)
def analyze_decision_intelligence_route(
    request: DecisionIntelligenceRequest,
    db: Session = Depends(get_db),
):
    if db.get(Commodity, request.commodity_id) is None:
        raise HTTPException(status_code=404, detail="Commodity not found")
    if db.get(Market, request.origin_market_id) is None:
        raise HTTPException(status_code=404, detail="Origin market not found")
    market_names: dict[str, str] = {}
    observations_by_market = defaultdict(list)
    candidate_market_ids = []
    for candidate in request.candidates:
        market = db.get(Market, candidate.market_id)
        if market is None:
            raise HTTPException(status_code=404, detail=f"Candidate market not found: {candidate.market_id}")
        market_names[candidate.market_id] = market.name
        candidate_market_ids.append(candidate.market_id)
    if candidate_market_ids:
        observations = get_historical_prices(
            db=db,
            commodity_id=request.commodity_id,
            market_ids=candidate_market_ids,
            start_date=request.start_date,
            end_date=request.end_date,
        )
        for observation in observations:
            observations_by_market[observation.market_id].append(observation)
    try:
        return analyze_decision_intelligence(request, observations_by_market, market_names)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

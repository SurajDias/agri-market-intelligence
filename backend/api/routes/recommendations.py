from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.api.dependencies import get_db
from backend.engine.recommendation import analyze_recommendation
from backend.models.commodity import Commodity
from backend.models.market import Market
from backend.schemas.recommendation import RecommendationRequest, RecommendationResponse


router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])


@router.post("/analyze", response_model=RecommendationResponse)
def analyze_market_recommendations(
    request: RecommendationRequest,
    db: Session = Depends(get_db),
):
    if db.get(Commodity, request.commodity_id) is None:
        raise HTTPException(status_code=404, detail="Commodity not found")
    origin = db.get(Market, request.origin_market_id)
    if origin is None:
        raise HTTPException(status_code=404, detail="Origin market not found")

    market_names: dict[str, str] = {}
    for candidate in request.candidates:
        market = db.get(Market, candidate.market_id)
        if market is None:
            raise HTTPException(status_code=404, detail=f"Candidate market not found: {candidate.market_id}")
        market_names[candidate.market_id] = market.name
    return analyze_recommendation(request, market_names)

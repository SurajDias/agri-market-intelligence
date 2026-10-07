from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.api.dependencies import get_db
from backend.engine.simulator import simulate
from backend.models.commodity import Commodity
from backend.models.market import Market
from backend.schemas.simulator import SimulatorRequest, SimulatorResponse


router = APIRouter(prefix="/api/simulator", tags=["simulator"])


@router.post("/analyze", response_model=SimulatorResponse)
def analyze_simulation(request: SimulatorRequest, db: Session = Depends(get_db)):
    if db.get(Commodity, request.commodity_id) is None:
        raise HTTPException(status_code=404, detail="Commodity not found")
    if db.get(Market, request.origin_market_id) is None:
        raise HTTPException(status_code=404, detail="Origin market not found")
    market_names = {}
    for candidate in request.candidates:
        market = db.get(Market, candidate.market_id)
        if market is None:
            raise HTTPException(status_code=404, detail=f"Candidate market not found: {candidate.market_id}")
        market_names[candidate.market_id] = market.name
    try:
        return simulate(request, market_names)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.api.dependencies import get_db
from backend.api.routes.historical_prices import _validate_request
from backend.models.commodity import Commodity
from backend.models.market import Market
from backend.schemas.evidence import EvidenceAssessmentRequest, EvidenceAssessmentResponse
from backend.services.historical_prices import get_historical_prices
from backend.engine.evidence import assess_evidence


router = APIRouter(prefix="/api/evidence", tags=["evidence"])


@router.post("/assess", response_model=EvidenceAssessmentResponse)
def assess_market_evidence(
    request: EvidenceAssessmentRequest,
    db: Session = Depends(get_db),
):
    _validate_request(db, request.commodity_id, request.market_id, None, request.start_date, request.end_date)
    observations = get_historical_prices(
        db=db,
        commodity_id=request.commodity_id,
        market_id=request.market_id,
        start_date=request.start_date,
        end_date=request.end_date,
    )
    try:
        return assess_evidence(request, observations)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

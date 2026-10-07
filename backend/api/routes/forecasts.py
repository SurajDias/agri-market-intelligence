from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.api.dependencies import get_db
from backend.api.routes.historical_prices import _validate_request
from backend.schemas.forecast import ForecastEvaluationResponse
from backend.services.forecasting import evaluate_history, prepare_history
from backend.services.historical_prices import get_historical_prices


router = APIRouter(prefix="/api", tags=["forecasts"])


@router.get("/forecasts/evaluate", response_model=ForecastEvaluationResponse)
def evaluate_forecast(
    commodity_id: str,
    market_id: str,
    start_date: date,
    end_date: date,
    horizon: int = 1,
    db: Session = Depends(get_db),
):
    if not 1 <= horizon <= 30:
        raise HTTPException(status_code=422, detail="horizon must be between 1 and 30")
    _validate_request(db, commodity_id, market_id, None, start_date, end_date)
    observations = get_historical_prices(
        db=db,
        commodity_id=commodity_id,
        market_id=market_id,
        start_date=start_date,
        end_date=end_date,
    )
    return evaluate_history(
        prepare_history(observations),
        commodity_id,
        market_id,
        start_date,
        end_date,
        horizon,
    )

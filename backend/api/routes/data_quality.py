from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.api.dependencies import get_db
from backend.schemas.data_quality import DataQualitySummaryResponse
from backend.services.data_quality import build_data_quality_summary

router = APIRouter(prefix="/api/data-quality", tags=["data-quality"])


@router.get("/summary", response_model=DataQualitySummaryResponse)
def data_quality_summary(
    commodity_id: str | None = None,
    market_id: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    reference_datetime: datetime | None = None,
    db: Session = Depends(get_db),
):
    if start_date and end_date and start_date > end_date:
        raise HTTPException(status_code=422, detail="start_date must not be after end_date")
    if reference_datetime is None:
        raise HTTPException(status_code=422, detail="reference_datetime is required for deterministic results")
    try:
        return build_data_quality_summary(db, commodity_id=commodity_id, market_id=market_id, start_date=start_date, end_date=end_date, reference_datetime=reference_datetime)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

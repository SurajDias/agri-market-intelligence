from fastapi import APIRouter

from backend.engine.shelf_life import estimate_shelf_life
from backend.schemas.shelf_life import ShelfLifeEstimateRequest, ShelfLifeEstimateResponse


router = APIRouter(prefix="/api/shelf-life", tags=["shelf-life"])


@router.post("/estimate", response_model=ShelfLifeEstimateResponse)
def estimate_shelf_life_route(request: ShelfLifeEstimateRequest):
    return estimate_shelf_life(
        quantity_kg=request.quantity_kg,
        remaining_shelf_life_days=request.remaining_shelf_life_days,
        transit_time_days=request.transit_time_days,
        baseline_spoilage_rate_per_day=request.baseline_spoilage_rate_per_day,
        handling_buffer_days=request.handling_buffer_days,
    )

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.api.dependencies import get_db
from backend.engine.transport_cost import calculate_transport_cost
from backend.models.market import Market
from backend.schemas.transport import TransportCostRequest, TransportCostResponse


router = APIRouter(prefix="/api/transport", tags=["transport"])


@router.post("/calculate", response_model=TransportCostResponse)
def calculate_transport(request: TransportCostRequest, db: Session = Depends(get_db)):
    origin = db.get(Market, request.origin_market_id)
    if origin is None:
        raise HTTPException(status_code=404, detail="Origin market not found")

    destination = db.get(Market, request.destination_market_id)
    if destination is None:
        raise HTTPException(status_code=404, detail="Destination market not found")

    return calculate_transport_cost(
        origin=request.origin_market_id,
        destination=request.destination_market_id,
        quantity_kg=request.quantity_kg,
        distance_km=request.distance_km,
        transport_rate_per_km_per_kg=request.transport_rate_per_km_per_kg,
    )

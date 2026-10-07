from fastapi import APIRouter

from backend.engine.decision_engine import calculate_expected_net_value
from backend.schemas.decision import DecisionValueRequest, DecisionValueResponse


router = APIRouter(prefix="/api/decision", tags=["decision"])


@router.post("/calculate", response_model=DecisionValueResponse)
def calculate_decision_value(request: DecisionValueRequest):
    return calculate_expected_net_value(
        quantity_kg=request.quantity_kg,
        expected_selling_price_per_kg=request.expected_selling_price_per_kg,
        transport_cost=request.transport_cost,
        estimated_spoilage_kg=request.estimated_spoilage_kg,
        shelf_life_status=request.shelf_life_status,
    )

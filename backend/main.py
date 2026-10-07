from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.api.routes.markets import router as markets_router
from backend.api.routes.historical_prices import router as historical_prices_router
from backend.api.routes.historical_analytics import router as historical_analytics_router
from backend.api.routes.baseline_forecasts import router as baseline_forecasts_router
from backend.api.routes.forecasts import router as forecasts_router
from backend.api.routes.transport import router as transport_router
from backend.api.routes.shelf_life import router as shelf_life_router
from backend.api.routes.decision import router as decision_router
from backend.api.routes.recommendations import router as recommendations_router
from backend.api.routes.evidence import router as evidence_router
from backend.api.routes.simulator import router as simulator_router
from backend.api.routes.decision_intelligence import router as decision_intelligence_router
from backend.api.routes.data_quality import router as data_quality_router
from backend.core.config import settings
from backend.core.db import check_database_connection

app = FastAPI(
    title="Agricultural Market Intelligence API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=True,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(markets_router)
app.include_router(historical_prices_router)
app.include_router(historical_analytics_router)
app.include_router(baseline_forecasts_router)
app.include_router(forecasts_router)
app.include_router(transport_router)
app.include_router(shelf_life_router)
app.include_router(decision_router)
app.include_router(recommendations_router)
app.include_router(evidence_router)
app.include_router(simulator_router)
app.include_router(decision_intelligence_router)
app.include_router(data_quality_router)


@app.get("/api/health", tags=["health"])
def health_check():
    if check_database_connection():
        return {"status": "ok", "database": "connected"}
    return JSONResponse(
        status_code=503,
        content={"status": "unavailable", "database": "unavailable"},
    )

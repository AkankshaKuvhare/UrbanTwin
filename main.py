"""UrbanTwin Research Platform - Main FastAPI Application Entrypoint.

Exposes REST APIs for system status, pipeline triggering, and model evaluation.
"""

from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict
from fastapi import Depends, FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from config.logging import get_logger, setup_logging
from config.settings import settings
from database.session import get_async_db
from pipelines.scheduler import app_scheduler

# Initialize structured logging
setup_logging()
logger = get_logger("urbantwin.api")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager handling startup and shutdown events."""
    logger.info(
        "Starting UrbanTwin API service",
        environment=settings.ENVIRONMENT,
        data_mode=settings.DATA_MODE,
        debug=settings.DEBUG,
    )
    # Start background scheduler if enabled
    app_scheduler.start()
    
    yield

    # Clean shutdown
    logger.info("Shutting down UrbanTwin API service")
    app_scheduler.shutdown()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Research monorepo for causal analysis between traffic congestion and urban air quality in Pune.",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Dashboard Routers
from dashboard.historical_aqi import router as dashboard_router
from dashboard.fusion import router as fusion_router
from dashboard.forecasting import router as forecasting_router
from dashboard.traffic import router as traffic_router
from analytics.dashboard import router as relationships_dashboard_router
from analytics.api import api_router as relationships_api_router

app.include_router(dashboard_router)
app.include_router(fusion_router)
app.include_router(forecasting_router)
app.include_router(traffic_router)
app.include_router(relationships_dashboard_router)
app.include_router(relationships_api_router)


@app.get("/", tags=["General"])
async def root() -> Dict[str, Any]:
    """Root metadata endpoint."""
    return {
        "project": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "data_mode": settings.DATA_MODE,
        "status": "operational",
    }


@app.get("/health", tags=["Health"])
async def health_check() -> Dict[str, str]:
    """Basic liveness health endpoint."""
    return {"status": "healthy"}


@app.get(f"{settings.API_V1_PREFIX}/health", tags=["Health"])
async def detailed_health_check(
    db: AsyncSession = Depends(get_async_db),
) -> Dict[str, Any]:
    """Detailed readiness health check verifying database and configuration state."""
    db_status = "connected"
    try:
        await db.execute(text("SELECT 1"))
    except Exception as exc:
        logger.error("Database health check probe failed", error=str(exc))
        db_status = f"unhealthy: {str(exc)}"

    return {
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "data_mode": settings.DATA_MODE,
        "database": db_status,
        "scheduler_running": app_scheduler._is_running,
        "pune_bbox": {
            "min_lat": settings.PUNE_BBOX_MIN_LAT,
            "max_lat": settings.PUNE_BBOX_MAX_LAT,
            "min_lon": settings.PUNE_BBOX_MIN_LON,
            "max_lon": settings.PUNE_BBOX_MAX_LON,
        },
    }


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "collect-traffic":
        from pipelines.traffic import TrafficCollectionPipeline
        print("Running TomTom Traffic Collector CLI...")
        pipeline = TrafficCollectionPipeline()
        res = pipeline.execute()
        print(f"Collection status: {'SUCCESS' if res.success else 'FAILED'}")
        if res.success:
            print("Metrics:", res.metrics)
        else:
            print("Error:", res.error_message)
    else:
        import uvicorn
        uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)

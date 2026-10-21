"""Dashboard package for UrbanTwin."""

from dashboard.app import DashboardManager
from dashboard.historical_aqi import (
    router as dashboard_router,
    build_historical_aqi_dashboard_html,
    get_dashboard_data,
    export_standalone_dashboard,
)
from dashboard.fusion import (
    router as fusion_router,
    build_fusion_dashboard_html,
    export_fusion_dashboard_html,
)
from dashboard.forecasting import (
    router as forecasting_router,
    build_forecasting_dashboard_html,
    export_forecasting_dashboard_html,
)

__all__ = [
    "DashboardManager",
    "dashboard_router",
    "fusion_router",
    "forecasting_router",
    "build_historical_aqi_dashboard_html",
    "get_dashboard_data",
    "export_standalone_dashboard",
    "build_fusion_dashboard_html",
    "export_fusion_dashboard_html",
    "build_forecasting_dashboard_html",
    "export_forecasting_dashboard_html",
]

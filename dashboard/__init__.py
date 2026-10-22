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
from dashboard.traffic import (
    router as traffic_router,
    build_traffic_dashboard_html,
    export_traffic_dashboard_html,
)
from analytics.dashboard import (
    router as relationships_router,
    build_relationships_dashboard_html,
    export_relationships_dashboard_html,
)
from gis.dashboard import (
    router as gis_router,
    build_gis_dashboard_html,
    export_gis_dashboard_html,
)
from simulator.dashboard import (
    router as simulator_router,
    build_simulator_dashboard_html,
    generate_simulation_reports,
)

__all__ = [
    "DashboardManager",
    "dashboard_router",
    "fusion_router",
    "forecasting_router",
    "traffic_router",
    "relationships_router",
    "gis_router",
    "simulator_router",
    "build_historical_aqi_dashboard_html",
    "get_dashboard_data",
    "export_standalone_dashboard",
    "build_fusion_dashboard_html",
    "export_fusion_dashboard_html",
    "build_forecasting_dashboard_html",
    "export_forecasting_dashboard_html",
    "build_traffic_dashboard_html",
    "export_traffic_dashboard_html",
    "build_relationships_dashboard_html",
    "export_relationships_dashboard_html",
    "build_gis_dashboard_html",
    "export_gis_dashboard_html",
    "build_simulator_dashboard_html",
    "generate_simulation_reports",
]

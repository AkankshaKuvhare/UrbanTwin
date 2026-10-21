"""Relationship Analytics package for UrbanTwin Milestone 8."""

from analytics.correlation import (
    compute_correlation_matrices,
    compute_correlation_summary,
    export_correlation_reports,
    generate_correlation_heatmap_fig,
    get_active_variables,
)
from analytics.dashboard import (
    build_relationships_dashboard_html,
    export_relationships_dashboard_html,
    router as relationships_dashboard_router,
)
from analytics.api import api_router as relationships_api_router
from analytics.feature_importance import (
    compute_or_load_feature_importance,
    export_importance_reports,
    generate_feature_importance_fig,
    get_attribution_summary,
)
from analytics.network_graph import (
    build_network_graph_data,
    export_network_reports,
    generate_network_graph_fig,
)
from analytics.scatter_analysis import (
    compute_scatter_statistics,
    export_scatter_reports,
    generate_single_scatter_fig,
    get_active_scatter_pairs,
)
from analytics.seasonality import (
    compute_all_variables_seasonality,
    compute_seasonality_aggregates,
    export_seasonality_reports,
    generate_seasonality_figures,
)
from analytics.time_series_analysis import (
    generate_synchronized_timeline_fig,
    resample_time_series,
)

__all__ = [
    "compute_correlation_matrices",
    "compute_correlation_summary",
    "export_correlation_reports",
    "generate_correlation_heatmap_fig",
    "get_active_variables",
    "compute_scatter_statistics",
    "export_scatter_reports",
    "generate_single_scatter_fig",
    "get_active_scatter_pairs",
    "resample_time_series",
    "generate_synchronized_timeline_fig",
    "compute_seasonality_aggregates",
    "compute_all_variables_seasonality",
    "generate_seasonality_figures",
    "export_seasonality_reports",
    "build_network_graph_data",
    "generate_network_graph_fig",
    "export_network_reports",
    "compute_or_load_feature_importance",
    "get_attribution_summary",
    "generate_feature_importance_fig",
    "export_importance_reports",
    "build_relationships_dashboard_html",
    "export_relationships_dashboard_html",
    "relationships_dashboard_router",
    "relationships_api_router",
]

"""FastAPI REST Endpoints for UrbanTwin Milestone 8 Relationship Analytics.

Mounted under /api/v1/relationships:
- GET /api/v1/relationships/correlation
- GET /api/v1/relationships/network
- GET /api/v1/relationships/scatter
- GET /api/v1/relationships/seasonality
- GET /api/v1/relationships/timeseries
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Query
import pandas as pd

from analytics.correlation import (
    compute_correlation_matrices,
    compute_correlation_summary,
    get_active_variables,
    TRAFFIC_VARIABLES,
)
from analytics.dashboard import load_analytical_dataset
from analytics.network_graph import build_network_graph_data
from analytics.scatter_analysis import (
    compute_scatter_statistics,
    get_active_scatter_pairs,
)
from analytics.seasonality import (
    compute_all_variables_seasonality,
    compute_seasonality_aggregates,
)
from analytics.time_series_analysis import resample_time_series

api_router = APIRouter(prefix="/api/v1/relationships", tags=["relationships_api"])


@api_router.get("/correlation")
async def get_correlation_data(
    method: str = Query("pearson", description="Correlation method: pearson, spearman, or kendall"),
    station_id: Optional[str] = Query(None, description="Optional station ID filter"),
) -> Dict[str, Any]:
    """Retrieve pairwise correlation matrices and summary statistics."""
    df = load_analytical_dataset(station_id=station_id)
    matrices = compute_correlation_matrices(df)
    summary_df = compute_correlation_summary(df, target="aqi")

    selected_matrix = matrices.get(method.lower(), matrices.get("pearson"))

    return {
        "method": method.lower(),
        "station_id": station_id or "all",
        "active_variables": list(selected_matrix.columns) if not selected_matrix.empty else [],
        "matrix": selected_matrix.to_dict() if not selected_matrix.empty else {},
        "target_summary": summary_df.to_dict(orient="records") if not summary_df.empty else [],
        "traffic_included": any(v in selected_matrix.columns for v in TRAFFIC_VARIABLES) if not selected_matrix.empty else False,
    }


@api_router.get("/network")
async def get_network_data(
    threshold: float = Query(0.20, ge=0.0, le=1.0, description="Minimum correlation |r| for edges"),
    station_id: Optional[str] = Query(None, description="Optional station ID filter"),
) -> Dict[str, Any]:
    """Retrieve force-directed network graph topology (nodes, edges, centrality)."""
    df = load_analytical_dataset(station_id=station_id)
    data = build_network_graph_data(df, threshold=threshold)

    return {
        "station_id": station_id or "all",
        "threshold": threshold,
        "nodes": data["nodes"],
        "edges": data["edges"],
        "stats": data["stats"],
    }


@api_router.get("/scatter")
async def get_scatter_data(
    x_var: Optional[str] = Query(None, description="Independent variable (e.g. pm25, temperature_2m)"),
    y_var: str = Query("aqi", description="Dependent variable (default: aqi)"),
    sample_limit: int = Query(500, description="Maximum sample points returned"),
    station_id: Optional[str] = Query(None, description="Optional station ID filter"),
) -> Dict[str, Any]:
    """Retrieve regression statistics and sample scatter points."""
    df = load_analytical_dataset(station_id=station_id)
    all_stats_df = compute_scatter_statistics(df)

    points = []
    reg_stats = {}

    if x_var and x_var in df.columns and y_var in df.columns:
        sub = df[[x_var, y_var]].dropna().head(sample_limit)
        points = [{"x": float(r[x_var]), "y": float(r[y_var])} for _, r in sub.iterrows()]

        stat_row = all_stats_df[all_stats_df["x_variable"] == x_var]
        if not stat_row.empty:
            reg_stats = stat_row.iloc[0].to_dict()

    return {
        "x_variable": x_var,
        "y_variable": y_var,
        "station_id": station_id or "all",
        "regression_stats": reg_stats,
        "all_pairs_summary": all_stats_df.to_dict(orient="records"),
        "points": points,
    }


@api_router.get("/seasonality")
async def get_seasonality_data(
    target: str = Query("aqi", description="Variable to aggregate"),
    station_id: Optional[str] = Query(None, description="Optional station ID filter"),
) -> Dict[str, Any]:
    """Retrieve monthly, weekly, and day-of-week seasonal cyclical profiles."""
    df = load_analytical_dataset(station_id=station_id)
    aggs = compute_seasonality_aggregates(df, target_col=target)

    return {
        "target_variable": target,
        "station_id": station_id or "all",
        "monthly": aggs["monthly"].to_dict(orient="records"),
        "weekly": aggs["weekly"].to_dict(orient="records"),
        "day_of_week": aggs["day_of_week"].to_dict(orient="records"),
        "month_dow_matrix": aggs["month_dow_pivot"].to_dict(),
    }


@api_router.get("/timeseries")
async def get_timeseries_data(
    freq: str = Query("D", description="Resampling frequency: D (daily), W (weekly), ME (monthly), YE (yearly)"),
    variables: Optional[List[str]] = Query(None, description="List of columns to resample"),
    station_id: Optional[str] = Query(None, description="Optional station ID filter"),
) -> Dict[str, Any]:
    """Retrieve synchronized multi-variable aggregated time-series observations."""
    df = load_analytical_dataset(station_id=station_id)
    resampled = resample_time_series(df, freq=freq, variables=variables)

    records = []
    if not resampled.empty:
        resampled_reset = resampled.reset_index()
        time_col = resampled_reset.columns[0]
        for _, r in resampled_reset.iterrows():
            item = {"timestamp": str(r[time_col])}
            for col in resampled.columns:
                val = r[col]
                item[col] = None if (val is None or pd.isna(val)) else round(float(val), 2)
            records.append(item)

    return {
        "frequency": freq,
        "station_id": station_id or "all",
        "variables": list(resampled.columns),
        "total_intervals": len(records),
        "data": records,
    }

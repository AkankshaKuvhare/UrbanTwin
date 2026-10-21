"""Time-Series Analysis Module for UrbanTwin Milestone 8.

Synchronizes and aggregates AQI, Meteorological Covariates, and (when available)
Traffic Flow Conditions across standardized temporal intervals:
- Daily ('D')
- Weekly ('W')
- Monthly ('M')
- Yearly ('Y')

Provides:
- Multi-tier temporal resampling with missingness tracking
- Synchronized multi-axis Plotly timeline with range sliders
- Summary temporal statistics and variance profiles
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from analytics.correlation import (
    DEFAULT_VARIABLE_LABELS,
    POLLUTANT_VARIABLES,
    WEATHER_VARIABLES,
    TRAFFIC_VARIABLES,
    get_active_variables,
)
from config.logging import get_logger

logger = get_logger("urbantwin.analytics.timeseries")

FREQ_MAP: Dict[str, str] = {
    "daily": "D",
    "weekly": "W",
    "monthly": "ME",  # modern pandas month-end
    "yearly": "YE",   # modern pandas year-end
    "d": "D",
    "w": "W",
    "m": "ME",
    "y": "YE",
}


def prepare_datetime_index(df: pd.DataFrame, dt_col: Optional[str] = None) -> pd.DataFrame:
    """Ensure DataFrame has a valid DatetimeIndex sorted chronologically."""
    df_copy = df.copy()
    candidate_cols = ["observation_datetime", "observation_date", "timestamp", "datetime", "date"]
    
    if dt_col and dt_col in df_copy.columns:
        date_col = dt_col
    else:
        date_col = next((c for c in candidate_cols if c in df_copy.columns), None)

    if date_col is None:
        raise ValueError(f"No valid datetime column found in {list(df_copy.columns)}")

    df_copy["_dt"] = pd.to_datetime(df_copy[date_col], errors="coerce")
    df_clean = df_copy.dropna(subset=["_dt"]).sort_values("_dt").set_index("_dt")
    return df_clean


def resample_time_series(
    df: pd.DataFrame,
    freq: str = "D",
    variables: Optional[List[str]] = None,
    agg: str = "mean",
) -> pd.DataFrame:
    """Resample multi-variable time series to standard frequency (D, W, ME, YE).

    Args:
        df: Input DataFrame with datetime column.
        freq: Resampling frequency ('daily'/'D', 'weekly'/'W', 'monthly'/'ME', 'yearly'/'YE').
        variables: Numeric variables to resample. If None, active variables are selected.
        agg: Aggregation method ('mean', 'median', 'max').

    Returns:
        Resampled DataFrame with datetime index.
    """
    clean_df = prepare_datetime_index(df)
    target_vars = variables or get_active_variables(clean_df)
    numeric_df = clean_df[target_vars].apply(pd.to_numeric, errors="coerce")

    standard_freq = FREQ_MAP.get(freq.lower(), freq)

    if agg == "median":
        resampled = numeric_df.resample(standard_freq).median()
    elif agg == "max":
        resampled = numeric_df.resample(standard_freq).max()
    else:
        resampled = numeric_df.resample(standard_freq).mean()

    # Drop time bins where all variables are NaN
    resampled = resampled.dropna(how="all")
    return resampled


def generate_synchronized_timeline_fig(
    df: pd.DataFrame,
    variables: Optional[List[str]] = None,
    freq: str = "D",
    dark_mode: bool = True,
) -> go.Figure:
    """Generate an interactive synchronized multi-panel Plotly timeline.

    Plots:
    - Panel 1: Primary Air Quality Target (AQI & PM2.5/PM10)
    - Panel 2: Key Meteorological Drivers (Temperature, Humidity, Wind Speed)
    - Panel 3: Traffic Conditions (if non-null data exists)
    """
    resampled = resample_time_series(df, freq=freq, variables=variables)
    if resampled.empty:
        fig = go.Figure()
        fig.add_annotation(text="No data available for time-series timeline", showarrow=False)
        return fig

    # Check whether traffic variables are non-empty
    has_traffic = any(v in resampled.columns and resampled[v].notna().sum() > 0 for v in TRAFFIC_VARIABLES)

    rows = 3 if has_traffic else 2
    row_heights = [0.55, 0.45] if rows == 2 else [0.4, 0.35, 0.25]
    subplot_titles = [
        "Air Quality Index & Core Pollutants",
        "Synchronized Meteorological Covariates",
    ]
    if has_traffic:
        subplot_titles.append("Arterial Traffic Flow Conditions")

    fig = make_subplots(
        rows=rows,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        subplot_titles=subplot_titles,
        row_heights=row_heights,
    )

    bg_color = "#0f172a" if dark_mode else "#ffffff"
    text_color = "#f8fafc" if dark_mode else "#1e293b"
    grid_color = "#334155" if dark_mode else "#e2e8f0"

    x_dates = resampled.index

    # 1. AQI & Pollutants
    palette_pollutants = {
        "aqi": "#f59e0b",
        "pm25": "#ef4444",
        "pm10": "#8b5cf6",
        "no2": "#3b82f6",
    }
    for col, color in palette_pollutants.items():
        if col in resampled.columns and resampled[col].notna().sum() > 0:
            fig.add_trace(
                go.Scatter(
                    x=x_dates,
                    y=resampled[col],
                    name=DEFAULT_VARIABLE_LABELS.get(col, col),
                    mode="lines",
                    line=dict(color=color, width=2 if col == "aqi" else 1.2),
                ),
                row=1,
                col=1,
            )

    # 2. Weather
    palette_weather = {
        "temperature_2m": "#f97316",
        "relative_humidity_2m": "#06b6d4",
        "wind_speed_10m": "#10b981",
        "surface_pressure": "#a855f7",
    }
    for col, color in palette_weather.items():
        if col in resampled.columns and resampled[col].notna().sum() > 0:
            fig.add_trace(
                go.Scatter(
                    x=x_dates,
                    y=resampled[col],
                    name=DEFAULT_VARIABLE_LABELS.get(col, col),
                    mode="lines",
                    line=dict(color=color, width=1.5),
                ),
                row=2,
                col=1,
            )

    # 3. Traffic (if present)
    if has_traffic:
        palette_traffic = {
            "traffic_speed": "#22c55e",
            "traffic_congestion": "#e11d48",
            "traffic_travel_time": "#eab308",
        }
        for col, color in palette_traffic.items():
            if col in resampled.columns and resampled[col].notna().sum() > 0:
                fig.add_trace(
                    go.Scatter(
                        x=x_dates,
                        y=resampled[col],
                        name=DEFAULT_VARIABLE_LABELS.get(col, col),
                        mode="lines",
                        line=dict(color=color, width=1.5),
                    ),
                    row=3,
                    col=1,
                )

    fig.update_layout(
        title=dict(
            text=f"<b>Synchronized UrbanTwin Time-Series Explorer</b> ({freq.upper()} Aggregation)",
            font=dict(color=text_color, size=16),
        ),
        paper_bgcolor=bg_color,
        plot_bgcolor=bg_color,
        font=dict(color=text_color, family="Inter, system-ui, sans-serif"),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            font=dict(color=text_color, size=11),
        ),
        height=750 if rows == 3 else 620,
        margin=dict(l=60, r=40, t=100, b=60),
    )

    for r in range(1, rows + 1):
        fig.update_xaxes(gridcolor=grid_color, showgrid=True, row=r, col=1)
        fig.update_yaxes(gridcolor=grid_color, showgrid=True, row=r, col=1)

    # Add range slider to bottom axis
    fig.update_xaxes(
        rangeslider=dict(visible=True, bgcolor=bg_color, thickness=0.05),
        row=rows,
        col=1,
    )

    return fig

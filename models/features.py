"""Feature Engineering Pipeline for UrbanTwin AQI Forecasting.

Generates calendar, lag, rolling, weather, and traffic-ready features
from the fused_zone_time master analytical dataset.

The pipeline automatically detects and includes traffic features when
they become available (non-null). No code changes are required when
traffic data is integrated.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Feature Group Definitions
# ---------------------------------------------------------------------------

CALENDAR_FEATURES = [
    "hour", "day_of_month", "day_of_week", "month", "quarter",
    "season", "is_weekend",
]

AQI_LAG_DAYS = [1, 2, 3, 7, 14, 30]

ROLLING_WINDOWS = [3, 7, 14, 30]

WEATHER_FEATURES = [
    "temperature_2m",
    "relative_humidity_2m",
    "wind_speed_10m",
    "surface_pressure",
    "precipitation",
    "boundary_layer_height",
]

TRAFFIC_FEATURES = [
    "traffic_speed",
    "traffic_congestion",
    "traffic_travel_time",
    "traffic_confidence",
]

TARGET_COLUMN = "aqi"


def _month_to_season(month: int) -> int:
    """Map month number to meteorological season for South Asia.

    Winter=0 (Dec-Feb), Pre-monsoon=1 (Mar-May),
    Monsoon=2 (Jun-Sep), Post-monsoon=3 (Oct-Nov).
    """
    if month in (12, 1, 2):
        return 0
    elif month in (3, 4, 5):
        return 1
    elif month in (6, 7, 8, 9):
        return 2
    else:
        return 3


# ---------------------------------------------------------------------------
# Calendar Features
# ---------------------------------------------------------------------------

def build_calendar_features(df: pd.DataFrame, dt_col: str = "observation_datetime") -> pd.DataFrame:
    """Extract calendar and cyclical time features from the observation timestamp.

    Args:
        df: DataFrame containing a datetime column.
        dt_col: Name of the datetime column.

    Returns:
        DataFrame with calendar feature columns appended.
    """
    out = df.copy()
    dt = pd.to_datetime(out[dt_col])

    out["hour"] = dt.dt.hour
    out["day_of_month"] = dt.dt.day
    out["day_of_week"] = dt.dt.dayofweek  # 0=Monday ... 6=Sunday
    out["month"] = dt.dt.month
    out["quarter"] = dt.dt.quarter
    out["season"] = out["month"].apply(_month_to_season)
    out["is_weekend"] = (out["day_of_week"] >= 5).astype(int)

    return out


# ---------------------------------------------------------------------------
# Lag Features
# ---------------------------------------------------------------------------

def build_lag_features(
    df: pd.DataFrame,
    target_col: str = TARGET_COLUMN,
    lag_days: Optional[List[int]] = None,
    group_col: str = "station_id",
) -> pd.DataFrame:
    """Create autoregressive lag features for the target variable.

    Args:
        df: DataFrame sorted by time within each group.
        target_col: Column to lag.
        lag_days: List of lag offsets in days (default: AQI_LAG_DAYS).
        group_col: Column to group by before shifting.

    Returns:
        DataFrame with lag columns appended (e.g. aqi_lag_1, aqi_lag_7).
    """
    out = df.copy()
    lags = lag_days or AQI_LAG_DAYS

    for lag in lags:
        col_name = f"{target_col}_lag_{lag}"
        out[col_name] = out.groupby(group_col)[target_col].shift(lag)

    return out


# ---------------------------------------------------------------------------
# Rolling Features
# ---------------------------------------------------------------------------

def build_rolling_features(
    df: pd.DataFrame,
    target_col: str = TARGET_COLUMN,
    windows: Optional[List[int]] = None,
    group_col: str = "station_id",
) -> pd.DataFrame:
    """Compute rolling mean and standard deviation features.

    To prevent data leakage during forecasting, the rolling window is computed
    strictly on PAST observations by shifting the target by 1 day first.

    Args:
        df: DataFrame sorted by time within each group.
        target_col: Column to compute rolling statistics on.
        windows: List of rolling window sizes in days.
        group_col: Column to group by.

    Returns:
        DataFrame with rolling mean/std columns appended.
    """
    out = df.copy()
    wins = windows or ROLLING_WINDOWS

    for w in wins:
        # Shift by 1 first so rolling window only includes past values, not the target itself!
        past_target = out.groupby(group_col)[target_col].shift(1)
        grouped = past_target.groupby(out[group_col])
        out[f"{target_col}_rolling_mean_{w}"] = grouped.transform(
            lambda x: x.rolling(window=w, min_periods=1).mean()
        )
        out[f"{target_col}_rolling_std_{w}"] = grouped.transform(
            lambda x: x.rolling(window=w, min_periods=1).std()
        )

    return out


# ---------------------------------------------------------------------------
# Weather Features
# ---------------------------------------------------------------------------

def build_weather_features(
    df: pd.DataFrame,
    weather_cols: Optional[List[str]] = None,
) -> pd.DataFrame:
    """Select and validate weather covariate columns.

    If any weather column is missing, it is created as NaN.

    Args:
        df: DataFrame potentially containing weather columns.
        weather_cols: List of weather feature names.

    Returns:
        DataFrame with weather columns ensured.
    """
    out = df.copy()
    cols = weather_cols or WEATHER_FEATURES

    for col in cols:
        if col not in out.columns:
            out[col] = np.nan

    return out


# ---------------------------------------------------------------------------
# Traffic Features (Future-Ready)
# ---------------------------------------------------------------------------

def build_traffic_features(
    df: pd.DataFrame,
    traffic_cols: Optional[List[str]] = None,
) -> pd.DataFrame:
    """Include traffic features if available, otherwise ensure nullable columns exist.

    This function requires ZERO code changes when traffic data becomes available.
    Traffic columns are already present in the fused_zone_time schema as nullable.
    When traffic data is ingested, these columns will automatically contain values
    and be included in the feature matrix.

    Args:
        df: DataFrame potentially containing traffic columns.
        traffic_cols: List of traffic feature names.

    Returns:
        DataFrame with traffic columns ensured (nullable if not yet available).
    """
    out = df.copy()
    cols = traffic_cols or TRAFFIC_FEATURES

    for col in cols:
        if col not in out.columns:
            out[col] = np.nan

    return out


def has_traffic_data(df: pd.DataFrame) -> bool:
    """Check if any traffic feature columns contain non-null data.

    Returns:
        True if at least one traffic column has any non-null values.
    """
    for col in TRAFFIC_FEATURES:
        if col in df.columns and df[col].notna().any():
            return True
    return False


# ---------------------------------------------------------------------------
# Full Feature Pipeline
# ---------------------------------------------------------------------------

def build_feature_matrix(
    df: pd.DataFrame,
    target_col: str = TARGET_COLUMN,
    include_traffic: bool = True,
    dt_col: str = "observation_datetime",
    group_col: str = "station_id",
) -> Tuple[pd.DataFrame, List[str]]:
    """Execute the complete feature engineering pipeline.

    Orchestrates calendar, lag, rolling, weather, and traffic feature generation.
    Returns the feature matrix and the list of feature column names.

    Args:
        df: Raw fused_zone_time DataFrame.
        target_col: Target variable column name.
        include_traffic: Whether to include traffic feature columns.
        dt_col: Datetime column name.
        group_col: Grouping column for lag/rolling computations.

    Returns:
        Tuple of (feature_enriched_df, feature_column_names).
    """
    # Ensure sorted by group and time
    out = df.sort_values([group_col, dt_col]).reset_index(drop=True)

    # Step 1: Calendar features
    out = build_calendar_features(out, dt_col=dt_col)

    # Step 2: Lag features
    out = build_lag_features(out, target_col=target_col, group_col=group_col)

    # Step 3: Rolling features
    out = build_rolling_features(out, target_col=target_col, group_col=group_col)

    # Step 4: Weather features
    out = build_weather_features(out)

    # Step 5: Traffic features (future-ready)
    if include_traffic:
        out = build_traffic_features(out)

    # Assemble feature column list
    feature_cols: List[str] = []

    # Calendar
    feature_cols.extend(CALENDAR_FEATURES)

    # Lags
    feature_cols.extend([f"{target_col}_lag_{d}" for d in AQI_LAG_DAYS])

    # Rolling
    for w in ROLLING_WINDOWS:
        feature_cols.extend([
            f"{target_col}_rolling_mean_{w}",
            f"{target_col}_rolling_std_{w}",
        ])

    # Weather
    feature_cols.extend([c for c in WEATHER_FEATURES if c in out.columns])

    # Traffic (only include columns that have data)
    if include_traffic:
        traffic_with_data = [c for c in TRAFFIC_FEATURES if c in out.columns and out[c].notna().any()]
        feature_cols.extend(traffic_with_data)

    # Deduplicate while preserving order
    seen = set()
    unique_features = []
    for f in feature_cols:
        if f not in seen:
            seen.add(f)
            unique_features.append(f)

    return out, unique_features


def get_feature_summary(df: pd.DataFrame, feature_cols: List[str]) -> pd.DataFrame:
    """Generate a summary of the feature matrix for reporting.

    Args:
        df: Feature-enriched DataFrame.
        feature_cols: List of feature column names.

    Returns:
        DataFrame with feature name, dtype, non-null count, null percentage, mean, std.
    """
    records = []
    for col in feature_cols:
        if col in df.columns:
            series = df[col]
            records.append({
                "feature": col,
                "dtype": str(series.dtype),
                "non_null_count": int(series.notna().sum()),
                "null_pct": round(series.isna().mean() * 100, 2),
                "mean": round(float(series.mean()), 4) if pd.api.types.is_numeric_dtype(series) else None,
                "std": round(float(series.std()), 4) if pd.api.types.is_numeric_dtype(series) else None,
                "min": round(float(series.min()), 4) if pd.api.types.is_numeric_dtype(series) else None,
                "max": round(float(series.max()), 4) if pd.api.types.is_numeric_dtype(series) else None,
            })
    return pd.DataFrame(records)

"""GIS Layer loaders for UrbanTwin.

Provides data-loading functions for each map layer:
  - Station layer  (AQI monitoring stations with latest pollutant data)
  - H3 zone layer  (Hexagonal grid colored by mean AQI)
  - Traffic layer  (TomTom monitoring points; auto-included when data exists)
  - Weather layer  (Latest weather observations per station/zone)

AQI thresholds follow India's CPCB/NAQI scale.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from config.logging import get_logger
from config.settings import settings

logger = get_logger("urbantwin.gis.layers")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
DATA_DIR = settings.DATA_DIR
FUSED_PATH = DATA_DIR / "fused_zone_time.parquet"
AQI_CSV = DATA_DIR / "all_stations_combined.csv"
WEATHER_PATH = DATA_DIR / "pune_historical_weather_hourly.parquet"
TRAFFIC_PATH = DATA_DIR / "traffic" / "traffic_observations.parquet"
TRAFFIC_POINTS_CFG = Path(settings.BASE_DIR) / "config" / "traffic_points.json"

# ---------------------------------------------------------------------------
# Station coordinates (matches spatial/snapping.py)
# ---------------------------------------------------------------------------
STATION_META: Dict[str, Dict[str, Any]] = {
    "11613": {
        "name": "Revenue Colony-Shivajinagar, Pune - IITM",
        "lat": 18.5314,
        "lon": 73.8446,
    },
    "3409439": {
        "name": "Savitribai Phule Pune University, Pune - MPCB",
        "lat": 18.5529,
        "lon": 73.8260,
    },
    "5661": {
        "name": "Karve Road Pune, Pune - MPCB",
        "lat": 18.5020,
        "lon": 73.8270,
    },
    "3409438": {
        "name": "Katraj Dairy, Pune - MPCB",
        "lat": 18.4550,
        "lon": 73.8580,
    },
    "3409436": {
        "name": "Park Street Wakad, Pimpri Chinchwad - MPCB",
        "lat": 18.6015,
        "lon": 73.7645,
    },
}

# ---------------------------------------------------------------------------
# AQI colour scale (India NAQI)
# ---------------------------------------------------------------------------
AQI_THRESHOLDS: List[tuple] = [
    (50, "#22c55e", "Good"),
    (100, "#84cc16", "Satisfactory"),
    (200, "#f59e0b", "Moderate"),
    (300, "#f97316", "Poor"),
    (400, "#ef4444", "Very Poor"),
    (float("inf"), "#7c3aed", "Severe"),
]


def get_aqi_color(aqi_value: Optional[float]) -> str:
    """Return hex colour for a given AQI value (India NAQI scale)."""
    if aqi_value is None or (isinstance(aqi_value, float) and np.isnan(aqi_value)):
        return "#94a3b8"  # slate-400 for missing
    for threshold, color, _ in AQI_THRESHOLDS:
        if aqi_value <= threshold:
            return color
    return "#7c3aed"


def get_aqi_category(aqi_value: Optional[float]) -> str:
    """Return textual AQI category for a given AQI value."""
    if aqi_value is None or (isinstance(aqi_value, float) and np.isnan(aqi_value)):
        return "Unknown"
    for threshold, _, category in AQI_THRESHOLDS:
        if aqi_value <= threshold:
            return category
    return "Severe"


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _safe_round(val: Any, decimals: int = 1) -> Optional[float]:
    """Return rounded float or None if not numeric."""
    try:
        v = float(val)
        return round(v, decimals) if not np.isnan(v) else None
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------------------
# Station Layer
# ---------------------------------------------------------------------------

def load_station_layer() -> pd.DataFrame:
    """Load AQI station layer with latest pollutant readings.

    Returns a DataFrame with columns:
        station_id, name, lat, lon, aqi, pm25, pm10, no2, co, so2, o3,
        aqi_color, aqi_category, last_updated, record_count
    """
    pollutant_cols = ["pm25", "pm10", "no2", "co", "so2", "o3"]
    rows: List[Dict[str, Any]] = []

    try:
        if FUSED_PATH.exists():
            df = pd.read_parquet(FUSED_PATH)
            # Normalise column names
            df.columns = [c.lower() for c in df.columns]
            # Map pm2.5 → pm25 if needed
            if "pm2.5" in df.columns and "pm25" not in df.columns:
                df = df.rename(columns={"pm2.5": "pm25"})

            for sid, meta in STATION_META.items():
                sub = df[df["station_id"].astype(str) == str(sid)] if "station_id" in df.columns else pd.DataFrame()
                if sub.empty and AQI_CSV.exists():
                    csv_df = pd.read_csv(AQI_CSV)
                    csv_df.columns = [c.lower() for c in csv_df.columns]
                    sub = csv_df[csv_df["station_id"].astype(str) == str(sid)]

                if sub.empty:
                    aqi_val = None
                    last_updated = None
                    record_count = 0
                    poll_vals = {c: None for c in pollutant_cols}
                else:
                    # Latest record
                    time_col = next(
                        (c for c in ["observation_datetime", "datetime", "date", "timestamp"] if c in sub.columns),
                        None,
                    )
                    if time_col:
                        sub = sub.sort_values(time_col, ascending=False)
                    latest = sub.iloc[0]
                    aqi_val = _safe_round(latest.get("aqi", None))
                    last_updated = str(latest[time_col]) if time_col else None
                    record_count = len(sub)
                    poll_vals = {c: _safe_round(latest.get(c, None)) for c in pollutant_cols}

                rows.append(
                    {
                        "station_id": sid,
                        "name": meta["name"],
                        "lat": meta["lat"],
                        "lon": meta["lon"],
                        "aqi": aqi_val,
                        **poll_vals,
                        "aqi_color": get_aqi_color(aqi_val),
                        "aqi_category": get_aqi_category(aqi_val),
                        "last_updated": last_updated,
                        "record_count": record_count,
                    }
                )
        else:
            # Fallback: static metadata only
            for sid, meta in STATION_META.items():
                rows.append(
                    {
                        "station_id": sid,
                        "name": meta["name"],
                        "lat": meta["lat"],
                        "lon": meta["lon"],
                        "aqi": None,
                        **{c: None for c in pollutant_cols},
                        "aqi_color": get_aqi_color(None),
                        "aqi_category": "Unknown",
                        "last_updated": None,
                        "record_count": 0,
                    }
                )

        result = pd.DataFrame(rows)
        logger.info("Loaded station layer", stations=len(result))
        return result

    except Exception as exc:
        logger.error("Failed to load station layer", error=str(exc))
        return pd.DataFrame(
            [
                {
                    "station_id": sid,
                    "name": meta["name"],
                    "lat": meta["lat"],
                    "lon": meta["lon"],
                    "aqi": None,
                    **{c: None for c in ["pm25", "pm10", "no2", "co", "so2", "o3"]},
                    "aqi_color": "#94a3b8",
                    "aqi_category": "Unknown",
                    "last_updated": None,
                    "record_count": 0,
                }
                for sid, meta in STATION_META.items()
            ]
        )


# ---------------------------------------------------------------------------
# H3 Zone Layer
# ---------------------------------------------------------------------------

def load_h3_layer() -> pd.DataFrame:
    """Load H3 hexagonal zone layer with mean AQI per cell.

    Returns a DataFrame with columns:
        zone_id, centroid_lat, centroid_lon, mean_aqi, aqi_color, aqi_category,
        record_count, mean_pm25, mean_pm10, mean_no2, geometry_wkt
    """
    try:
        from spatial.grid import generate_h3_grid_pmc_pcmc

        grid_gdf = generate_h3_grid_pmc_pcmc(resolution=settings.H3_RESOLUTION)

        if FUSED_PATH.exists():
            fused = pd.read_parquet(FUSED_PATH)
            fused.columns = [c.lower() for c in fused.columns]
            if "pm2.5" in fused.columns and "pm25" not in fused.columns:
                fused = fused.rename(columns={"pm2.5": "pm25"})

            agg_cols = {c: "mean" for c in ["aqi", "pm25", "pm10", "no2"] if c in fused.columns}
            agg_cols["aqi"] = "mean" if "aqi" in fused.columns else None

            grp_cols = [c for c in agg_cols if agg_cols[c] is not None]
            if "zone_id" in fused.columns and grp_cols:
                zone_agg = (
                    fused.groupby("zone_id")[list(agg_cols.keys())]
                    .agg("mean")
                    .reset_index()
                )
                zone_agg["record_count"] = fused.groupby("zone_id").size().values
                grid_gdf = grid_gdf.merge(zone_agg, on="zone_id", how="left")
            else:
                grid_gdf["aqi"] = None
                grid_gdf["record_count"] = 0
        else:
            grid_gdf["aqi"] = None
            grid_gdf["record_count"] = 0

        # Add derived columns
        grid_gdf["mean_aqi"] = grid_gdf.get("aqi", pd.Series(dtype=float))
        grid_gdf["mean_pm25"] = grid_gdf.get("pm25", pd.Series(dtype=float))
        grid_gdf["mean_pm10"] = grid_gdf.get("pm10", pd.Series(dtype=float))
        grid_gdf["mean_no2"] = grid_gdf.get("no2", pd.Series(dtype=float))
        grid_gdf["aqi_color"] = grid_gdf["mean_aqi"].apply(get_aqi_color)
        grid_gdf["aqi_category"] = grid_gdf["mean_aqi"].apply(get_aqi_category)

        if "geometry" in grid_gdf.columns:
            grid_gdf["geometry_wkt"] = grid_gdf["geometry"].apply(
                lambda g: g.wkt if g is not None else None
            )

        result_cols = [
            "zone_id",
            "centroid_lat",
            "centroid_lon",
            "mean_aqi",
            "aqi_color",
            "aqi_category",
            "record_count",
            "mean_pm25",
            "mean_pm10",
            "mean_no2",
        ]
        if "geometry_wkt" in grid_gdf.columns:
            result_cols.append("geometry_wkt")
        if "geometry" in grid_gdf.columns:
            result_cols.append("geometry")

        result = grid_gdf[[c for c in result_cols if c in grid_gdf.columns]].copy()
        logger.info("Loaded H3 zone layer", zones=len(result))
        return result

    except Exception as exc:
        logger.error("Failed to load H3 zone layer", error=str(exc))
        return pd.DataFrame(
            columns=[
                "zone_id", "centroid_lat", "centroid_lon", "mean_aqi",
                "aqi_color", "aqi_category", "record_count",
            ]
        )


# ---------------------------------------------------------------------------
# Traffic Layer
# ---------------------------------------------------------------------------

def load_traffic_layer() -> pd.DataFrame:
    """Load traffic monitoring layer.

    Returns a DataFrame of traffic monitoring points that have actual
    (non-null) speed observations.  Returns empty DataFrame if no data.
    """
    try:
        points_df = pd.DataFrame()
        obs_df = pd.DataFrame()

        if TRAFFIC_POINTS_CFG.exists():
            with open(TRAFFIC_POINTS_CFG) as f:
                points_raw = json.load(f)
            # Handle both list and dict format
            if isinstance(points_raw, dict) and "points" in points_raw:
                points_raw = points_raw["points"]
            points_df = pd.DataFrame(points_raw)

        if TRAFFIC_PATH.exists():
            obs_df = pd.read_parquet(TRAFFIC_PATH)
            obs_df.columns = [c.lower() for c in obs_df.columns]

        if obs_df.empty:
            logger.info("No traffic observations – traffic layer empty")
            return pd.DataFrame(
                columns=[
                    "point_id", "name", "lat", "lon", "current_speed",
                    "free_flow_speed", "congestion_ratio", "road_closure",
                    "confidence", "has_data",
                ]
            )

        # Filter to rows with actual speed data
        speed_col = next(
            (c for c in ["current_speed", "speed"] if c in obs_df.columns), None
        )
        if speed_col:
            obs_df = obs_df[obs_df[speed_col].notna()]

        if obs_df.empty:
            return pd.DataFrame()

        # Latest reading per point
        pid_col = next((c for c in ["point_id", "id"] if c in obs_df.columns), None)
        if pid_col:
            obs_latest = (
                obs_df.sort_values("timestamp" if "timestamp" in obs_df.columns else obs_df.columns[0])
                .groupby(pid_col)
                .last()
                .reset_index()
            )
        else:
            obs_latest = obs_df.copy()

        # Merge with point metadata
        # Normalise ID column in points_df if needed
        if not points_df.empty:
            if "id" in points_df.columns and "point_id" not in points_df.columns:
                points_df = points_df.rename(columns={"id": "point_id"})
            if "point_id" in points_df.columns and "point_id" in obs_latest.columns:
                merged = points_df.merge(obs_latest, on="point_id", how="inner")
            else:
                merged = obs_latest.copy()
        else:
            merged = obs_latest.copy()

        # Compute congestion ratio
        if "current_speed" in merged.columns and "free_flow_speed" in merged.columns:
            merged["congestion_ratio"] = (
                1.0 - merged["current_speed"] / merged["free_flow_speed"].replace(0, np.nan)
            ).clip(0, 1)
        else:
            merged["congestion_ratio"] = None

        merged["has_data"] = True

        # Standardise column names
        for old, new in [("latitude", "lat"), ("longitude", "lon")]:
            if old in merged.columns and new not in merged.columns:
                merged = merged.rename(columns={old: new})

        logger.info("Loaded traffic layer", points=len(merged))
        return merged

    except Exception as exc:
        logger.error("Failed to load traffic layer", error=str(exc))
        return pd.DataFrame()


# ---------------------------------------------------------------------------
# Weather Layer
# ---------------------------------------------------------------------------

def load_weather_layer() -> pd.DataFrame:
    """Load latest weather observations.

    Returns a DataFrame with columns:
        station_id, lat, lon, temperature_2m, relative_humidity_2m,
        wind_speed_10m, wind_direction_10m, surface_pressure,
        precipitation, boundary_layer_height, last_updated
    """
    try:
        weather_cols = [
            "temperature_2m",
            "relative_humidity_2m",
            "wind_speed_10m",
            "wind_direction_10m",
            "surface_pressure",
            "precipitation",
            "boundary_layer_height",
        ]

        if FUSED_PATH.exists():
            df = pd.read_parquet(FUSED_PATH)
            df.columns = [c.lower() for c in df.columns]

            # Get latest weather per station
            time_col = next(
                (c for c in ["observation_datetime", "datetime", "date"] if c in df.columns),
                None,
            )

            rows = []
            for sid, meta in STATION_META.items():
                sub = df[df["station_id"].astype(str) == str(sid)] if "station_id" in df.columns else pd.DataFrame()
                if sub.empty:
                    rows.append(
                        {
                            "station_id": sid,
                            "name": meta["name"],
                            "lat": meta["lat"],
                            "lon": meta["lon"],
                            **{c: None for c in weather_cols},
                            "last_updated": None,
                        }
                    )
                    continue

                if time_col:
                    sub = sub.sort_values(time_col, ascending=False)
                latest = sub.iloc[0]

                rows.append(
                    {
                        "station_id": sid,
                        "name": meta["name"],
                        "lat": meta["lat"],
                        "lon": meta["lon"],
                        **{c: _safe_round(latest.get(c, None)) for c in weather_cols},
                        "last_updated": str(latest[time_col]) if time_col else None,
                    }
                )
        elif WEATHER_PATH.exists():
            df = pd.read_parquet(WEATHER_PATH)
            df.columns = [c.lower() for c in df.columns]
            # Take latest row and replicate for all stations
            latest = df.sort_values(df.columns[0]).iloc[-1]
            rows = [
                {
                    "station_id": sid,
                    "name": meta["name"],
                    "lat": meta["lat"],
                    "lon": meta["lon"],
                    **{c: _safe_round(latest.get(c, None)) for c in weather_cols},
                    "last_updated": str(latest.iloc[0]),
                }
                for sid, meta in STATION_META.items()
            ]
        else:
            rows = [
                {
                    "station_id": sid,
                    "name": meta["name"],
                    "lat": meta["lat"],
                    "lon": meta["lon"],
                    **{c: None for c in weather_cols},
                    "last_updated": None,
                }
                for sid, meta in STATION_META.items()
            ]

        result = pd.DataFrame(rows)
        logger.info("Loaded weather layer", stations=len(result))
        return result

    except Exception as exc:
        logger.error("Failed to load weather layer", error=str(exc))
        return pd.DataFrame(
            columns=["station_id", "name", "lat", "lon", "temperature_2m", "last_updated"]
        )

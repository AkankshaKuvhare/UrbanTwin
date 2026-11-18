"""Space-Time Data Fusion Engine for UrbanTwin (Milestone 5).

Constructs the master analytical dataset by fusing:
1. Station AQI observations
2. Spatial entity resolution (H3 Resolution 7 zones)
3. Hourly weather covariates (Open-Meteo) matched by nearest timestamp
4. Explicit NULL traffic placeholders (traffic data is not available yet)

This table (fused_zone_time) serves as the single source of truth for all
downstream causal discovery and forecasting models.
"""

from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from sqlalchemy import create_engine, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

# Ensure project root is in sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config.logging import get_logger
from config.settings import settings
from database.base import Base
from database.models import AQIObservation, FusedZoneTime, Station, TrafficObservation
from pipelines.base import BasePipeline, PipelineResult
from spatial.snapping import PUNE_STATION_COORDINATES, SpatialEntityResolver

logger = get_logger(__name__)

CORE_POLLUTANT_FIELDS = ["aqi", "pm25", "pm10", "no2", "co", "so2", "o3", "dominant_pollutant"]
CORE_WEATHER_FIELDS = [
    "temperature_2m",
    "relative_humidity_2m",
    "precipitation",
    "wind_speed_10m",
    "wind_direction_10m",
    "surface_pressure",
    "boundary_layer_height",
]
TRAFFIC_PLACEHOLDER_FIELDS = [
    "traffic_speed",
    "traffic_congestion",
    "traffic_travel_time",
    "traffic_confidence",
]
TRAFFIC_COLUMNS = TRAFFIC_PLACEHOLDER_FIELDS
FUSED_SCHEMA_COLUMNS = [
    "zone_id",
    "observation_datetime",
    "station_id",
    *CORE_POLLUTANT_FIELDS,
    *CORE_WEATHER_FIELDS,
    *TRAFFIC_PLACEHOLDER_FIELDS,
    "weather_missing",
    "aqi_missing",
    "traffic_missing",
]


class SpaceTimeFusionEngine:
    """Production space-time fusion engine joining AQI, spatial zones, and weather."""

    def __init__(
        self,
        resolver: Optional[SpatialEntityResolver] = None,
        db_url: Optional[str] = None,
        resolution: Optional[int] = None,
    ) -> None:
        target_res = resolution or settings.H3_RESOLUTION
        self.resolver = resolver or SpatialEntityResolver(resolution=target_res)
        self.db_url = db_url or settings.DATABASE_URL
        self.station_zone_map = self.resolver.build_station_zone_mapping()
        self.correspondence_table = self.resolver.build_entity_correspondence_table(
            station_mapping_df=self.station_zone_map
        )

    def load_aqi_data(self, aqi_source: Optional[Union[pd.DataFrame, str, Path]] = None) -> pd.DataFrame:
        """Load AQI observation records from provided DataFrame, CSV file, or Database."""
        if isinstance(aqi_source, pd.DataFrame):
            df = aqi_source.copy()
        elif aqi_source is not None and Path(aqi_source).exists():
            df = pd.read_csv(aqi_source)
        else:
            # Query from database or default CSV
            try:
                engine = create_engine(self.db_url)
                with engine.connect() as conn:
                    query = "SELECT * FROM aqi_observations ORDER BY observation_date ASC"
                    df = pd.read_sql(query, conn)
                if df.empty:
                    raise ValueError("Database aqi_observations table is empty.")
            except Exception as exc:
                logger.warning("Could not read AQI from database, falling back to local CSV", error=str(exc))
                csv_path = settings.BASE_DIR / "data" / "all_stations_combined.csv"
                if not csv_path.exists():
                    csv_path = settings.BASE_DIR / "data" / "real" / "raw" / "all_stations_combined.csv"
                df = pd.read_csv(csv_path)

        # Standardize columns and timestamps
        date_col = next((c for c in ["observation_datetime", "observation_date", "datetime", "date", "timestamp"] if c in df.columns), None)
        if date_col is None:
            raise KeyError("No valid date/datetime column found in AQI data")

        parsed_dates = pd.to_datetime(df[date_col])
        if parsed_dates.dt.tz is None:
            df["observation_datetime"] = parsed_dates.dt.tz_localize("Asia/Kolkata")
        else:
            df["observation_datetime"] = parsed_dates.dt.tz_convert("Asia/Kolkata")
        df["observation_date"] = df["observation_datetime"].dt.date
        df["station_id"] = df["station_id"].astype(str).str.strip()

        for p in ["aqi", "pm25", "pm10", "no2", "co", "so2", "o3"]:
            if p in df.columns:
                df[p] = pd.to_numeric(df[p], errors="coerce")
            else:
                df[p] = np.nan

        if "dominant_pollutant" not in df.columns:
            df["dominant_pollutant"] = None

        return df

    def load_weather_data(self, weather_source: Optional[Union[pd.DataFrame, str, Path]] = None) -> pd.DataFrame:
        """Load hourly meteorological dataset from DataFrame, Parquet, or CSV."""
        if isinstance(weather_source, pd.DataFrame):
            df = weather_source.copy()
        elif weather_source is not None and Path(weather_source).exists():
            p = Path(weather_source)
            df = pd.read_parquet(p) if p.suffix == ".parquet" else pd.read_csv(p)
        else:
            candidate_paths = [
                settings.BASE_DIR / "data" / "pune_historical_weather_hourly.parquet",
                settings.BASE_DIR / "data" / "real" / "raw" / "pune_historical_weather_hourly.parquet",
                settings.BASE_DIR / "data" / "pune_historical_weather_hourly.csv",
            ]
            valid_p = next((cp for cp in candidate_paths if cp.exists()), None)
            if valid_p is None:
                raise FileNotFoundError("Weather dataset not found. Run collectors/openmeteo.py first.")
            df = pd.read_parquet(valid_p) if valid_p.suffix == ".parquet" else pd.read_csv(valid_p)

        # Ensure datetime with timezone
        t_col = "timestamp" if "timestamp" in df.columns else "datetime"
        df["weather_datetime"] = pd.to_datetime(df[t_col])
        if df["weather_datetime"].dt.tz is None:
            df["weather_datetime"] = df["weather_datetime"].dt.tz_localize("Asia/Kolkata")
        else:
            df["weather_datetime"] = df["weather_datetime"].dt.tz_convert("Asia/Kolkata")

        # Normalize canonical names
        col_mappings = {
            "temperature_c": "temperature_2m",
            "relative_humidity": "relative_humidity_2m",
            "precipitation_mm": "precipitation",
            "wind_speed_ms": "wind_speed_10m",
            "wind_direction_deg": "wind_direction_10m",
            "surface_pressure_hpa": "surface_pressure",
            "boundary_layer_height_m": "boundary_layer_height",
        }
        for src, dest in col_mappings.items():
            if dest not in df.columns and src in df.columns:
                df[dest] = df[src]

        return df

    def load_traffic_data(
        self, traffic_source: Optional[Union[pd.DataFrame, str, Path]] = None
    ) -> pd.DataFrame:
        """Load arterial traffic observations from Database (primary source of truth) or fallback.

        Args:
            traffic_source: Optional DataFrame, CSV/Parquet path, or None to query database.

        Returns:
            DataFrame containing prepared traffic records aggregated by (zone_id, traffic_datetime).
        """
        if isinstance(traffic_source, pd.DataFrame):
            df = traffic_source.copy()
        elif traffic_source is not None and Path(traffic_source).exists():
            p = Path(traffic_source)
            df = pd.read_parquet(p) if p.suffix == ".parquet" else pd.read_csv(p)
        else:
            # Query primary source of truth: PostgreSQL/SQLite database
            try:
                engine = create_engine(self.db_url)
                with engine.connect() as conn:
                    query = "SELECT * FROM traffic_observations ORDER BY timestamp ASC"
                    df = pd.read_sql(query, conn)
                if df.empty:
                    raise ValueError("Database traffic_observations table is empty.")
            except Exception as exc:
                logger.warning(
                    "Could not read traffic from database, checking fallback artifact",
                    error=str(exc),
                )
                parquet_path = settings.DATA_DIR / "traffic" / "traffic_observations.parquet"
                if parquet_path.exists():
                    df = pd.read_parquet(parquet_path)
                else:
                    return pd.DataFrame()

        if df.empty:
            return pd.DataFrame()

        return self.prepare_traffic_data(df)

    def prepare_traffic_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare, snap, normalize, and aggregate traffic observations to H3 Resolution 7 zones.

        Reuses existing H3 utilities (self.resolver) and traffic points configuration.
        """
        if df.empty:
            return pd.DataFrame()

        traffic = df.copy()

        # Deduplicate on (point_id, timestamp) if columns exist
        if "point_id" in traffic.columns and "timestamp" in traffic.columns:
            traffic = traffic.drop_duplicates(subset=["point_id", "timestamp"], keep="last")

        # Temporal standardization (Asia/Kolkata timezone)
        t_col = next(
            (c for c in ["traffic_datetime", "timestamp", "observation_datetime", "datetime", "date"] if c in traffic.columns),
            None,
        )
        if t_col is None:
            logger.warning("No valid timestamp column found in traffic dataset")
            return pd.DataFrame()

        parsed_ts = pd.to_datetime(traffic[t_col])
        if parsed_ts.dt.tz is None:
            traffic["traffic_datetime"] = parsed_ts.dt.tz_localize("Asia/Kolkata")
        else:
            traffic["traffic_datetime"] = parsed_ts.dt.tz_convert("Asia/Kolkata")

        # Spatial resolution: Map traffic points to H3 Resolution 7 zones
        if "zone_id" not in traffic.columns:
            if "latitude" not in traffic.columns or "longitude" not in traffic.columns:
                points_cfg = settings.BASE_DIR / "config" / "traffic_points.json"
                if points_cfg.exists():
                    try:
                        with open(points_cfg, "r", encoding="utf-8") as f:
                            pts = json.load(f)
                        coords_map = {p["id"]: (p.get("latitude"), p.get("longitude")) for p in pts if "id" in p}
                        if "point_id" in traffic.columns:
                            traffic["latitude"] = traffic["point_id"].map(lambda pid: coords_map.get(pid, (np.nan, np.nan))[0])
                            traffic["longitude"] = traffic["point_id"].map(lambda pid: coords_map.get(pid, (np.nan, np.nan))[1])
                    except Exception as exc:
                        logger.warning("Failed loading traffic points config for spatial snapping", error=str(exc))

            if "latitude" in traffic.columns and "longitude" in traffic.columns:
                unique_pts = traffic[["latitude", "longitude"]].dropna().drop_duplicates()
                pt_to_zone = {}
                for _, pt_row in unique_pts.iterrows():
                    res = self.resolver.resolve_point(pt_row["latitude"], pt_row["longitude"])
                    pt_to_zone[(pt_row["latitude"], pt_row["longitude"])] = res["zone_id"]
                traffic["zone_id"] = [
                    pt_to_zone.get((lat, lon)) for lat, lon in zip(traffic["latitude"], traffic["longitude"])
                ]

        traffic = traffic.dropna(subset=["zone_id"]).copy()
        if traffic.empty:
            return pd.DataFrame()

        traffic["zone_id"] = traffic["zone_id"].astype(str)

        # Standardize traffic feature columns
        # 1. Speed (km/h)
        if "traffic_speed" not in traffic.columns and "current_speed" in traffic.columns:
            traffic["traffic_speed"] = pd.to_numeric(traffic["current_speed"], errors="coerce")
        elif "traffic_speed" in traffic.columns:
            traffic["traffic_speed"] = pd.to_numeric(traffic["traffic_speed"], errors="coerce")
        else:
            traffic["traffic_speed"] = np.nan

        # 2. Travel Time (seconds)
        if "traffic_travel_time" not in traffic.columns and "current_travel_time" in traffic.columns:
            traffic["traffic_travel_time"] = pd.to_numeric(traffic["current_travel_time"], errors="coerce")
        elif "traffic_travel_time" in traffic.columns:
            traffic["traffic_travel_time"] = pd.to_numeric(traffic["traffic_travel_time"], errors="coerce")
        else:
            traffic["traffic_travel_time"] = np.nan

        # 3. Confidence (0.0 to 1.0)
        if "traffic_confidence" not in traffic.columns and "confidence" in traffic.columns:
            traffic["traffic_confidence"] = pd.to_numeric(traffic["confidence"], errors="coerce")
        elif "traffic_confidence" in traffic.columns:
            traffic["traffic_confidence"] = pd.to_numeric(traffic["traffic_confidence"], errors="coerce")
        else:
            traffic["traffic_confidence"] = np.nan

        # 4. Congestion ratio (0.0 to 1.0)
        if "traffic_congestion" not in traffic.columns:
            if "free_flow_speed" in traffic.columns and "traffic_speed" in traffic.columns:
                ff = pd.to_numeric(traffic["free_flow_speed"], errors="coerce").replace(0, np.nan)
                cong = (ff - traffic["traffic_speed"]) / ff
                traffic["traffic_congestion"] = cong.clip(lower=0.0, upper=1.0)
            else:
                traffic["traffic_congestion"] = np.nan
        else:
            traffic["traffic_congestion"] = pd.to_numeric(traffic["traffic_congestion"], errors="coerce").clip(lower=0.0, upper=1.0)

        # Zone-level aggregation: reconciles multiple sensor points falling inside the same H3 zone
        traffic["traffic_datetime_agg"] = traffic["traffic_datetime"].dt.round("1min")
        agg_df = (
            traffic.groupby(["zone_id", "traffic_datetime_agg"], as_index=False)
            .agg({
                "traffic_speed": "mean",
                "traffic_congestion": "mean",
                "traffic_travel_time": "mean",
                "traffic_confidence": "mean",
            })
            .rename(columns={"traffic_datetime_agg": "traffic_datetime"})
        )
        agg_df = agg_df.sort_values("traffic_datetime").reset_index(drop=True)
        return agg_df

    def fuse(
        self,
        aqi_df: pd.DataFrame,
        weather_df: pd.DataFrame,
        traffic_df: Optional[pd.DataFrame] = None,
        tolerance: pd.Timedelta = pd.Timedelta("12h"),
        traffic_tolerance: pd.Timedelta = pd.Timedelta("1h"),
    ) -> pd.DataFrame:
        """Execute space-time join uniting AQI, H3 Spatial Zones, Weather, and Traffic covariates.

        Logic:
            1. Map each AQI station to its H3 zone via spatial correspondence.
            2. Match observations to hourly weather via nearest-timestamp alignment (merge_asof).
            3. Match observations to arterial traffic via nearest-timestamp alignment (merge_asof).
            4. Compute missingness indicator flags with strict NULL fallback safety.

        Args:
            aqi_df: Prepared AQI DataFrame.
            weather_df: Prepared hourly weather DataFrame.
            traffic_df: Optional prepared traffic DataFrame.
            tolerance: Max allowable timestamp delta for nearest-neighbour weather alignment.
            traffic_tolerance: Max allowable timestamp delta for nearest-neighbour traffic alignment.

        Returns:
            Master analytical DataFrame matching fused_zone_time schema.
        """
        # 0. Data normalization if needed
        if "observation_datetime" not in aqi_df.columns:
            fused = self.load_aqi_data(aqi_df)
        else:
            fused = aqi_df.copy()
            fused["station_id"] = fused["station_id"].astype(str).str.strip()

        if "weather_datetime" not in weather_df.columns:
            weather_prep = self.load_weather_data(weather_df)
        else:
            weather_prep = weather_df.copy()

        # 1. Spatial Resolution: Attach H3 zone_id
        station_to_zone = self.station_zone_map.set_index("station_id")["zone_id"].to_dict()
        fused["zone_id"] = fused["station_id"].map(station_to_zone)

        # Fallback for unmapped stations
        unmapped_mask = fused["zone_id"].isna()
        if unmapped_mask.any():
            logger.warning("Unmapped stations detected, applying dynamic snapping", count=int(unmapped_mask.sum()))
            # Default to Pune center zone
            fused.loc[unmapped_mask, "zone_id"] = self.resolver.zones_gdf.iloc[0]["zone_id"]

        fused["zone_id"] = fused["zone_id"].astype(str)

        # 2. Temporal Alignment: Nearest-timestamp merge_asof with weather
        fused_sorted = fused.sort_values("observation_datetime").reset_index(drop=True)
        weather_sorted = weather_prep.sort_values("weather_datetime").reset_index(drop=True)

        weather_cols_to_merge = ["weather_datetime"] + [
            c for c in CORE_WEATHER_FIELDS if c in weather_sorted.columns
        ]

        merged = pd.merge_asof(
            fused_sorted,
            weather_sorted[weather_cols_to_merge],
            left_on="observation_datetime",
            right_on="weather_datetime",
            direction="nearest",
            tolerance=tolerance,
        )

        # 3. Temporal Alignment: Nearest-timestamp merge_asof with traffic
        has_traffic = False
        if traffic_df is not None and not traffic_df.empty:
            if "traffic_datetime" not in traffic_df.columns or "zone_id" not in traffic_df.columns:
                traffic_prep = self.prepare_traffic_data(traffic_df)
            else:
                traffic_prep = traffic_df.copy()

            if not traffic_prep.empty:
                has_traffic = True
                traffic_prep["zone_id"] = traffic_prep["zone_id"].astype(str)
                traffic_sorted = traffic_prep.sort_values("traffic_datetime").reset_index(drop=True)
                merged_sorted = merged.sort_values("observation_datetime").reset_index(drop=True)

                traffic_cols_to_merge = ["traffic_datetime", "zone_id"] + [
                    c for c in TRAFFIC_PLACEHOLDER_FIELDS if c in traffic_sorted.columns
                ]

                merged = pd.merge_asof(
                    merged_sorted,
                    traffic_sorted[traffic_cols_to_merge],
                    left_on="observation_datetime",
                    right_on="traffic_datetime",
                    by="zone_id",
                    direction="nearest",
                    tolerance=traffic_tolerance,
                )

        if not has_traffic:
            for t_col in TRAFFIC_PLACEHOLDER_FIELDS:
                merged[t_col] = np.nan

        # 4. Missingness indicators
        merged["weather_missing"] = merged["weather_datetime"].isna() | merged["temperature_2m"].isna()
        merged["aqi_missing"] = merged["aqi"].isna()
        merged["traffic_missing"] = merged["traffic_speed"].isna()

        # Select & order canonical columns matching fused_zone_time
        canonical_columns = [
            "zone_id",
            "observation_datetime",
            "station_id",
            "aqi",
            "pm25",
            "pm10",
            "no2",
            "co",
            "so2",
            "o3",
            "dominant_pollutant",
            "temperature_2m",
            "relative_humidity_2m",
            "precipitation",
            "wind_speed_10m",
            "wind_direction_10m",
            "surface_pressure",
            "boundary_layer_height",
            "traffic_speed",
            "traffic_congestion",
            "traffic_travel_time",
            "traffic_confidence",
            "weather_missing",
            "aqi_missing",
            "traffic_missing",
        ]

        result_df = merged[canonical_columns].copy()

        # Deduplicate on (zone_id, observation_datetime, station_id)
        result_df = result_df.drop_duplicates(subset=["zone_id", "observation_datetime", "station_id"])

        logger.info(
            "Fusion completed successfully",
            total_fused_records=len(result_df),
            zones_count=result_df["zone_id"].nunique(),
            weather_missing_count=int(result_df["weather_missing"].sum()),
            aqi_missing_count=int(result_df["aqi_missing"].sum()),
        )
        return result_df

    # Alias for method naming compatibility
    fuse_space_time = fuse

    def compute_validation_metrics(self, fused_df: pd.DataFrame) -> Dict[str, Any]:
        """Compute coverage, completeness, and missingness metrics across the fused table."""
        total_records = len(fused_df)
        total_zones = fused_df["zone_id"].nunique()
        total_stations = fused_df["station_id"].nunique()

        min_dt = fused_df["observation_datetime"].min()
        max_dt = fused_df["observation_datetime"].max()

        weather_completeness = (
            round((1.0 - (fused_df["weather_missing"].sum() / total_records)) * 100, 2)
            if total_records > 0 else 0.0
        )
        aqi_completeness = (
            round((1.0 - (fused_df["aqi_missing"].sum() / total_records)) * 100, 2)
            if total_records > 0 else 0.0
        )
        traffic_completeness = (
            round((1.0 - (fused_df["traffic_missing"].sum() / total_records)) * 100, 2)
            if total_records > 0 else 0.0
        )
        overall_coverage = round((weather_completeness + aqi_completeness) / 2.0, 2)

        # Per-zone completeness
        zone_records = []
        for z_id, grp in fused_df.groupby("zone_id"):
            z_total = len(grp)
            z_w_valid = int((~grp["weather_missing"]).sum())
            z_a_valid = int((~grp["aqi_missing"]).sum())
            z_t_valid = int((~grp["traffic_missing"]).sum())
            zone_records.append({
                "zone_id": str(z_id),
                "total_records": z_total,
                "weather_valid_count": z_w_valid,
                "weather_completeness_pct": round((z_w_valid / z_total) * 100, 2),
                "aqi_valid_count": z_a_valid,
                "aqi_completeness_pct": round((z_a_valid / z_total) * 100, 2),
                "traffic_valid_count": z_t_valid,
                "traffic_completeness_pct": round((z_t_valid / z_total) * 100, 2),
                "mean_aqi": round(float(grp["aqi"].mean()), 2) if grp["aqi"].notna().any() else None,
                "mean_temp": round(float(grp["temperature_2m"].mean()), 2) if grp["temperature_2m"].notna().any() else None,
                "mean_traffic_speed": round(float(grp["traffic_speed"].mean()), 2) if grp["traffic_speed"].notna().any() else None,
            })
        zone_completeness_df = pd.DataFrame(zone_records)

        # Missingness matrix across all columns
        missing_matrix = []
        for col in fused_df.columns:
            null_count = int(fused_df[col].isna().sum())
            missing_matrix.append({
                "column": col,
                "null_count": null_count,
                "null_percentage": round((null_count / total_records) * 100, 2) if total_records > 0 else 0.0,
            })
        missing_df = pd.DataFrame(missing_matrix)

        return {
            "total_records": total_records,
            "total_zones": total_zones,
            "total_stations": total_stations,
            "temporal_range": f"{min_dt} to {max_dt}",
            "weather_completeness_pct": weather_completeness,
            "aqi_completeness_pct": aqi_completeness,
            "traffic_completeness_pct": traffic_completeness,
            "fusion_coverage_pct": overall_coverage,
            "zone_completeness": zone_completeness_df,
            "missingness_matrix": missing_df,
        }

    def export_reports_and_visualizations(
        self, fused_df: pd.DataFrame, output_dir: Optional[Union[str, Path]] = None
    ) -> Dict[str, Path]:
        """Export CSV summaries and diagnostic figures to reports/fusion/."""
        out_path = Path(output_dir) if output_dir else settings.BASE_DIR / "reports" / "fusion"
        out_path.mkdir(parents=True, exist_ok=True)
        figs_dir = out_path / "figures"
        figs_dir.mkdir(parents=True, exist_ok=True)

        metrics = self.compute_validation_metrics(fused_df)

        # 1. Export CSV Summaries
        coverage_path = out_path / "coverage_report.csv"
        metrics["zone_completeness"].to_csv(coverage_path, index=False)

        missing_path = out_path / "missing_value_report.csv"
        metrics["missingness_matrix"].to_csv(missing_path, index=False)

        summary_data = [
            {"metric": "total_records", "value": metrics["total_records"]},
            {"metric": "total_zones", "value": metrics["total_zones"]},
            {"metric": "total_stations", "value": metrics["total_stations"]},
            {"metric": "temporal_range", "value": metrics["temporal_range"]},
            {"metric": "weather_completeness_pct", "value": metrics["weather_completeness_pct"]},
            {"metric": "aqi_completeness_pct", "value": metrics["aqi_completeness_pct"]},
            {"metric": "traffic_completeness_pct", "value": metrics["traffic_completeness_pct"]},
            {"metric": "fusion_coverage_pct", "value": metrics["fusion_coverage_pct"]},
        ]
        fusion_summary_path = out_path / "fusion_report.csv"
        pd.DataFrame(summary_data).to_csv(fusion_summary_path, index=False)

        # 2. Diagnostic Figures
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")

        # Plot 1: AQI vs Temperature
        fig1, ax1 = plt.subplots(figsize=(8, 5))
        valid_pair = fused_df.dropna(subset=["aqi", "temperature_2m"])
        ax1.scatter(valid_pair["temperature_2m"], valid_pair["aqi"], alpha=0.35, color="#e6550d", edgecolors="none")
        ax1.set_title("UrbanTwin Space-Time Fusion: AQI vs Temperature", fontsize=12, fontweight="bold")
        ax1.set_xlabel("Temperature (°C)")
        ax1.set_ylabel("Air Quality Index (AQI)")
        fig1.tight_layout()
        p1 = figs_dir / "aqi_vs_temperature.png"
        fig1.savefig(p1, dpi=180)
        plt.close(fig1)

        # Plot 2: AQI vs Relative Humidity
        fig2, ax2 = plt.subplots(figsize=(8, 5))
        valid_rh = fused_df.dropna(subset=["aqi", "relative_humidity_2m"])
        ax2.scatter(valid_rh["relative_humidity_2m"], valid_rh["aqi"], alpha=0.35, color="#3182bd", edgecolors="none")
        ax2.set_title("UrbanTwin Space-Time Fusion: AQI vs Relative Humidity", fontsize=12, fontweight="bold")
        ax2.set_xlabel("Relative Humidity (%)")
        ax2.set_ylabel("Air Quality Index (AQI)")
        fig2.tight_layout()
        p2 = figs_dir / "aqi_vs_humidity.png"
        fig2.savefig(p2, dpi=180)
        plt.close(fig2)

        # Plot 3: Missingness Matrix Bar Chart
        fig3, ax3 = plt.subplots(figsize=(10, 5))
        miss_df = metrics["missingness_matrix"]
        ax3.bar(miss_df["column"], miss_df["null_percentage"], color="#756bb1", edgecolor="black", alpha=0.85)
        ax3.set_xticklabels(miss_df["column"], rotation=45, ha="right", fontsize=9)
        ax3.set_ylabel("Null Percentage (%)")
        ax3.set_title("Space-Time Fusion Missingness Audit", fontsize=12, fontweight="bold")
        ax3.set_ylim(0, 105)
        fig3.tight_layout()
        p3 = figs_dir / "missingness_matrix.png"
        fig3.savefig(p3, dpi=180)
        plt.close(fig3)

        return {
            "coverage_report": coverage_path,
            "missing_value_report": missing_path,
            "fusion_report": fusion_summary_path,
            "figures_dir": figs_dir,
        }

    def save_to_database(self, fused_df: pd.DataFrame, batch_size: int = 1000) -> int:
        """Persist fused space-time panel to PostgreSQL/SQLite fused_zone_time table.

        Args:
            fused_df: Master DataFrame.
            batch_size: Batch insert size.

        Returns:
            Number of inserted records.
        """
        engine = create_engine(self.db_url)
        Base.metadata.create_all(engine, tables=[FusedZoneTime.__table__])

        records = fused_df.to_dict(orient="records")
        dialect = engine.dialect.name
        inserted_total = 0

        with Session(engine) as session:
            for i in range(0, len(records), batch_size):
                batch = records[i : i + batch_size]
                if dialect == "postgresql":
                    stmt = pg_insert(FusedZoneTime).values(batch)
                    stmt = stmt.on_conflict_do_nothing(
                        index_elements=["zone_id", "observation_datetime", "station_id"]
                    )
                    res = session.execute(stmt)
                    rc = res.rowcount if res.rowcount is not None and res.rowcount >= 0 else len(batch)
                    inserted_total += rc
                elif dialect == "sqlite":
                    stmt = sqlite_insert(FusedZoneTime).values(batch)
                    stmt = stmt.on_conflict_do_nothing(
                        index_elements=["zone_id", "observation_datetime", "station_id"]
                    )
                    res = session.execute(stmt)
                    rc = res.rowcount if res.rowcount is not None and res.rowcount >= 0 else len(batch)
                    inserted_total += rc
                else:
                    session.bulk_insert_mappings(FusedZoneTime, batch)
                    inserted_total += len(batch)

                session.commit()

        logger.info("Persisted fused space-time records to database", total_records=inserted_total)
        return inserted_total


def run_space_time_fusion_pipeline(
    output_dir: Optional[Union[str, Path]] = None,
    save_db: bool = False,
    traffic_source: Optional[Union[pd.DataFrame, str, Path]] = None,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Execute complete Milestone 5 Space-Time Data Fusion pipeline."""
    engine = SpaceTimeFusionEngine()
    aqi_df = engine.load_aqi_data()
    weather_df = engine.load_weather_data()
    traffic_df = engine.load_traffic_data(traffic_source=traffic_source)

    fused_df = engine.fuse(aqi_df, weather_df, traffic_df=traffic_df)

    # Save to data/master and parquet
    out_dir = Path(output_dir) if output_dir else settings.BASE_DIR / "data"
    out_dir.mkdir(parents=True, exist_ok=True)
    fused_parquet = out_dir / "fused_zone_time.parquet"
    fused_csv = out_dir / "fused_zone_time.csv"
    fused_df.to_parquet(fused_parquet, index=False)
    fused_df.to_csv(fused_csv, index=False)

    reports = engine.export_reports_and_visualizations(fused_df)

    if save_db:
        try:
            engine.save_to_database(fused_df)
        except Exception as e:
            logger.warning("Could not persist to live database", error=str(e))

    metrics = engine.compute_validation_metrics(fused_df)
    return fused_df, metrics


class DatasetFusionPipeline(BasePipeline):
    """Pipeline coordinating the fusion of AQI, spatial entities, and weather into fused_zone_time."""

    @property
    def name(self) -> str:
        return "dataset_fusion_stage_3"

    def execute(self, **kwargs: Any) -> PipelineResult:
        """Run space-time data fusion pipeline stage."""
        raise NotImplementedError("DatasetFusionPipeline.execute is not yet implemented.")


if __name__ == "__main__":
    fused_df, metrics = run_space_time_fusion_pipeline()
    print("\n--- URBAN TWIN SPACE-TIME FUSION COMPLETED ---")
    print(f"Total Fused Records:    {metrics['total_records']:,}")
    print(f"Active H3 Zones:        {metrics['total_zones']}")
    print(f"Weather Completeness:   {metrics['weather_completeness_pct']}%")
    print(f"AQI Completeness:       {metrics['aqi_completeness_pct']}%")
    print(f"Traffic Completeness:   {metrics['traffic_completeness_pct']}%")
    print(f"Overall Fusion Coverage:{metrics['fusion_coverage_pct']}%")

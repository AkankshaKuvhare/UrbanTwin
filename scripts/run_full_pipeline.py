"""End-to-End System Validation Script for UrbanTwin.

Executes every completed pipeline stage in order, computes health scores,
and writes structured reports to reports/system_validation/.

Pipeline Stages:
1. Verify Environment (.env)
2. Database Connection & Schema Verification
3. Alembic Migration Status
4. AQI Historical Import
5. AQI Data Quality Audit
6. Weather Collector
7. Traffic Collector (single test run only)
8. H3 Grid Generation
9. Entity Resolution
10. Space-Time Fusion
11. Baseline Forecasting
12. Dashboard Generation

Usage:
    python scripts/run_full_pipeline.py
"""

import csv
import importlib
import json
import os
import sys
import time
import traceback
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Bootstrap: ensure project root is on sys.path
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

REPORTS_DIR = PROJECT_ROOT / "reports" / "system_validation"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

RUN_TIMESTAMP = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class StageResult:
    stage_index: int
    stage_name: str
    started_at: float = 0.0
    ended_at: float = 0.0
    success: bool = False
    score: int = 0          # 0-100
    records: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)

    @property
    def duration_s(self) -> float:
        return round(self.ended_at - self.started_at, 3)

    @property
    def status_label(self) -> str:
        if self.success and self.score >= 80:
            return "PASS"
        if self.success and self.score >= 50:
            return "WARN"
        return "FAIL"


# ---------------------------------------------------------------------------
# Console printing helpers (ASCII-only for Windows console safety)
# ---------------------------------------------------------------------------

def _now() -> float:
    return time.monotonic()


def _banner(text: str) -> None:
    line = "-" * 65
    print(f"\n{line}")
    print(f"  {text}")
    print(line)


def _ok(msg: str) -> None:
    print(f"  [OK]   {msg}")


def _warn(msg: str) -> None:
    print(f"  [WARN] {msg}")


def _err(msg: str) -> None:
    print(f"  [ERR]  {msg}")


def _info(msg: str) -> None:
    print(f"  [INFO] {msg}")


# ---------------------------------------------------------------------------
# Stage 1: Environment (.env)
# ---------------------------------------------------------------------------

def stage_environment() -> StageResult:
    """Stage 1 - Verify Environment (.env) and critical configurations."""
    result = StageResult(1, "Environment (.env)")
    result.started_at = _now()
    score = 100

    try:
        env_path = PROJECT_ROOT / ".env"
        if not env_path.exists():
            result.errors.append(".env file not found")
            score -= 40
            _err(".env file missing")
        else:
            _ok(f".env file found ({env_path.name})")

        from config.settings import settings
        _ok("Configuration settings imported successfully")

        # TomTom API key
        api_key = getattr(settings, "TOMTOM_API_KEY", None) or os.getenv("TOMTOM_API_KEY")
        if api_key and len(str(api_key).strip()) >= 10:
            _ok(f"TOMTOM_API_KEY verified ({len(str(api_key))} characters)")
            result.metrics["tomtom_key_configured"] = True
        else:
            result.warnings.append("TOMTOM_API_KEY missing or empty")
            score -= 20
            _warn("TOMTOM_API_KEY not configured")

        # Database URL
        db_url = getattr(settings, "DATABASE_URL", None) or os.getenv("DATABASE_URL")
        if db_url:
            _ok("DATABASE_URL setting detected")
            result.metrics["db_url_configured"] = True
        else:
            result.warnings.append("DATABASE_URL not configured")
            score -= 10
            _warn("DATABASE_URL not configured")

        # Data directory
        data_dir = getattr(settings, "DATA_DIR", PROJECT_ROOT / "data")
        if data_dir.exists():
            _ok(f"DATA_DIR accessible: {data_dir.name}/")
            result.metrics["data_dir_exists"] = True
        else:
            result.errors.append("DATA_DIR directory missing")
            score -= 20

        result.success = True
        result.records = 4  # 4 checks performed

    except Exception as exc:
        result.errors.append(str(exc))
        score = max(0, score - 50)
        _err(f"Exception: {exc}")

    result.score = max(0, score)
    result.ended_at = _now()
    return result


# ---------------------------------------------------------------------------
# Stage 2: Database Connection & Schema Verification
# ---------------------------------------------------------------------------

def stage_database() -> StageResult:
    """Stage 2 - Database Connection & ORM Schema Verification."""
    result = StageResult(2, "Database & Schema")
    result.started_at = _now()
    score = 100

    try:
        from database.models import Base
        tables = Base.metadata.tables
        required_schema_tables = [
            "stations", "aqi_observations", "traffic_observations",
            "fused_zone_time", "spatial_zones", "entity_correspondences"
        ]

        # Verify ORM Schema definitions (PKs, FKs, Indexes, UniqueConstraints)
        table_schema_info = {}
        for tbl_name in required_schema_tables:
            if tbl_name in tables:
                tbl = tables[tbl_name]
                pks = [c.name for c in tbl.primary_key.columns]
                fks = [f"{fk.parent.name}->{fk.target_fullname}" for fk in tbl.foreign_keys]
                indexes = [idx.name for idx in tbl.indexes]
                ucs = [c.name for c in tbl.constraints if c.__class__.__name__ == "UniqueConstraint"]
                table_schema_info[tbl_name] = {
                    "primary_key": pks,
                    "foreign_keys": fks,
                    "indexes": indexes,
                    "unique_constraints": ucs,
                    "columns": len(tbl.columns)
                }
                _ok(f"Schema {tbl_name}: PK={pks}, FKs={len(fks)}, Idx={len(indexes)}, UCs={len(ucs)}")
            else:
                _warn(f"Schema {tbl_name}: NOT FOUND in ORM metadata")
                result.warnings.append(f"ORM table {tbl_name} missing")
                score -= 10

        result.metrics["schema_tables"] = table_schema_info

        # Now test live DB connection
        import psycopg2
        from config.settings import settings

        db_url = str(getattr(settings, "DATABASE_URL", "") or "")
        connected = False
        db_rows = {}

        try:
            if "postgresql" in db_url:
                clean_dsn = db_url.replace("postgresql+psycopg2", "postgresql")
                conn = psycopg2.connect(dsn=clean_dsn, connect_timeout=3)
                cur = conn.cursor()
                cur.execute("SELECT version();")
                v = cur.fetchone()[0]
                _ok(f"PostgreSQL live connection established: {v.split(',')[0]}")
                connected = True

                for tbl_name in required_schema_tables:
                    try:
                        cur.execute(f"SELECT COUNT(*) FROM {tbl_name};")
                        cnt = cur.fetchone()[0]
                        db_rows[tbl_name] = cnt
                        _ok(f"Live table {tbl_name}: {cnt:,} rows")
                    except Exception:
                        conn.rollback()
                        db_rows[tbl_name] = "table_not_in_db"
                conn.close()
        except psycopg2.OperationalError as pe:
            _warn(f"PostgreSQL auth/connection offline (expected in local dev): {str(pe).splitlines()[0]}")
            result.warnings.append(f"PostgreSQL connection offline: {str(pe).splitlines()[0]}")
            _info("Verifying Parquet/CSV storage fallbacks...")
            score = 75  # Graceful fallback warning

        # Verify fallback data storage
        fallback_counts = {}
        aqi_csv = PROJECT_ROOT / "data" / "all_stations_combined.csv"
        fused_pq = PROJECT_ROOT / "data" / "fused_zone_time.parquet"
        weather_pq = PROJECT_ROOT / "data" / "pune_historical_weather_hourly.parquet"
        traffic_pq = PROJECT_ROOT / "data" / "traffic" / "traffic_observations.parquet"

        import pandas as pd
        if aqi_csv.exists():
            fallback_counts["aqi_observations"] = len(pd.read_csv(aqi_csv))
        if fused_pq.exists():
            fallback_counts["fused_zone_time"] = len(pd.read_parquet(fused_pq))
        if weather_pq.exists():
            fallback_counts["weather_observations"] = len(pd.read_parquet(weather_pq))
        if traffic_pq.exists():
            fallback_counts["traffic_observations"] = len(pd.read_parquet(traffic_pq))

        for k, v in fallback_counts.items():
            _ok(f"Fallback storage {k}: {v:,} records available")

        result.metrics["live_db_connected"] = connected
        result.metrics["db_rows"] = db_rows if connected else fallback_counts
        result.records = sum(fallback_counts.values())
        result.success = True

    except Exception as exc:
        result.errors.append(str(exc))
        score = max(0, score - 30)
        _err(f"Exception: {exc}")

    result.score = max(0, score)
    result.ended_at = _now()
    return result


# ---------------------------------------------------------------------------
# Stage 3: Alembic Migration Status
# ---------------------------------------------------------------------------

def stage_migration_status() -> StageResult:
    """Stage 3 - Alembic Migration Status and Version History."""
    result = StageResult(3, "Alembic Migrations")
    result.started_at = _now()
    score = 100

    try:
        versions_dir = PROJECT_ROOT / "database" / "migrations" / "versions"
        if not versions_dir.exists():
            versions_dir = PROJECT_ROOT / "alembic" / "versions"

        if versions_dir.exists():
            files = sorted([f.name for f in versions_dir.glob("*.py") if not f.name.startswith("__")])
            _ok(f"Found {len(files)} migration script(s) in {versions_dir.name}/")
            for f in files:
                _info(f"  Migration: {f}")
            result.records = len(files)
            result.metrics["migration_files"] = files
            if len(files) == 0:
                score -= 40
                result.warnings.append("No migration versions found")
        else:
            result.warnings.append("Migration versions directory not found")
            score -= 40
            _warn("Migration versions directory not found")

        alembic_ini = PROJECT_ROOT / "alembic.ini"
        if alembic_ini.exists():
            _ok("alembic.ini configuration file present")
        else:
            result.warnings.append("alembic.ini not found")
            score -= 20

        result.success = True

    except Exception as exc:
        result.errors.append(str(exc))
        score = max(0, score - 30)
        _err(f"Exception: {exc}")

    result.score = max(0, score)
    result.ended_at = _now()
    return result


# ---------------------------------------------------------------------------
# Stage 4: AQI Historical Import
# ---------------------------------------------------------------------------

def stage_aqi_import() -> StageResult:
    """Stage 4 - AQI Historical Import Validation."""
    result = StageResult(4, "AQI Historical Import")
    result.started_at = _now()
    score = 100

    try:
        import pandas as pd
        aqi_csv = PROJECT_ROOT / "data" / "all_stations_combined.csv"

        if not aqi_csv.exists():
            result.errors.append(f"AQI data file not found: {aqi_csv}")
            result.score = 0
            result.ended_at = _now()
            return result

        df = pd.read_csv(aqi_csv)
        total_rows = len(df)
        result.records = total_rows
        _ok(f"Loaded AQI historical data: {total_rows:,} rows, {len(df.columns)} columns")

        # 1. Station count check
        station_col = "station_id" if "station_id" in df.columns else None
        if station_col:
            stations = df[station_col].unique().tolist()
            _ok(f"Unique stations: {len(stations)} {stations}")
            result.metrics["stations"] = [str(s) for s in stations]
            result.metrics["station_count"] = len(stations)
            if len(stations) < 5:
                result.warnings.append(f"Found {len(stations)} stations, expected >= 5")
                score -= 10
        else:
            result.warnings.append("station_id column missing")
            score -= 20

        # 2. Duplicate records check
        date_col = next((c for c in ["observation_date", "date", "timestamp"] if c in df.columns), None)
        if station_col and date_col:
            dups = int(df.duplicated(subset=[station_col, date_col]).sum())
            result.metrics["duplicate_station_date_pairs"] = dups
            if dups > 0:
                _warn(f"Found {dups} duplicate station-date pairs")
                result.warnings.append(f"{dups} duplicate station-date pairs")
                score -= min(15, dups)
            else:
                _ok("Zero duplicate (station, date) records verified")

        # 3. Date continuity check
        if date_col:
            dates = pd.to_datetime(df[date_col], errors="coerce").dropna().sort_values()
            if len(dates) > 0:
                min_d = dates.min()
                max_d = dates.max()
                span_days = (max_d - min_d).days
                _ok(f"Date coverage: {min_d.date()} to {max_d.date()} ({span_days} calendar days)")
                result.metrics["date_min"] = str(min_d.date())
                result.metrics["date_max"] = str(max_d.date())
                result.metrics["span_days"] = span_days

        # 4. Missing percentage & AQI statistics
        if "aqi" in df.columns:
            aqi_series = pd.to_numeric(df["aqi"], errors="coerce")
            missing_pct = round(float(aqi_series.isna().mean() * 100), 2)
            valid_aqi = aqi_series.dropna()
            stats = {
                "count": int(len(valid_aqi)),
                "missing_pct": missing_pct,
                "mean": round(float(valid_aqi.mean()), 2),
                "std": round(float(valid_aqi.std()), 2),
                "min": round(float(valid_aqi.min()), 2),
                "max": round(float(valid_aqi.max()), 2),
            }
            _ok(f"AQI stats: mean={stats['mean']}, std={stats['std']}, min={stats['min']}, max={stats['max']}, missing={missing_pct}%")
            result.metrics["aqi_stats"] = stats
            if missing_pct > 40:
                result.warnings.append(f"AQI missingness {missing_pct}% > 40%")
                score -= 10

        result.success = True

    except Exception as exc:
        result.errors.append(str(exc))
        result.errors.append(traceback.format_exc())
        score = max(0, score - 50)
        _err(f"Exception: {exc}")

    result.score = max(0, score)
    result.ended_at = _now()
    return result


# ---------------------------------------------------------------------------
# Stage 5: AQI Data Quality Audit
# ---------------------------------------------------------------------------

def stage_aqi_quality() -> StageResult:
    """Stage 5 - AQI Data Quality Audit Pipeline."""
    result = StageResult(5, "AQI Data Quality")
    result.started_at = _now()
    score = 100

    try:
        import pandas as pd
        from pipelines.data_quality import DataQualityAnalyzer

        aqi_csv = PROJECT_ROOT / "data" / "all_stations_combined.csv"
        df = pd.read_csv(aqi_csv)

        analyzer = DataQualityAnalyzer(df)
        completeness = analyzer.compute_data_completeness_score()
        date_cov = analyzer.compute_date_coverage()
        st_cov = analyzer.compute_station_coverage()
        dup_rep = analyzer.compute_duplicate_report()

        _ok(f"Data completeness score: {completeness:.2f}%")
        _ok(f"Temporal coverage: {date_cov.get('temporal_coverage_pct', 'N/A')}% across {date_cov.get('total_calendar_days', 'N/A')} days")
        _ok(f"Station coverage: {len(st_cov)} stations analyzed")
        _ok(f"Duplicates report: exact_duplicates={dup_rep.get('exact_duplicate_rows', 0)}")

        result.metrics["completeness_score"] = completeness
        result.metrics["temporal_coverage_pct"] = date_cov.get("temporal_coverage_pct")
        result.metrics["station_count_analyzed"] = len(st_cov)
        result.records = len(df)
        result.success = True

    except Exception as exc:
        result.errors.append(str(exc))
        result.errors.append(traceback.format_exc())
        score = max(0, score - 40)
        _err(f"Exception: {exc}")

    result.score = max(0, score)
    result.ended_at = _now()
    return result


# ---------------------------------------------------------------------------
# Stage 6: Weather Collector
# ---------------------------------------------------------------------------

def stage_weather() -> StageResult:
    """Stage 6 - Weather Data Collection & Temporal Continuity."""
    result = StageResult(6, "Weather Collector")
    result.started_at = _now()
    score = 100

    try:
        import pandas as pd
        wx_pq = PROJECT_ROOT / "data" / "pune_historical_weather_hourly.parquet"
        wx_csv = PROJECT_ROOT / "data" / "pune_historical_weather_hourly.csv"

        target_file = wx_pq if wx_pq.exists() else wx_csv
        if not target_file.exists():
            result.errors.append("Weather dataset file not found")
            result.score = 0
            result.ended_at = _now()
            return result

        df = pd.read_parquet(target_file) if target_file.suffix == ".parquet" else pd.read_csv(target_file)
        _ok(f"Loaded weather observations: {len(df):,} hourly rows from {target_file.name}")
        result.records = len(df)

        expected_vars = [
            "temperature_2m", "relative_humidity_2m", "precipitation",
            "wind_speed_10m", "wind_direction_10m", "surface_pressure"
        ]
        present_vars = [v for v in expected_vars if v in df.columns]
        missing_vars = [v for v in expected_vars if v not in df.columns]
        _ok(f"Weather meteorological variables present: {len(present_vars)}/{len(expected_vars)}")
        if missing_vars:
            _warn(f"Missing weather variables: {missing_vars}")
            result.warnings.append(f"Missing variables: {missing_vars}")
            score -= 10

        # Temporal coverage check
        time_col = next((c for c in ["time", "timestamp", "datetime", "observation_datetime"] if c in df.columns), None)
        if time_col:
            dt_series = pd.to_datetime(df[time_col], errors="coerce").dropna().sort_values()
            if len(dt_series) > 0:
                t0 = dt_series.min()
                t1 = dt_series.max()
                days = (t1 - t0).days
                _ok(f"Weather temporal span: {t0.date()} to {t1.date()} ({days} days, {len(dt_series):,} timesteps)")
                result.metrics["start_date"] = str(t0.date())
                result.metrics["end_date"] = str(t1.date())
                result.metrics["days_span"] = days

            # Check duplicate timestamps
            dups = int(df.duplicated(subset=[time_col]).sum())
            result.metrics["duplicate_timestamps"] = dups
            if dups > 0:
                _warn(f"Found {dups} duplicate weather timestamps")
                result.warnings.append(f"{dups} duplicate weather timestamps")
                score -= 10
            else:
                _ok("Zero duplicate timestamps verified in weather dataset")

        result.success = True

    except Exception as exc:
        result.errors.append(str(exc))
        result.errors.append(traceback.format_exc())
        score = max(0, score - 40)
        _err(f"Exception: {exc}")

    result.score = max(0, score)
    result.ended_at = _now()
    return result


# ---------------------------------------------------------------------------
# Stage 7: Traffic Collector (Single test cycle only)
# ---------------------------------------------------------------------------

def stage_traffic() -> StageResult:
    """Stage 7 - TomTom Traffic Collector (Single test cycle)."""
    result = StageResult(7, "Traffic Collector")
    result.started_at = _now()
    score = 100

    try:
        from collectors.tomtom import TomTomCollector

        _info("Initializing TomTomCollector for a single collection run...")
        collector = TomTomCollector()

        t0 = _now()
        obs_df, report = collector.collect_all_points()
        elapsed = _now() - t0

        n_obs = len(obs_df) if obs_df is not None else 0
        cov_pct = report.get("coverage_percentage", 0.0)
        avg_lat = report.get("average_latency_seconds", 0.0)
        failed = report.get("failed_requests", 0)

        _ok(f"TomTom cycle executed: {n_obs} points collected in {elapsed:.2f}s")
        _ok(f"Coverage: {cov_pct:.1f}%, Avg latency: {avg_lat:.3f}s, Failures: {failed}")

        result.records = n_obs
        result.metrics["points_collected"] = n_obs
        result.metrics["coverage_percentage"] = cov_pct
        result.metrics["average_latency_seconds"] = avg_lat
        result.metrics["failed_requests"] = failed

        if cov_pct < 50.0:
            score -= 30
            result.warnings.append(f"Traffic coverage low: {cov_pct:.1f}%")
        elif cov_pct < 80.0:
            score -= 15
            result.warnings.append(f"Traffic coverage partial: {cov_pct:.1f}%")

        result.success = True

    except Exception as exc:
        result.errors.append(str(exc))
        result.errors.append(traceback.format_exc())
        score = max(0, score - 50)
        _err(f"Exception: {exc}")

    result.score = max(0, score)
    result.ended_at = _now()
    return result


# ---------------------------------------------------------------------------
# Stage 8: H3 Grid Generation
# ---------------------------------------------------------------------------

def stage_h3_spatial() -> StageResult:
    """Stage 8 - H3 Spatial Hexagonal Grid Generation."""
    result = StageResult(8, "H3 Spatial Grid")
    result.started_at = _now()
    score = 100

    try:
        import h3
        from spatial.grid import generate_h3_grid_pmc_pcmc

        _info("Generating H3 resolution 7 grid covering PMC + PCMC...")
        grid_gdf = generate_h3_grid_pmc_pcmc(resolution=7)
        n_zones = len(grid_gdf)
        _ok(f"Generated {n_zones} H3 resolution 7 hexagons covering Pune metropolis")

        result.records = n_zones
        result.metrics["h3_resolution"] = 7
        result.metrics["total_hexagons"] = n_zones

        # Verify geometry and centroids
        if "centroid_lat" in grid_gdf.columns and "centroid_lon" in grid_gdf.columns:
            _ok(f"Hexagonal centroids verified (lat: [{grid_gdf['centroid_lat'].min():.2f}, {grid_gdf['centroid_lat'].max():.2f}])")
        else:
            result.warnings.append("Centroid coordinates not present in grid GeoDataFrame")
            score -= 10

        # Sample cell to latlng check
        sample_cell = grid_gdf["zone_id"].iloc[0]
        c_lat, c_lon = h3.cell_to_latlng(sample_cell)
        _ok(f"H3 v4 API verification: cell {sample_cell} -> ({c_lat:.4f}, {c_lon:.4f})")

        result.success = True

    except Exception as exc:
        result.errors.append(str(exc))
        result.errors.append(traceback.format_exc())
        score = max(0, score - 40)
        _err(f"Exception: {exc}")

    result.score = max(0, score)
    result.ended_at = _now()
    return result


# ---------------------------------------------------------------------------
# Stage 9: Entity Resolution
# ---------------------------------------------------------------------------

def stage_entity_resolution() -> StageResult:
    """Stage 9 - Spatial Snapping and Entity Correspondence."""
    result = StageResult(9, "Entity Resolution")
    result.started_at = _now()
    score = 100

    try:
        from spatial.snapping import SpatialEntityResolver

        resolver = SpatialEntityResolver()
        station_mapping_df = resolver.resolve_all_stations()
        _ok(f"Resolved {len(station_mapping_df)} monitoring stations to H3 zones:")

        for _, row in station_mapping_df.iterrows():
            _info(f"  Station {row['station_id']} ({row['station_name'][:25]}...): zone={row['zone_id']}, dist={row['distance_m']:.1f}m, status={row['is_valid']}")

        # Verify snapping distances
        max_dist_m = station_mapping_df["distance_m"].max()
        all_valid = (station_mapping_df["is_valid"] == "valid").all()
        _ok(f"Snapping validation: max distance = {max_dist_m:.1f}m, all stations valid = {all_valid}")

        if not all_valid:
            result.warnings.append("Some stations flagged as warning or invalid distance")
            score -= 15

        # Master entity correspondence table
        corr_table = resolver.build_entity_correspondence_table()
        _ok(f"Master entity_correspondence table generated: {len(corr_table)} mappings")
        result.records = len(corr_table)
        result.metrics["entity_correspondence_rows"] = len(corr_table)
        result.metrics["max_station_snap_dist_m"] = round(float(max_dist_m), 1)

        result.success = True

    except Exception as exc:
        result.errors.append(str(exc))
        result.errors.append(traceback.format_exc())
        score = max(0, score - 40)
        _err(f"Exception: {exc}")

    result.score = max(0, score)
    result.ended_at = _now()
    return result


# ---------------------------------------------------------------------------
# Stage 10: Space-Time Fusion
# ---------------------------------------------------------------------------

def stage_fusion() -> StageResult:
    """Stage 10 - Space-Time Master Analytical Dataset (fused_zone_time)."""
    result = StageResult(10, "Space-Time Fusion")
    result.started_at = _now()
    score = 100

    try:
        import pandas as pd
        fused_pq = PROJECT_ROOT / "data" / "fused_zone_time.parquet"
        fused_csv = PROJECT_ROOT / "data" / "fused_zone_time.csv"

        target_file = fused_pq if fused_pq.exists() else fused_csv
        if not target_file.exists():
            result.errors.append("fused_zone_time dataset not found")
            result.score = 0
            result.ended_at = _now()
            return result

        df = pd.read_parquet(target_file) if target_file.suffix == ".parquet" else pd.read_csv(target_file)
        n_rows = len(df)
        n_cols = len(df.columns)
        _ok(f"Loaded fused master dataset: {n_rows:,} records, {n_cols} columns")
        result.records = n_rows
        result.metrics["row_count"] = n_rows
        result.metrics["column_count"] = n_cols

        # 1. H3 zones and stations check
        n_zones = df["zone_id"].nunique() if "zone_id" in df.columns else 0
        n_stations = df["station_id"].nunique() if "station_id" in df.columns else 0
        _ok(f"Spatial coverage: {n_zones} H3 zones, {n_stations} stations")
        result.metrics["zone_count"] = n_zones
        result.metrics["station_count"] = n_stations

        # 2. Check traffic columns (must be present and remain 100% NULL)
        traffic_cols = ["traffic_speed", "traffic_congestion", "traffic_travel_time", "traffic_confidence"]
        for tc in traffic_cols:
            if tc in df.columns:
                null_pct = df[tc].isna().mean() * 100
                _ok(f"Traffic column '{tc}': {null_pct:.1f}% NULL (expected 100% NULL)")
                result.metrics[f"{tc}_null_pct"] = null_pct
                if null_pct < 100.0:
                    result.warnings.append(f"Traffic column {tc} has unexpected non-null values")
                    score -= 10
            else:
                result.warnings.append(f"Traffic column {tc} missing in fused schema")
                score -= 10

        # 3. Weather completeness in fused table
        if "temperature_2m" in df.columns:
            wx_null = round(float(df["temperature_2m"].isna().mean() * 100), 2)
            _ok(f"Weather feature completeness: temperature_2m null = {wx_null}%")
            result.metrics["temperature_null_pct"] = wx_null

        result.success = True

    except Exception as exc:
        result.errors.append(str(exc))
        result.errors.append(traceback.format_exc())
        score = max(0, score - 40)
        _err(f"Exception: {exc}")

    result.score = max(0, score)
    result.ended_at = _now()
    return result


# ---------------------------------------------------------------------------
# Stage 11: Baseline Forecasting Framework
# ---------------------------------------------------------------------------

def stage_forecasting() -> StageResult:
    """Stage 11 - Baseline AQI Forecasting Models & Feature Pipeline."""
    result = StageResult(11, "Baseline Forecasting")
    result.started_at = _now()
    score = 100

    try:
        import pandas as pd
        from models.features import build_feature_matrix

        # 1. Verify feature generation from fused data
        fused_pq = PROJECT_ROOT / "data" / "fused_zone_time.parquet"
        if fused_pq.exists():
            df_fused = pd.read_parquet(fused_pq)
            feat_df, feat_names = build_feature_matrix(df_fused, target_col="aqi")
            _ok(f"Feature matrix generated: {feat_df.shape[0]:,} samples, {len(feat_names)} engineered features")
            result.metrics["feature_matrix_samples"] = feat_df.shape[0]
            result.metrics["feature_names_count"] = len(feat_names)
        else:
            result.warnings.append("fused_zone_time.parquet missing for feature test")
            score -= 15

        # 2. Check baseline evaluation results
        results_csv = PROJECT_ROOT / "reports" / "models" / "baseline_results.csv"
        metrics_json = PROJECT_ROOT / "reports" / "models" / "metrics.json"

        if results_csv.exists():
            res_df = pd.read_csv(results_csv)
            _ok(f"Model comparison table loaded: {len(res_df)} trained model baselines")
            for _, r in res_df.iterrows():
                m_name = r.get("label", r.get("model_key", r.get("model", "Unknown")))
                rmse = r.get("cv_rmse", r.get("rmse", "N/A"))
                mae = r.get("cv_mae", r.get("mae", "N/A"))
                r2 = r.get("cv_r2", r.get("r2", "N/A"))
                rmse_str = f"{float(rmse):.2f}" if isinstance(rmse, (int, float)) else str(rmse)
                mae_str = f"{float(mae):.2f}" if isinstance(mae, (int, float)) else str(mae)
                r2_str = f"{float(r2):.4f}" if isinstance(r2, (int, float)) else str(r2)
                _info(f"  {m_name}: RMSE={rmse_str}, MAE={mae_str}, R2={r2_str}")
            result.records = len(res_df)
            result.metrics["baseline_models_count"] = len(res_df)
        else:
            result.warnings.append("baseline_results.csv not found")
            score -= 20

        if metrics_json.exists():
            with open(metrics_json, "r") as f:
                metrics_data = json.load(f)
            _ok(f"Forecasting metrics JSON loaded ({len(metrics_data)} model summaries)")
        else:
            result.warnings.append("metrics.json not found")
            score -= 10

        # 3. Check visual artifacts
        expected_plots = [
            "feature_importance.png", "model_comparison.png",
            "prediction_vs_actual.png", "residual_plot.png"
        ]
        models_dir = PROJECT_ROOT / "reports" / "models"
        plots_found = 0
        for p in expected_plots:
            if (models_dir / p).exists():
                plots_found += 1
            else:
                result.warnings.append(f"Forecasting plot missing: {p}")
        _ok(f"Evaluation plots verified: {plots_found}/{len(expected_plots)} present")

        result.success = True

    except Exception as exc:
        result.errors.append(str(exc))
        result.errors.append(traceback.format_exc())
        score = max(0, score - 40)
        _err(f"Exception: {exc}")

    result.score = max(0, score)
    result.ended_at = _now()
    return result


# ---------------------------------------------------------------------------
# Stage 12: Dashboard Generation
# ---------------------------------------------------------------------------

def stage_dashboards() -> StageResult:
    """Stage 12 - Dashboard Artifact Generation."""
    result = StageResult(12, "Dashboard Generation")
    result.started_at = _now()
    score = 100

    dashboard_callers = [
        ("Historical AQI", "dashboard.historical_aqi", "export_standalone_dashboard"),
        ("Space-Time Fusion", "dashboard.fusion", "export_fusion_dashboard_html"),
        ("Baseline Forecasting", "dashboard.forecasting", "export_forecasting_dashboard_html"),
        ("TomTom Traffic", "dashboard.traffic", "export_traffic_dashboard_html"),
    ]

    generated_count = 0
    for name, mod_name, fn_name in dashboard_callers:
        try:
            mod = importlib.import_module(mod_name)
            fn = getattr(mod, fn_name)
            out_path = fn()
            out_file = Path(out_path)
            if out_file.exists() and out_file.stat().st_size > 1000:
                _ok(f"Dashboard {name}: Generated {out_file.name} ({out_file.stat().st_size:,} bytes)")
                result.metrics[f"{name.lower().replace(' ', '_')}_size_bytes"] = out_file.stat().st_size
                generated_count += 1
            else:
                _warn(f"Dashboard {name}: Output empty or missing")
                result.warnings.append(f"{name} dashboard output empty")
                score -= 20
        except Exception as exc:
            _err(f"Dashboard {name} failed: {exc}")
            result.errors.append(f"{name} error: {exc}")
            score -= 25

    result.records = generated_count
    result.metrics["dashboards_generated"] = generated_count
    result.metrics["dashboards_total"] = len(dashboard_callers)
    result.success = generated_count > 0

    result.score = max(0, score)
    result.ended_at = _now()
    return result


# ---------------------------------------------------------------------------
# Report writers
# ---------------------------------------------------------------------------

def write_reports(stages: List[StageResult], total_elapsed: float) -> None:
    """Write all validation reports to reports/system_validation/."""
    overall_score = int(sum(s.score for s in stages) / len(stages)) if stages else 0

    # 1. validation_summary.md
    md_lines = [
        "# UrbanTwin System Validation & Integration Report",
        f"\n**Execution Timestamp:** {RUN_TIMESTAMP}",
        f"\n**Total Execution Duration:** {total_elapsed:.2f} seconds",
        f"\n**Overall System Health Score:** {overall_score}/100\n",
        "## Pipeline Stages Execution Summary\n",
        "| # | Module / Pipeline Stage | Status | Score | Duration (s) | Records / Items | Findings & Diagnostics |",
        "|---|-------------------------|--------|-------|--------------|-----------------|------------------------|",
    ]
    for s in stages:
        notes = "; ".join(s.warnings[:2] + [f"ERR: {e[:40]}" for e in s.errors[:1]])
        if not notes:
            notes = "All checks passed cleanly"
        md_lines.append(
            f"| {s.stage_index} | {s.stage_name} | **{s.status_label}** "
            f"| {s.score}/100 | {s.duration_s:.2f} | {s.records:,} | {notes} |"
        )

    md_lines.append("\n## Module Health Breakdown\n")
    for s in stages:
        md_lines.append(f"- **{s.stage_name}**: {s.score}/100 ({s.status_label}) - {s.records:,} records processed in {s.duration_s:.2f}s")

    md_path = REPORTS_DIR / "validation_summary.md"
    md_path.write_text("\n".join(md_lines), encoding="utf-8")
    _ok(f"Generated: {md_path}")

    # 2. validation_summary.json
    json_payload = {
        "run_timestamp": RUN_TIMESTAMP,
        "overall_health_score": overall_score,
        "total_elapsed_seconds": round(total_elapsed, 3),
        "stages": [
            {
                "stage_index": s.stage_index,
                "stage_name": s.stage_name,
                "status": s.status_label,
                "score": s.score,
                "duration_s": s.duration_s,
                "records": s.records,
                "success": s.success,
                "warnings": s.warnings,
                "errors": [e[:300] for e in s.errors],
                "metrics": s.metrics,
            }
            for s in stages
        ],
    }
    json_path = REPORTS_DIR / "validation_summary.json"
    json_path.write_text(json.dumps(json_payload, indent=2, default=str), encoding="utf-8")
    _ok(f"Generated: {json_path}")

    # 3. pipeline_execution_log.csv
    log_path = REPORTS_DIR / "pipeline_execution_log.csv"
    with open(log_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["stage_index", "stage_name", "status", "health_score", "duration_seconds", "records", "warnings", "errors"])
        for s in stages:
            w.writerow([
                s.stage_index, s.stage_name, s.status_label, s.score,
                s.duration_s, s.records,
                "|".join(s.warnings), "|".join(e[:100] for e in s.errors),
            ])
    _ok(f"Generated: {log_path}")

    # 4. database_health.csv
    db_path = REPORTS_DIR / "database_health.csv"
    db_stage = next((s for s in stages if s.stage_index == 2), None)
    with open(db_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["table_name", "primary_key", "foreign_keys_count", "indexes_count", "unique_constraints_count", "row_count", "source", "status"])
        if db_stage and "schema_tables" in db_stage.metrics:
            for tbl_name, info in db_stage.metrics["schema_tables"].items():
                rows = db_stage.metrics.get("db_rows", {}).get(tbl_name, "N/A")
                source = "live_postgresql" if db_stage.metrics.get("live_db_connected") else "parquet_fallback"
                w.writerow([
                    tbl_name,
                    ",".join(info.get("primary_key", [])),
                    len(info.get("foreign_keys", [])),
                    len(info.get("indexes", [])),
                    len(info.get("unique_constraints", [])),
                    rows,
                    source,
                    "valid",
                ])
    _ok(f"Generated: {db_path}")

    # 5. api_health.csv
    api_path = REPORTS_DIR / "api_health.csv"
    traffic_stage = next((s for s in stages if s.stage_index == 7), None)
    with open(api_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["api_name", "endpoint_tested", "status", "latency_seconds", "coverage_percentage", "records_retrieved", "failures"])
        if traffic_stage:
            w.writerow([
                "TomTom Traffic API",
                "Flow Segment Data (v4)",
                traffic_stage.status_label,
                traffic_stage.metrics.get("average_latency_seconds", "N/A"),
                traffic_stage.metrics.get("coverage_percentage", "N/A"),
                traffic_stage.metrics.get("points_collected", 0),
                traffic_stage.metrics.get("failed_requests", 0),
            ])
    _ok(f"Generated: {api_path}")

    # 6. performance_metrics.csv
    perf_path = REPORTS_DIR / "performance_metrics.csv"
    with open(perf_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["stage_index", "stage_name", "duration_seconds", "records_processed", "health_score"])
        for s in stages:
            w.writerow([s.stage_index, s.stage_name, s.duration_s, s.records, s.score])
    _ok(f"Generated: {perf_path}")

    # 7. validation_errors.md
    err_lines = [
        "# UrbanTwin System Validation - Diagnostics and Issues\n",
        f"**Run:** {RUN_TIMESTAMP}\n",
    ]
    has_issues = False
    for s in stages:
        if s.errors or s.warnings:
            has_issues = True
            err_lines.append(f"### Stage {s.stage_index}: {s.stage_name} (Score: {s.score}/100, Status: {s.status_label})")
            if s.warnings:
                err_lines.append("**Warnings / Non-Critical Findings:**")
                for w in s.warnings:
                    err_lines.append(f"- {w}")
            if s.errors:
                err_lines.append("**Errors Encountered:**")
                for e in s.errors:
                    err_lines.append(f"```text\n{e}\n```")
            err_lines.append("")

    if not has_issues:
        err_lines.append("No errors or warnings detected across any of the 12 pipeline stages.")

    err_path = REPORTS_DIR / "validation_errors.md"
    err_path.write_text("\n".join(err_lines), encoding="utf-8")
    _ok(f"Generated: {err_path}")


# ---------------------------------------------------------------------------
# Console summary
# ---------------------------------------------------------------------------

def _health_bar(score: int, width: int = 15) -> str:
    filled = int(score / 100 * width)
    return "[" + "=" * filled + " " * (width - filled) + f"] {score:3d}/100"


def print_summary(stages: List[StageResult], total_elapsed: float) -> None:
    overall = int(sum(s.score for s in stages) / len(stages)) if stages else 0
    _banner("URBANTWIN SYSTEM VALIDATION SUMMARY")
    print(f"  {'#':<3} {'Pipeline Stage':<28} {'Status':<6} {'Score':<22} {'Duration':>8}s  {'Records':>9}")
    print(f"  {'-'*3} {'-'*28} {'-'*6} {'-'*22} {'-'*9}  {'-'*9}")
    for s in stages:
        bar = _health_bar(s.score)
        print(f"  {s.stage_index:<3} {s.stage_name:<28} {s.status_label:<6} {bar}  {s.duration_s:>8.2f}s  {s.records:>9,}")

    print(f"  {'-'*83}")
    print(f"  {'AGGREGATE HEALTH SCORE':<38} {_health_bar(overall)}")
    print(f"\n  Total Execution Time: {total_elapsed:.2f} seconds")
    print(f"  Detailed Reports Saved: {REPORTS_DIR}")

    passed = sum(1 for s in stages if s.status_label == "PASS")
    warned = sum(1 for s in stages if s.status_label == "WARN")
    failed = sum(1 for s in stages if s.status_label == "FAIL")
    print(f"\n  Summary: {passed} PASS | {warned} WARN | {failed} FAIL (Total {len(stages)} Stages)")


# ---------------------------------------------------------------------------
# Main Orchestrator
# ---------------------------------------------------------------------------

STAGE_RUNNERS = [
    stage_environment,
    stage_database,
    stage_migration_status,
    stage_aqi_import,
    stage_aqi_quality,
    stage_weather,
    stage_traffic,
    stage_h3_spatial,
    stage_entity_resolution,
    stage_fusion,
    stage_forecasting,
    stage_dashboards,
]


def run_full_pipeline() -> Tuple[List[StageResult], float]:
    """Execute all validation stages in sequential order."""
    wall_start = time.monotonic()
    results: List[StageResult] = []

    for idx, fn in enumerate(STAGE_RUNNERS, start=1):
        doc = fn.__doc__.splitlines()[0].strip() if fn.__doc__ else fn.__name__
        _banner(doc)
        try:
            res = fn()
        except Exception as exc:
            res = StageResult(idx, fn.__name__)
            res.errors.append(f"Unexpected unhandled error: {exc}")
            res.errors.append(traceback.format_exc())
            res.score = 0
            res.ended_at = _now()
            _err(f"Unhandled failure in {fn.__name__}: {exc}")

        results.append(res)
        _info(f"Stage completed in {res.duration_s:.2f}s with score {res.score}/100 ({res.status_label})")

    total_elapsed = time.monotonic() - wall_start
    return results, total_elapsed


def main() -> int:
    print("=" * 65)
    print("  UrbanTwin End-to-End System Validation & Integration Testing")
    print(f"  Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 65)

    stages, elapsed = run_full_pipeline()

    _banner("Generating Validation Reports")
    write_reports(stages, elapsed)

    print_summary(stages, elapsed)

    overall = int(sum(s.score for s in stages) / len(stages)) if stages else 0
    return 0 if overall >= 50 else 1


if __name__ == "__main__":
    sys.exit(main())

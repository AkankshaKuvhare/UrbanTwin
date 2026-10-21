"""Unit and integration tests for Milestone 5: Space-Time Data Fusion Engine."""

from datetime import datetime, timezone
import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from main import app
from spatial.utils import haversine_distance_km, haversine_distance_m
from spatial.grid import generate_h3_grid_pmc_pcmc
from spatial.snapping import SpatialEntityResolver
from pipelines.fusion import (
    SpaceTimeFusionEngine,
    TRAFFIC_COLUMNS,
    FUSED_SCHEMA_COLUMNS,
)
from dashboard.fusion import load_fusion_data, build_fusion_dashboard_html

client = TestClient(app)


# ---------------------------------------------------------------------------
# 1. Spatial Foundation & H3 Snapping Tests
# ---------------------------------------------------------------------------


def test_haversine_distance_calculations() -> None:
    """Test haversine formula distance calculations between known Pune points."""
    # Shivajinagar (18.5314, 73.8446) to SPPU (18.5529, 73.8260) ~ 3.1 km
    dist_km = haversine_distance_km(18.5314, 73.8446, 18.5529, 73.8260)
    dist_m = haversine_distance_m(18.5314, 73.8446, 18.5529, 73.8260)

    assert 2.8 <= dist_km <= 3.5
    assert 2800 <= dist_m <= 3500
    # Zero distance between identical coordinates
    assert haversine_distance_m(18.5204, 73.8567, 18.5204, 73.8567) == pytest.approx(0.0)


def test_generate_h3_grid_pmc_pcmc() -> None:
    """Test H3 resolution 7 grid generation covering PMC + PCMC."""
    gdf = generate_h3_grid_pmc_pcmc(resolution=7)
    assert not gdf.empty
    assert len(gdf) > 100
    assert "zone_id" in gdf.columns
    assert "centroid_lat" in gdf.columns
    assert "centroid_lon" in gdf.columns
    assert gdf.crs.to_epsg() == 4326

    # Verify centroids fall within extended Pune bounds
    assert (gdf["centroid_lat"] >= 18.3).all()
    assert (gdf["centroid_lat"] <= 18.8).all()
    assert (gdf["centroid_lon"] >= 73.6).all()
    assert (gdf["centroid_lon"] <= 74.1).all()


def test_spatial_entity_resolver_stations() -> None:
    """Test snapping of AQI stations to nearest H3 Resolution 7 cells."""
    resolver = SpatialEntityResolver(resolution=7)
    df_resolved = resolver.resolve_all_stations()

    assert len(df_resolved) == 5
    assert set(df_resolved["snap_status"].unique()).issubset({"valid", "warning"})

    # All known stations should snap within 1.5 km of cell centroid
    assert (df_resolved["distance_m"] <= 1500).all()
    for _, row in df_resolved.iterrows():
        assert row["zone_id"].startswith("87")
        assert len(row["zone_id"]) == 15


def test_spatial_entity_resolver_custom_thresholds() -> None:
    """Test distance threshold classification for custom coordinates."""
    resolver = SpatialEntityResolver(resolution=7)
    # Point at Pune center
    res_center = resolver.resolve_point(18.5204, 73.8567, entity_name="Center")
    assert res_center["snap_status"] in ("valid", "warning")
    assert res_center["distance_m"] < 3000

    # Point far outside Pune (Mumbai: 19.0760, 72.8777)
    res_outside = resolver.resolve_point(19.0760, 72.8777, entity_name="FarAway")
    assert res_outside["snap_status"] == "invalid"
    assert res_outside["distance_m"] > 3000


# ---------------------------------------------------------------------------
# 2. Space-Time Data Fusion Engine Tests
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_fusion_inputs():
    """Create synthetic AQI and Weather dataframes for deterministic unit testing."""
    # AQI observations for 2 stations across 3 days
    dates = pd.date_range("2024-01-01", periods=3, freq="D", tz="Asia/Kolkata")
    aqi_records = []
    for dt in dates:
        aqi_records.append({
            "station_id": 11613,  # Shivajinagar
            "datetime": dt,
            "aqi": 120.0,
            "pm25": 45.0,
            "pm10": 85.0,
            "no2": 22.0,
            "co": 1.1,
            "so2": 8.0,
            "o3": 14.0,
            "dominant_pollutant": "pm25",
        })
        aqi_records.append({
            "station_id": 3409439,  # SPPU
            "datetime": dt,
            "aqi": 110.0,
            "pm25": 40.0,
            "pm10": 78.0,
            "no2": 19.0,
            "co": 0.9,
            "so2": 7.0,
            "o3": 12.0,
            "dominant_pollutant": "pm10",
        })
    aqi_df = pd.DataFrame(aqi_records)

    # Weather hourly observations
    weather_dates = pd.date_range("2024-01-01", periods=72, freq="h", tz="Asia/Kolkata")
    weather_df = pd.DataFrame({
        "timestamp": weather_dates,
        "temperature_2m": np.linspace(15.0, 30.0, len(weather_dates)),
        "relative_humidity_2m": np.linspace(40.0, 70.0, len(weather_dates)),
        "precipitation": 0.0,
        "wind_speed_10m": 5.5,
        "wind_direction_10m": 180.0,
        "surface_pressure": 950.0,
        "boundary_layer_height": 800.0,
    })

    return aqi_df, weather_df


def test_space_time_fusion_execution(sample_fusion_inputs) -> None:
    """Test the complete space-time fusion pipeline with synthetic inputs."""
    aqi_df, weather_df = sample_fusion_inputs
    engine = SpaceTimeFusionEngine(resolution=7)
    fused_df = engine.fuse_space_time(aqi_df, weather_df)

    # 1. Total records check (2 stations * 3 days = 6)
    assert len(fused_df) == 6

    # 2. Schema columns check
    for col in FUSED_SCHEMA_COLUMNS:
        assert col in fused_df.columns, f"Missing column {col} in fused dataset"

    # 3. Traffic columns MUST be completely NULL (traffic collector is not yet active)
    for col in TRAFFIC_COLUMNS:
        assert fused_df[col].isna().all(), f"Traffic column {col} must be completely NULL"

    # 4. Missingness flags check
    assert fused_df["traffic_missing"].all()  # All traffic missing
    assert not fused_df["weather_missing"].any()  # All weather matched
    assert not fused_df["aqi_missing"].any()  # All AQI present

    # 5. Composite unique index check
    dup_mask = fused_df.duplicated(subset=["zone_id", "observation_datetime", "station_id"])
    assert not dup_mask.any(), "Duplicate space-time entries found"

    # 6. Check weather covariates alignment
    assert not fused_df["temperature_2m"].isna().any()
    assert (fused_df["temperature_2m"] >= 15.0).all()
    assert (fused_df["temperature_2m"] <= 30.0).all()


def test_traffic_columns_strictly_null_in_production_dataset() -> None:
    """Verify that the generated production master dataset data/fused_zone_time.parquet has strictly NULL traffic."""
    df, _ = load_fusion_data()
    for col in TRAFFIC_COLUMNS:
        assert col in df.columns, f"Expected {col} in schema"
        assert df[col].isna().all(), f"Production traffic column {col} must be strictly NULL"
    assert df["traffic_missing"].all(), "traffic_missing flag must be True for all records"


def test_spatial_coverage_in_production_dataset() -> None:
    """Verify that all 5 active Pune monitoring stations are mapped to distinct H3 zones."""
    df, summary = load_fusion_data()
    assert len(df) == 3751
    assert df["zone_id"].nunique() == 5
    assert df["station_id"].nunique() == 5
    assert not df["observation_datetime"].isna().any()
    assert summary.get("weather_completeness_pct") == 100.0 or summary.get("weather_completeness_pct") == "100.0"


# ---------------------------------------------------------------------------
# 3. Dashboard Integration Tests
# ---------------------------------------------------------------------------


def test_dashboard_fusion_endpoint() -> None:
    """Test the FastAPI /dashboard/fusion endpoint returns 200 OK and valid HTML."""
    response = client.get("/dashboard/fusion")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    html_text = response.text
    assert "UrbanTwin Space-Time Fusion Engine" in html_text
    assert "Milestone 5 Operational" in html_text
    assert "fused_zone_time" in html_text
    assert "chart-zones" in html_text
    assert "chart-timeline" in html_text
    assert "chart-temp-scatter" in html_text
    assert "chart-missing" in html_text

"""Unit and integration tests for real traffic pipeline integration into fused_zone_time.

Covers:
✓ no traffic available (empty df / None fallback)
✓ partial traffic coverage (some zones/times matched, others remain NULL)
✓ complete traffic coverage (all space-time records matched)
✓ H3 spatial snapping (mapping traffic points to Resolution 7 cells)
✓ temporal matching (nearest-timestamp merge_asof alignment within tolerance)
✓ merge_asof correctness and tolerance bounds
✓ NULL fallback safety and traffic_missing flags
✓ duplicate traffic observations deduplication and zone aggregation
✓ forecasting feature engineering automatic traffic detection
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path
import json
import numpy as np
import pandas as pd
import pytest

from spatial.snapping import SpatialEntityResolver
from pipelines.fusion import (
    SpaceTimeFusionEngine,
    TRAFFIC_PLACEHOLDER_FIELDS,
    FUSED_SCHEMA_COLUMNS,
)
from models.features import has_traffic_data, build_feature_matrix, TRAFFIC_FEATURES


@pytest.fixture
def base_space_time_data():
    """Create deterministic AQI and Weather observations across 2 zones over 3 days."""
    dates = pd.date_range("2026-10-21 00:00:00", periods=3, freq="D", tz="Asia/Kolkata")
    aqi_records = []
    for dt in dates:
        # Station 11613 (Shivajinagar) -> snaps to 87608850effffff
        aqi_records.append({
            "station_id": "11613",
            "observation_datetime": dt,
            "aqi": 125.0,
            "pm25": 48.0,
            "pm10": 90.0,
            "no2": 24.0,
            "co": 1.2,
            "so2": 9.0,
            "o3": 15.0,
            "dominant_pollutant": "pm25",
        })
        # Station 3409439 (SPPU) -> snaps to 87608850dffffff
        aqi_records.append({
            "station_id": "3409439",
            "observation_datetime": dt,
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

    weather_dates = pd.date_range("2026-10-21 00:00:00", periods=72, freq="h", tz="Asia/Kolkata")
    weather_df = pd.DataFrame({
        "weather_datetime": weather_dates,
        "temperature_2m": np.linspace(20.0, 32.0, len(weather_dates)),
        "relative_humidity_2m": np.linspace(45.0, 75.0, len(weather_dates)),
        "precipitation": 0.0,
        "wind_speed_10m": 4.2,
        "wind_direction_10m": 160.0,
        "surface_pressure": 952.0,
        "boundary_layer_height": 750.0,
    })

    return aqi_df, weather_df


# ---------------------------------------------------------------------------
# 1. No Traffic Available Tests
# ---------------------------------------------------------------------------

def test_fusion_no_traffic_available(base_space_time_data):
    """When no traffic observations exist (None or empty), traffic columns remain NULL and traffic_missing=True."""
    aqi_df, weather_df = base_space_time_data
    engine = SpaceTimeFusionEngine(resolution=7)

    # Test with traffic_df=None
    fused_none = engine.fuse(aqi_df, weather_df, traffic_df=None)
    assert len(fused_none) == 6
    for col in TRAFFIC_PLACEHOLDER_FIELDS:
        assert fused_none[col].isna().all(), f"{col} must be completely NaN when traffic is None"
    assert fused_none["traffic_missing"].all()

    # Test with empty DataFrame
    fused_empty = engine.fuse(aqi_df, weather_df, traffic_df=pd.DataFrame())
    assert len(fused_empty) == 6
    for col in TRAFFIC_PLACEHOLDER_FIELDS:
        assert fused_empty[col].isna().all(), f"{col} must be completely NaN when traffic is empty df"
    assert fused_empty["traffic_missing"].all()


# ---------------------------------------------------------------------------
# 2. Complete Traffic Coverage Tests
# ---------------------------------------------------------------------------

def test_fusion_complete_traffic_coverage(base_space_time_data):
    """When traffic observations match all space-time cells, columns are populated and traffic_missing=False."""
    aqi_df, weather_df = base_space_time_data
    engine = SpaceTimeFusionEngine(resolution=7)

    # Known zones for Shivajinagar & SPPU
    shv_zone = engine.station_zone_map.set_index("station_id").loc["11613", "zone_id"]
    sppu_zone = engine.station_zone_map.set_index("station_id").loc["3409439", "zone_id"]

    dates = pd.date_range("2026-10-21 00:00:00", periods=3, freq="D", tz="Asia/Kolkata")
    traffic_records = []
    for dt in dates:
        # Traffic for Shivajinagar zone
        traffic_records.append({
            "zone_id": shv_zone,
            "traffic_datetime": dt,
            "traffic_speed": 22.5,
            "traffic_congestion": 0.45,
            "traffic_travel_time": 320.0,
            "traffic_confidence": 0.95,
        })
        # Traffic for SPPU zone
        traffic_records.append({
            "zone_id": sppu_zone,
            "traffic_datetime": dt,
            "traffic_speed": 34.0,
            "traffic_congestion": 0.20,
            "traffic_travel_time": 180.0,
            "traffic_confidence": 1.0,
        })
    traffic_df = pd.DataFrame(traffic_records)

    fused = engine.fuse(aqi_df, weather_df, traffic_df=traffic_df)
    assert len(fused) == 6

    # Every single row must have traffic populated
    for col in TRAFFIC_PLACEHOLDER_FIELDS:
        assert fused[col].notna().all(), f"Expected no NaN in {col}"
    assert not fused["traffic_missing"].any(), "traffic_missing must be False for all matched rows"

    # Verify values
    shv_rows = fused[fused["zone_id"] == shv_zone]
    assert np.allclose(shv_rows["traffic_speed"], 22.5)
    assert np.allclose(shv_rows["traffic_congestion"], 0.45)


# ---------------------------------------------------------------------------
# 3. Partial Traffic Coverage Tests
# ---------------------------------------------------------------------------

def test_fusion_partial_traffic_coverage(base_space_time_data):
    """When traffic only covers one zone, the other zone remains NULL with traffic_missing=True."""
    aqi_df, weather_df = base_space_time_data
    engine = SpaceTimeFusionEngine(resolution=7)

    shv_zone = engine.station_zone_map.set_index("station_id").loc["11613", "zone_id"]
    sppu_zone = engine.station_zone_map.set_index("station_id").loc["3409439", "zone_id"]

    dates = pd.date_range("2026-10-21 00:00:00", periods=3, freq="D", tz="Asia/Kolkata")
    # Only supply traffic for Shivajinagar
    traffic_records = [
        {
            "zone_id": shv_zone,
            "traffic_datetime": dt,
            "traffic_speed": 25.0,
            "traffic_congestion": 0.35,
            "traffic_travel_time": 250.0,
            "traffic_confidence": 0.9,
        }
        for dt in dates
    ]
    traffic_df = pd.DataFrame(traffic_records)

    fused = engine.fuse(aqi_df, weather_df, traffic_df=traffic_df)
    assert len(fused) == 6

    shv_fused = fused[fused["zone_id"] == shv_zone]
    sppu_fused = fused[fused["zone_id"] == sppu_zone]

    # Shivajinagar has traffic
    assert not shv_fused["traffic_missing"].any()
    assert shv_fused["traffic_speed"].notna().all()
    assert np.allclose(shv_fused["traffic_speed"], 25.0)

    # SPPU has NO traffic
    assert sppu_fused["traffic_missing"].all()
    assert sppu_fused["traffic_speed"].isna().all()
    assert sppu_fused["traffic_congestion"].isna().all()


# ---------------------------------------------------------------------------
# 4. H3 Spatial Snapping Tests
# ---------------------------------------------------------------------------

def test_traffic_h3_spatial_matching():
    """Verify traffic points correctly snap to H3 Resolution 7 cells reusing resolver."""
    engine = SpaceTimeFusionEngine(resolution=7)

    raw_traffic = pd.DataFrame([
        {
            "point_id": "PT_JM_ROAD",
            "latitude": 18.5285,
            "longitude": 73.8475,
            "timestamp": "2026-10-21T10:00:00Z",
            "current_speed": 28.0,
            "free_flow_speed": 45.0,
            "current_travel_time": 150.0,
            "confidence": 1.0,
        },
        {
            "point_id": "PT_FC_ROAD",
            "latitude": 18.5250,
            "longitude": 73.8415,
            "timestamp": "2026-10-21T10:00:00Z",
            "current_speed": 18.0,
            "free_flow_speed": 40.0,
            "current_travel_time": 220.0,
            "confidence": 0.8,
        },
    ])

    prep = engine.prepare_traffic_data(raw_traffic)
    assert not prep.empty
    assert "zone_id" in prep.columns
    for z in prep["zone_id"]:
        assert z.startswith("87")
        assert len(z) == 15


# ---------------------------------------------------------------------------
# 5. Temporal Matching and merge_asof Tolerance Tests
# ---------------------------------------------------------------------------

def test_traffic_temporal_merge_asof_tolerance(base_space_time_data):
    """Verify merge_asof tolerance: observations within 1 hour match; beyond 1 hour do not."""
    aqi_df, weather_df = base_space_time_data
    engine = SpaceTimeFusionEngine(resolution=7)
    shv_zone = engine.station_zone_map.set_index("station_id").loc["11613", "zone_id"]

    # AQI is at 2026-10-21 00:00:00
    # Create traffic at 00:25:00 (within 1h) and another at 02:30:00 (outside 1h)
    traffic_df = pd.DataFrame([
        {
            "zone_id": shv_zone,
            "traffic_datetime": pd.Timestamp("2026-10-21 00:25:00", tz="Asia/Kolkata"),
            "traffic_speed": 20.0,
            "traffic_congestion": 0.50,
            "traffic_travel_time": 300.0,
            "traffic_confidence": 1.0,
        },
        {
            "zone_id": shv_zone,
            "traffic_datetime": pd.Timestamp("2026-10-22 02:30:00", tz="Asia/Kolkata"),
            "traffic_speed": 45.0,
            "traffic_congestion": 0.10,
            "traffic_travel_time": 100.0,
            "traffic_confidence": 1.0,
        },
    ])

    fused = engine.fuse(aqi_df, weather_df, traffic_df=traffic_df, traffic_tolerance=pd.Timedelta("1h"))

    # Day 1 (2026-10-21 00:00) should match 00:25:00 (+25m delta <= 1h)
    day1_shv = fused[(fused["zone_id"] == shv_zone) & (fused["observation_datetime"] == pd.Timestamp("2026-10-21 00:00:00", tz="Asia/Kolkata"))]
    assert not day1_shv["traffic_missing"].values[0]
    assert day1_shv["traffic_speed"].values[0] == 20.0

    # Day 2 (2026-10-22 00:00) vs 02:30:00 is 2h30m delta > 1h tolerance -> should NOT match
    day2_shv = fused[(fused["zone_id"] == shv_zone) & (fused["observation_datetime"] == pd.Timestamp("2026-10-22 00:00:00", tz="Asia/Kolkata"))]
    assert day2_shv["traffic_missing"].values[0]
    assert np.isnan(day2_shv["traffic_speed"].values[0])


# ---------------------------------------------------------------------------
# 6. Duplicate Observations and Multi-Point Zone Aggregation Tests
# ---------------------------------------------------------------------------

def test_traffic_deduplication_and_zone_aggregation():
    """Verify duplicate (point_id, timestamp) rows are deduplicated and multi-point zone clusters averaged."""
    engine = SpaceTimeFusionEngine(resolution=7)

    now = "2026-10-21T12:00:00Z"
    # Duplicate point PT1
    # Different point PT2 in same zone
    raw_traffic = pd.DataFrame([
        {
            "point_id": "PT1",
            "latitude": 18.5314,
            "longitude": 73.8446,
            "timestamp": now,
            "current_speed": 20.0,
            "free_flow_speed": 50.0,
            "current_travel_time": 200.0,
            "confidence": 0.8,
        },
        {
            # Exact duplicate of PT1 (should be dropped)
            "point_id": "PT1",
            "latitude": 18.5314,
            "longitude": 73.8446,
            "timestamp": now,
            "current_speed": 20.0,
            "free_flow_speed": 50.0,
            "current_travel_time": 200.0,
            "confidence": 0.8,
        },
        {
            # Point PT2 very close (same H3 zone, 100m away)
            "point_id": "PT2",
            "latitude": 18.5320,
            "longitude": 73.8450,
            "timestamp": now,
            "current_speed": 30.0,
            "free_flow_speed": 50.0,
            "current_travel_time": 100.0,
            "confidence": 1.0,
        },
    ])

    prep = engine.prepare_traffic_data(raw_traffic)
    # Both points snap to the same Shivajinagar zone
    assert len(prep) == 1
    # Average speed = (20 + 30) / 2 = 25.0
    assert prep["traffic_speed"].values[0] == pytest.approx(25.0)
    # Average travel time = (200 + 100) / 2 = 150.0
    assert prep["traffic_travel_time"].values[0] == pytest.approx(150.0)


# ---------------------------------------------------------------------------
# 7. Model Feature Engineering Auto-Detection Tests
# ---------------------------------------------------------------------------

def test_forecasting_feature_detection(base_space_time_data):
    """Verify that models.features automatically detects traffic when populated."""
    aqi_df, weather_df = base_space_time_data
    engine = SpaceTimeFusionEngine(resolution=7)

    # 1. Without traffic
    fused_no_traffic = engine.fuse(aqi_df, weather_df, traffic_df=None)
    assert not has_traffic_data(fused_no_traffic), "has_traffic_data must return False when all traffic is NULL"

    # 2. With traffic
    shv_zone = engine.station_zone_map.set_index("station_id").loc["11613", "zone_id"]
    traffic_df = pd.DataFrame([{
        "zone_id": shv_zone,
        "traffic_datetime": pd.Timestamp("2026-10-21 00:00:00", tz="Asia/Kolkata"),
        "traffic_speed": 26.0,
        "traffic_congestion": 0.30,
        "traffic_travel_time": 210.0,
        "traffic_confidence": 0.95,
    }])
    fused_with_traffic = engine.fuse(aqi_df, weather_df, traffic_df=traffic_df)
    assert has_traffic_data(fused_with_traffic), "has_traffic_data must return True when traffic is populated"

    # Verify build_feature_matrix includes traffic features
    _, feature_cols = build_feature_matrix(fused_with_traffic, include_traffic=True)
    assert "traffic_speed" in feature_cols
    assert "traffic_congestion" in feature_cols

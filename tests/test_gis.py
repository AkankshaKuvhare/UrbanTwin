"""Tests for Milestone 9 – Interactive GIS & Digital Twin Map."""

from pathlib import Path
import json
import pytest
from fastapi.testclient import TestClient
import pandas as pd

from main import app
from gis.layers import (
    load_station_layer,
    load_h3_layer,
    load_traffic_layer,
    load_weather_layer,
    get_aqi_color,
    get_aqi_category,
    STATION_META,
)
from gis.geojson_export import (
    export_stations_geojson,
    export_h3_zones_geojson,
    export_traffic_geojson,
    export_all_geojson,
    validate_geojson,
)
from gis.map_builder import (
    build_pune_map,
    export_map_html,
    export_map_png,
    generate_map_statistics,
)
from gis.dashboard import build_gis_dashboard_html


client = TestClient(app)


# ===========================================================================
# 1. Layer Tests
# ===========================================================================

def test_aqi_color_and_category_mapping():
    """Verify AQI categories and corresponding color hexes according to CPCB NAQI."""
    assert get_aqi_color(25) == "#22c55e"
    assert get_aqi_category(25) == "Good"

    assert get_aqi_color(75) == "#84cc16"
    assert get_aqi_category(75) == "Satisfactory"

    assert get_aqi_color(150) == "#f59e0b"
    assert get_aqi_category(150) == "Moderate"

    assert get_aqi_color(250) == "#f97316"
    assert get_aqi_category(250) == "Poor"

    assert get_aqi_color(350) == "#ef4444"
    assert get_aqi_category(350) == "Very Poor"

    assert get_aqi_color(450) == "#7c3aed"
    assert get_aqi_category(450) == "Severe"

    assert get_aqi_color(None) == "#94a3b8"
    assert get_aqi_category(None) == "Unknown"


def test_station_layer_loading():
    """Verify station layer loads all 5 Pune stations with metadata and pollutant fields."""
    stations = load_station_layer()
    assert isinstance(stations, pd.DataFrame)
    assert len(stations) == len(STATION_META)
    expected_cols = ["station_id", "name", "lat", "lon", "aqi", "pm25", "pm10", "no2", "co", "so2", "o3", "aqi_color", "aqi_category"]
    for col in expected_cols:
        assert col in stations.columns


def test_h3_layer_loading():
    """Verify H3 hexagonal zone layer loads successfully with resolution 7 cells."""
    zones = load_h3_layer()
    assert isinstance(zones, pd.DataFrame)
    assert len(zones) > 0
    assert "zone_id" in zones.columns
    assert "centroid_lat" in zones.columns
    assert "centroid_lon" in zones.columns
    assert "aqi_color" in zones.columns


def test_traffic_layer_loading():
    """Verify traffic layer handles existing or empty traffic gracefully."""
    traffic = load_traffic_layer()
    assert isinstance(traffic, pd.DataFrame)
    # Check that if not empty, essential columns exist
    if not traffic.empty:
        assert any(c in traffic.columns for c in ["current_speed", "speed"])
        assert any(c in traffic.columns for c in ["lat", "latitude"])


def test_weather_layer_loading():
    """Verify weather layer returns meteorological observations."""
    weather = load_weather_layer()
    assert isinstance(weather, pd.DataFrame)
    assert len(weather) > 0
    assert "temperature_2m" in weather.columns
    assert "station_id" in weather.columns


# ===========================================================================
# 2. GeoJSON Export & Validation Tests
# ===========================================================================

def test_export_and_validate_stations_geojson(tmp_path: Path):
    """Test stations GeoJSON export and schema compliance."""
    dest = tmp_path / "test_stations.geojson"
    out_path = export_stations_geojson(dest)
    assert out_path.exists()

    val = validate_geojson(out_path)
    assert val["valid"] is True
    assert val["feature_count"] == len(STATION_META)
    assert len(val["errors"]) == 0

    data = json.loads(out_path.read_text(encoding="utf-8"))
    assert data["type"] == "FeatureCollection"
    feat = data["features"][0]
    assert feat["geometry"]["type"] == "Point"
    assert len(feat["geometry"]["coordinates"]) == 2


def test_export_and_validate_h3_zones_geojson(tmp_path: Path):
    """Test H3 zones GeoJSON export and schema compliance."""
    dest = tmp_path / "test_h3_zones.geojson"
    out_path = export_h3_zones_geojson(dest)
    assert out_path.exists()

    val = validate_geojson(out_path)
    assert val["valid"] is True
    assert val["feature_count"] > 0
    assert len(val["errors"]) == 0

    data = json.loads(out_path.read_text(encoding="utf-8"))
    assert data["type"] == "FeatureCollection"
    feat = data["features"][0]
    assert feat["geometry"]["type"] in ("Polygon", "Point")


def test_export_and_validate_traffic_geojson(tmp_path: Path):
    """Test traffic GeoJSON export and schema compliance."""
    dest = tmp_path / "test_traffic.geojson"
    out_path = export_traffic_geojson(dest)
    assert out_path.exists()

    val = validate_geojson(out_path)
    assert val["valid"] is True

    data = json.loads(out_path.read_text(encoding="utf-8"))
    assert data["type"] == "FeatureCollection"


def test_export_all_geojson(tmp_path: Path):
    """Test batch export of all GeoJSON layers."""
    res = export_all_geojson(tmp_path)
    assert "stations" in res
    assert "h3_zones" in res
    assert "traffic" in res
    for name, p in res.items():
        assert p.exists()


# ===========================================================================
# 3. Map Builder & Static Snapshot Tests
# ===========================================================================

def test_build_pune_map():
    """Verify Folium map creation without OSM (for fast offline test)."""
    m = build_pune_map(include_osm=False)
    assert m is not None
    html = m.get_root().render()
    assert "UrbanTwin" in html or "leaflet" in html.lower()


def test_export_map_html(tmp_path: Path):
    """Verify map HTML export to disk."""
    dest = tmp_path / "test_map.html"
    p = export_map_html(output_path=dest, include_osm=False)
    assert p.exists()
    assert dest.stat().st_size > 1000


def test_export_map_png(tmp_path: Path):
    """Verify publication-quality static PNG snapshot generation."""
    dest = tmp_path / "test_map.png"
    p = export_map_png(output_path=dest)
    assert p.exists()
    assert dest.stat().st_size > 1000


def test_generate_map_statistics():
    """Verify computation of map KPI statistics."""
    stats = generate_map_statistics()
    assert isinstance(stats, dict)
    assert "station_count" in stats
    assert "zone_count" in stats
    assert "aqi_coverage_pct" in stats
    assert stats["station_count"] == 5


# ===========================================================================
# 4. Dashboard & API Endpoints Tests
# ===========================================================================

def test_dashboard_map_html():
    """Verify /dashboard/map renders the full-screen GIS shell."""
    res = client.get("/dashboard/map")
    assert res.status_code == 200
    assert "text/html" in res.headers["content-type"]
    assert "UrbanTwin" in res.text
    assert "GIS Digital Twin" in res.text


def test_dashboard_map_embed():
    """Verify /dashboard/map/embed renders the embedded Folium map."""
    res = client.get("/dashboard/map/embed")
    assert res.status_code == 200
    assert "text/html" in res.headers["content-type"]
    assert "leaflet" in res.text.lower() or "map" in res.text.lower()


def test_dashboard_map_static():
    """Verify /dashboard/map/static renders standalone map."""
    res = client.get("/dashboard/map/static")
    assert res.status_code == 200
    assert "text/html" in res.headers["content-type"]


def test_api_v1_map_metadata():
    """Verify /api/v1/map returns statistics and metadata."""
    res = client.get("/api/v1/map")
    assert res.status_code == 200
    data = res.json()
    assert "station_count" in data
    assert "zone_count" in data
    assert data["station_count"] == 5


def test_api_v1_stations():
    """Verify /api/v1/stations returns station records."""
    res = client.get("/api/v1/stations")
    assert res.status_code == 200
    data = res.json()
    assert "count" in data
    assert "stations" in data
    assert data["count"] == 5

    # Filter test
    station_id = "11613"
    res_filtered = client.get(f"/api/v1/stations?station_id={station_id}")
    assert res_filtered.status_code == 200
    filtered_data = res_filtered.json()
    assert filtered_data["count"] == 1
    assert str(filtered_data["stations"][0]["station_id"]) == station_id


def test_api_v1_zones():
    """Verify /api/v1/zones returns H3 zone data."""
    res = client.get("/api/v1/zones?limit=10")
    assert res.status_code == 200
    data = res.json()
    assert "zones" in data
    assert len(data["zones"]) <= 10
    if len(data["zones"]) > 0:
        assert "zone_id" in data["zones"][0]


def test_api_v1_map_geojson():
    """Verify /api/v1/map/geojson triggers exports and returns paths."""
    res = client.get("/api/v1/map/geojson")
    assert res.status_code == 200
    data = res.json()
    assert "exported" in data
    assert "stations" in data["exported"]
    assert "h3_zones" in data["exported"]

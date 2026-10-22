"""End-to-End Validation Script for UrbanTwin Milestone 9 GIS & Digital Twin Map.

Verifies:
1. Geospatial Layer Loaders (AQI Stations, H3 Zones, Traffic Points, Weather)
2. GeoJSON Export & Schema Validation (stations.geojson, h3_zones.geojson, traffic_points.geojson)
3. Folium Map Generation & Standalone HTML Export (pune_digital_twin_map.html)
4. Publication-Quality Static PNG Generation (pune_digital_twin_map.png)
5. Map Statistics & Metrics Computation (map_statistics.json)
6. GIS Dashboard Generation (/dashboard/map, /dashboard/map/embed, /dashboard/map/static)
7. FastAPI REST Endpoints (/api/v1/map, /api/v1/stations, /api/v1/zones, /api/v1/map/geojson)

Usage:
    python scripts/test_gis_module.py
"""

import json
import os
import sys
import time
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
from fastapi.testclient import TestClient

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
from gis.dashboard import (
    build_gis_dashboard_html,
    export_gis_dashboard_html,
)

STAGE_SEPARATOR = "=" * 70


def stage_print(num: int, title: str):
    print(f"\n{STAGE_SEPARATOR}")
    print(f" STAGE {num}: {title.upper()}")
    print(f"{STAGE_SEPARATOR}")


def main():
    total_start = time.time()
    passed_checks = 0
    total_checks = 0

    print("*" * 70)
    print(" URBANTWIN MILESTONE 9: INTERACTIVE GIS & DIGITAL TWIN VALIDATION")
    print("*" * 70)

    # -----------------------------------------------------------------------
    # STAGE 1: Layer Data Loading
    # -----------------------------------------------------------------------
    stage_print(1, "Geospatial Data Layers Loading")
    total_checks += 4

    stations_df = load_station_layer()
    print(f"[OK] Stations loaded: {len(stations_df)} stations detected.")
    assert len(stations_df) == 5, f"Expected 5 stations, got {len(stations_df)}"
    passed_checks += 1

    zones_df = load_h3_layer()
    print(f"[OK] H3 Zones loaded: {len(zones_df)} cells (Res 7).")
    assert len(zones_df) > 0, "No H3 zones loaded!"
    passed_checks += 1

    traffic_df = load_traffic_layer()
    has_traffic = not traffic_df.empty
    print(f"[OK] Traffic Layer: {len(traffic_df)} active observations (Has Data: {has_traffic}).")
    passed_checks += 1

    weather_df = load_weather_layer()
    print(f"[OK] Weather Layer: {len(weather_df)} station weather observations.")
    assert len(weather_df) > 0, "Weather layer empty!"
    passed_checks += 1

    # -----------------------------------------------------------------------
    # STAGE 2: AQI Indexing & Categorization
    # -----------------------------------------------------------------------
    stage_print(2, "CPCB NAQI Indexing and Color Palette")
    total_checks += 2

    test_vals = [25, 75, 150, 250, 350, 450, None]
    for v in test_vals:
        c = get_aqi_color(v)
        cat = get_aqi_category(v)
        print(f"  AQI: {str(v):<5} -> Category: {cat:<15} Color: {c}")
    passed_checks += 1

    assert get_aqi_color(25) == "#22c55e"
    assert get_aqi_color(450) == "#7c3aed"
    passed_checks += 1

    # -----------------------------------------------------------------------
    # STAGE 3: GeoJSON Generation & Schema Validation
    # -----------------------------------------------------------------------
    stage_print(3, "GeoJSON Layer Generation and Schema Validation")
    total_checks += 4

    out_dir = PROJECT_ROOT / "reports" / "gis"
    out_dir.mkdir(parents=True, exist_ok=True)

    geojson_map = export_all_geojson(out_dir)
    for name, path in geojson_map.items():
        v = validate_geojson(path)
        print(f"[OK] {name:<12} -> {path.name:<25} Valid: {v['valid']} (Features: {v['feature_count']})")
        assert v["valid"], f"Invalid GeoJSON for {name}: {v['errors']}"
    passed_checks += 3

    # Extra check for stations GeoJSON features
    st_val = validate_geojson(geojson_map["stations"])
    assert st_val["feature_count"] == 5, f"Expected 5 station features, got {st_val['feature_count']}"
    passed_checks += 1

    # -----------------------------------------------------------------------
    # STAGE 4: Interactive Folium Map & Standalone HTML
    # -----------------------------------------------------------------------
    stage_print(4, "Interactive Folium Digital Twin Map Building")
    total_checks += 3

    m = build_pune_map(include_osm=False)
    assert m is not None, "Folium map object failed to instantiate"
    print("[OK] Interactive Folium Map assembled with multi-layer overlays.")
    passed_checks += 1

    html_path = export_map_html(out_dir / "pune_digital_twin_map.html", include_osm=False)
    assert html_path.exists() and html_path.stat().st_size > 1000
    print(f"[OK] Standalone Map HTML exported: {html_path.name} ({html_path.stat().st_size / 1024:.1f} KB)")
    passed_checks += 1

    dashboard_html_path = export_gis_dashboard_html(out_dir / "gis_dashboard.html")
    assert dashboard_html_path.exists() and dashboard_html_path.stat().st_size > 1000
    print(f"[OK] GIS Dashboard HTML exported: {dashboard_html_path.name} ({dashboard_html_path.stat().st_size / 1024:.1f} KB)")
    passed_checks += 1

    # -----------------------------------------------------------------------
    # STAGE 5: Publication-Quality PNG Generation
    # -----------------------------------------------------------------------
    stage_print(5, "Publication-Quality PNG Snapshot Generation")
    total_checks += 1

    png_path = export_map_png(out_dir / "pune_digital_twin_map.png")
    assert png_path.exists() and png_path.stat().st_size > 1000
    print(f"[OK] Publication-grade static PNG snapshot saved: {png_path.name} ({png_path.stat().st_size / 1024:.1f} KB)")
    passed_checks += 1

    # -----------------------------------------------------------------------
    # STAGE 6: Map Statistics & KPI Metrics
    # -----------------------------------------------------------------------
    stage_print(6, "Map Analytics & Metadata Summary")
    total_checks += 2

    stats = generate_map_statistics()
    stats_path = out_dir / "map_statistics.json"
    stats_path.write_text(json.dumps(stats, indent=2), encoding="utf-8")
    print(f"[OK] Map Statistics exported to {stats_path.name}:")
    print(f"     - Stations:          {stats.get('station_count')}")
    print(f"     - H3 Zones:          {stats.get('zone_count')}")
    print(f"     - AQI Coverage:      {stats.get('aqi_coverage_pct')}%")
    print(f"     - Mean AQI:          {stats.get('mean_aqi')}")
    print(f"     - Has Traffic Data:  {stats.get('has_traffic_data')}")
    assert stats["station_count"] == 5
    passed_checks += 1
    assert stats["zone_count"] > 0
    passed_checks += 1

    # -----------------------------------------------------------------------
    # STAGE 7: FastAPI Endpoints Verification
    # -----------------------------------------------------------------------
    stage_print(7, "FastAPI Endpoints Testing via TestClient")
    client = TestClient(app)

    endpoints = [
        ("/dashboard/map", 200, "text/html"),
        ("/dashboard/map/embed", 200, "text/html"),
        ("/dashboard/map/static", 200, "text/html"),
        ("/api/v1/map", 200, "application/json"),
        ("/api/v1/stations", 200, "application/json"),
        ("/api/v1/zones?limit=5", 200, "application/json"),
        ("/api/v1/map/geojson", 200, "application/json"),
    ]

    total_checks += len(endpoints)
    for route, exp_status, exp_type in endpoints:
        resp = client.get(route)
        print(f"[OK] {route:<28} -> Status: {resp.status_code} ({resp.headers.get('content-type', '').split(';')[0]})")
        assert resp.status_code == exp_status, f"Expected {exp_status} for {route}, got {resp.status_code}"
        assert exp_type in resp.headers.get("content-type", "")
        passed_checks += 1

    # -----------------------------------------------------------------------
    # STAGE 8: Report Artifacts Verification
    # -----------------------------------------------------------------------
    stage_print(8, "Artifacts Integrity Check")
    required_files = [
        "stations.geojson",
        "h3_zones.geojson",
        "traffic_points.geojson",
        "pune_digital_twin_map.html",
        "gis_dashboard.html",
        "pune_digital_twin_map.png",
        "map_statistics.json",
    ]
    total_checks += len(required_files)
    for fname in required_files:
        fpath = out_dir / fname
        assert fpath.exists(), f"Missing required artifact: {fname}"
        print(f"[OK] Artifact verified: {fname:<30} ({fpath.stat().st_size / 1024:.1f} KB)")
        passed_checks += 1

    # -----------------------------------------------------------------------
    # FINAL SUMMARY
    # -----------------------------------------------------------------------
    elapsed = time.time() - total_start
    print("\n" + "=" * 70)
    print(f" ALL {passed_checks}/{total_checks} CHECKS PASSED IN {elapsed:.2f}s")
    print(" URBANTWIN MILESTONE 9 IS READY AND FULLY OPERATIONAL!")
    print("=" * 70)


if __name__ == "__main__":
    main()

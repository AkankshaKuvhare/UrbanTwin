"""GeoJSON export utilities for UrbanTwin GIS module.

Exports AQI stations, H3 zones, and traffic points as valid GeoJSON files
to reports/gis/.  Includes schema validation for exported files.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from config.logging import get_logger
from config.settings import settings

logger = get_logger("urbantwin.gis.geojson_export")

GIS_REPORTS_DIR = Path(settings.BASE_DIR) / "reports" / "gis"
GIS_REPORTS_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clean_value(v: Any) -> Any:
    """Convert numpy scalars and NaN to JSON-serialisable types."""
    if v is None:
        return None
    if isinstance(v, float) and np.isnan(v):
        return None
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.floating,)):
        return float(v) if not np.isnan(v) else None
    if isinstance(v, (np.bool_,)):
        return bool(v)
    return v


def _row_to_properties(row: pd.Series, exclude_cols: Optional[List[str]] = None) -> Dict[str, Any]:
    """Convert a DataFrame row to a GeoJSON properties dict."""
    skip = set(exclude_cols or []) | {"geometry", "geometry_wkt"}
    return {k: _clean_value(v) for k, v in row.items() if k not in skip}


# ---------------------------------------------------------------------------
# Station GeoJSON
# ---------------------------------------------------------------------------

def export_stations_geojson(output_path: Optional[Path] = None) -> Path:
    """Export AQI monitoring stations as GeoJSON FeatureCollection.

    Args:
        output_path: Optional override path.

    Returns:
        Path to the written .geojson file.
    """
    from gis.layers import load_station_layer

    output_path = output_path or GIS_REPORTS_DIR / "stations.geojson"
    stations = load_station_layer()

    features: List[Dict[str, Any]] = []
    for _, row in stations.iterrows():
        lat = _clean_value(row.get("lat"))
        lon = _clean_value(row.get("lon"))
        if lat is None or lon is None:
            continue
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [lon, lat],  # GeoJSON: [lon, lat]
            },
            "properties": _row_to_properties(row, exclude_cols=["lat", "lon"]),
        }
        features.append(feature)

    geojson = {
        "type": "FeatureCollection",
        "features": features,
        "metadata": {
            "source": "UrbanTwin",
            "layer": "aqi_stations",
            "count": len(features),
        },
    }

    output_path = Path(output_path)
    output_path.write_text(json.dumps(geojson, indent=2, default=str), encoding="utf-8")
    logger.info("Exported stations GeoJSON", path=str(output_path), features=len(features))
    return output_path


# ---------------------------------------------------------------------------
# H3 Zones GeoJSON
# ---------------------------------------------------------------------------

def export_h3_zones_geojson(output_path: Optional[Path] = None) -> Path:
    """Export H3 hexagonal zones as GeoJSON FeatureCollection.

    Args:
        output_path: Optional override path.

    Returns:
        Path to the written .geojson file.
    """
    from gis.layers import load_h3_layer

    output_path = output_path or GIS_REPORTS_DIR / "h3_zones.geojson"
    zones = load_h3_layer()

    features: List[Dict[str, Any]] = []

    for _, row in zones.iterrows():
        # Try to get geometry from GeoDataFrame geometry column
        geom = None
        if "geometry" in row.index and row["geometry"] is not None:
            try:
                import shapely.geometry
                geom = shapely.geometry.mapping(row["geometry"])
            except Exception:
                geom = None

        if geom is None:
            # Fallback: build hexagon from H3 cell boundaries
            try:
                import h3
                zone_id = str(row.get("zone_id", ""))
                if zone_id:
                    boundary = h3.cell_to_boundary(zone_id)
                    # h3 returns (lat, lon) pairs; GeoJSON needs [lon, lat]
                    coords = [[lon, lat] for lat, lon in boundary]
                    coords.append(coords[0])  # close the ring
                    geom = {"type": "Polygon", "coordinates": [coords]}
            except Exception:
                # Last resort: point at centroid
                clat = _clean_value(row.get("centroid_lat"))
                clon = _clean_value(row.get("centroid_lon"))
                if clat is not None and clon is not None:
                    geom = {"type": "Point", "coordinates": [clon, clat]}

        if geom is None:
            continue

        props = _row_to_properties(row, exclude_cols=["geometry", "geometry_wkt", "centroid_lat", "centroid_lon"])
        props["centroid_lat"] = _clean_value(row.get("centroid_lat"))
        props["centroid_lon"] = _clean_value(row.get("centroid_lon"))

        feature = {
            "type": "Feature",
            "geometry": geom,
            "properties": props,
        }
        features.append(feature)

    geojson = {
        "type": "FeatureCollection",
        "features": features,
        "metadata": {
            "source": "UrbanTwin",
            "layer": "h3_zones",
            "resolution": settings.H3_RESOLUTION,
            "count": len(features),
        },
    }

    output_path = Path(output_path)
    output_path.write_text(json.dumps(geojson, indent=2, default=str), encoding="utf-8")
    logger.info("Exported H3 zones GeoJSON", path=str(output_path), features=len(features))
    return output_path


# ---------------------------------------------------------------------------
# Traffic GeoJSON
# ---------------------------------------------------------------------------

def export_traffic_geojson(output_path: Optional[Path] = None) -> Path:
    """Export traffic monitoring points as GeoJSON FeatureCollection.

    Returns an empty FeatureCollection if no traffic data is available.

    Args:
        output_path: Optional override path.

    Returns:
        Path to the written .geojson file.
    """
    from gis.layers import load_traffic_layer

    output_path = output_path or GIS_REPORTS_DIR / "traffic_points.geojson"
    traffic = load_traffic_layer()

    features: List[Dict[str, Any]] = []
    if not traffic.empty:
        for _, row in traffic.iterrows():
            lat = _clean_value(row.get("lat") or row.get("latitude"))
            lon = _clean_value(row.get("lon") or row.get("longitude"))
            if lat is None or lon is None:
                continue
            feature = {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [lon, lat]},
                "properties": _row_to_properties(
                    row, exclude_cols=["lat", "lon", "latitude", "longitude"]
                ),
            }
            features.append(feature)

    geojson = {
        "type": "FeatureCollection",
        "features": features,
        "metadata": {
            "source": "UrbanTwin",
            "layer": "traffic_points",
            "count": len(features),
            "has_data": len(features) > 0,
        },
    }

    output_path = Path(output_path)
    output_path.write_text(json.dumps(geojson, indent=2, default=str), encoding="utf-8")
    logger.info("Exported traffic GeoJSON", path=str(output_path), features=len(features))
    return output_path


# ---------------------------------------------------------------------------
# Export all
# ---------------------------------------------------------------------------

def export_all_geojson(output_dir: Optional[Path] = None) -> Dict[str, Path]:
    """Export all GIS layers to GeoJSON files.

    Args:
        output_dir: Directory to write files into (defaults to reports/gis/).

    Returns:
        Dict mapping layer name to output path.
    """
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
    else:
        output_dir = GIS_REPORTS_DIR

    results: Dict[str, Path] = {}

    results["stations"] = export_stations_geojson(output_dir / "stations.geojson")
    results["h3_zones"] = export_h3_zones_geojson(output_dir / "h3_zones.geojson")
    results["traffic"] = export_traffic_geojson(output_dir / "traffic_points.geojson")

    logger.info("Exported all GeoJSON layers", count=len(results))
    return results


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_geojson(path: Path) -> Dict[str, Any]:
    """Validate a GeoJSON file for schema compliance.

    Args:
        path: Path to the .geojson file.

    Returns:
        Dict with keys: valid (bool), errors (list[str]), feature_count (int).
    """
    path = Path(path)
    errors: List[str] = []

    if not path.exists():
        return {"valid": False, "errors": [f"File not found: {path}"], "feature_count": 0}

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {"valid": False, "errors": [f"JSON parse error: {exc}"], "feature_count": 0}

    # Top-level type check
    if data.get("type") != "FeatureCollection":
        errors.append("Root type must be 'FeatureCollection'")

    features = data.get("features", [])
    if not isinstance(features, list):
        errors.append("'features' must be an array")
        return {"valid": False, "errors": errors, "feature_count": 0}

    valid_geom_types = {"Point", "MultiPoint", "LineString", "MultiLineString", "Polygon", "MultiPolygon", "GeometryCollection"}

    for i, feature in enumerate(features):
        if feature.get("type") != "Feature":
            errors.append(f"Feature {i}: type must be 'Feature'")
        geom = feature.get("geometry")
        if geom is None:
            errors.append(f"Feature {i}: null geometry")
            continue
        if geom.get("type") not in valid_geom_types:
            errors.append(f"Feature {i}: invalid geometry type '{geom.get('type')}'")
        if "coordinates" not in geom:
            errors.append(f"Feature {i}: geometry missing 'coordinates'")

    is_valid = len(errors) == 0
    return {"valid": is_valid, "errors": errors, "feature_count": len(features)}

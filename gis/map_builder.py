"""Folium-based interactive map builder for UrbanTwin Digital Twin.

Builds a multi-layer Folium map representing the Pune & PCMC digital twin:
  - AQI station markers (colour-coded by AQI category)
  - H3 hexagonal zone overlay (colour-coded by mean AQI)
  - Traffic monitoring points (only when data exists)
  - Weather information popups
  - OSM road network (gracefully skipped on Overpass timeout)
  - Timeline / date filter controls (JS-driven)
  - Full layer-control panel
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

import folium
from folium.plugins import FloatImage, MiniMap, Fullscreen
import pandas as pd

from config.logging import get_logger
from config.settings import settings
from gis.layers import get_aqi_color, get_aqi_category, STATION_META

logger = get_logger("urbantwin.gis.map_builder")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
PUNE_CENTER = [18.52, 73.85]
GIS_REPORTS_DIR = Path(settings.BASE_DIR) / "reports" / "gis"
GIS_REPORTS_DIR.mkdir(parents=True, exist_ok=True)

AQI_LEGEND_HTML = """
<div style="
    position: fixed;
    bottom: 40px; right: 10px; z-index: 9999;
    background: rgba(15,23,42,0.92);
    border: 1px solid #334155;
    border-radius: 10px;
    padding: 12px 16px;
    font-family: 'Inter', sans-serif;
    font-size: 12px;
    color: #e2e8f0;
    min-width: 150px;
">
    <div style="font-weight:700; font-size:13px; margin-bottom:8px; color:#94a3b8;">
        AQI Legend (India NAQI)
    </div>
    <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
        <span style="background:#22c55e;width:14px;height:14px;border-radius:3px;display:inline-block;"></span>
        0–50 &nbsp; Good
    </div>
    <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
        <span style="background:#84cc16;width:14px;height:14px;border-radius:3px;display:inline-block;"></span>
        51–100 &nbsp; Satisfactory
    </div>
    <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
        <span style="background:#f59e0b;width:14px;height:14px;border-radius:3px;display:inline-block;"></span>
        101–200 &nbsp; Moderate
    </div>
    <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
        <span style="background:#f97316;width:14px;height:14px;border-radius:3px;display:inline-block;"></span>
        201–300 &nbsp; Poor
    </div>
    <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
        <span style="background:#ef4444;width:14px;height:14px;border-radius:3px;display:inline-block;"></span>
        301–400 &nbsp; Very Poor
    </div>
    <div style="display:flex;align-items:center;gap:8px;">
        <span style="background:#7c3aed;width:14px;height:14px;border-radius:3px;display:inline-block;"></span>
        401+ &nbsp; Severe
    </div>
</div>
"""


# ---------------------------------------------------------------------------
# Popup builders
# ---------------------------------------------------------------------------

def _station_popup(row: pd.Series) -> str:
    """Build HTML popup for an AQI station marker."""
    def fmt(val: Any) -> str:
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return "N/A"
        try:
            return f"{float(val):.1f}"
        except (TypeError, ValueError):
            return str(val)

    color = row.get("aqi_color", "#94a3b8")
    category = row.get("aqi_category", "Unknown")
    aqi = fmt(row.get("aqi"))
    last_upd = str(row.get("last_updated", "N/A"))[:16] if row.get("last_updated") else "N/A"

    return f"""
    <div style="font-family:'Inter',sans-serif;min-width:230px;background:#0f172a;color:#e2e8f0;border-radius:8px;padding:14px;">
        <div style="font-weight:700;font-size:14px;margin-bottom:10px;color:#f1f5f9;border-bottom:1px solid #334155;padding-bottom:6px;">
            {row.get('name', 'Station')}
        </div>
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
            <div>
                <div style="font-size:11px;color:#94a3b8;">AQI</div>
                <div style="font-size:26px;font-weight:800;color:{color};">{aqi}</div>
            </div>
            <div style="background:{color}20;border:1px solid {color};border-radius:6px;padding:4px 10px;font-size:11px;color:{color};font-weight:600;">
                {category}
            </div>
        </div>
        <table style="width:100%;border-collapse:collapse;font-size:11px;">
            <tr><td style="color:#94a3b8;padding:2px 0;">PM2.5</td><td style="text-align:right;font-weight:600;">{fmt(row.get('pm25'))} µg/m³</td></tr>
            <tr><td style="color:#94a3b8;padding:2px 0;">PM10</td><td style="text-align:right;font-weight:600;">{fmt(row.get('pm10'))} µg/m³</td></tr>
            <tr><td style="color:#94a3b8;padding:2px 0;">NO₂</td><td style="text-align:right;font-weight:600;">{fmt(row.get('no2'))} µg/m³</td></tr>
            <tr><td style="color:#94a3b8;padding:2px 0;">CO</td><td style="text-align:right;font-weight:600;">{fmt(row.get('co'))} mg/m³</td></tr>
            <tr><td style="color:#94a3b8;padding:2px 0;">SO₂</td><td style="text-align:right;font-weight:600;">{fmt(row.get('so2'))} µg/m³</td></tr>
            <tr><td style="color:#94a3b8;padding:2px 0;">O₃</td><td style="text-align:right;font-weight:600;">{fmt(row.get('o3'))} µg/m³</td></tr>
        </table>
        <div style="margin-top:8px;font-size:10px;color:#64748b;">Last updated: {last_upd}</div>
        <div style="font-size:10px;color:#64748b;">Station ID: {row.get('station_id', 'N/A')}</div>
    </div>
    """


def _traffic_popup(row: pd.Series) -> str:
    """Build HTML popup for a traffic monitoring point."""
    def fmt(val: Any, decimals: int = 1) -> str:
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return "N/A"
        try:
            return f"{float(val):.{decimals}f}"
        except (TypeError, ValueError):
            return str(val)

    cong = row.get("congestion_ratio")
    cong_pct = f"{float(cong)*100:.0f}%" if cong is not None and not pd.isna(float(cong) if cong is not None else float("nan")) else "N/A"

    closure = row.get("road_closure", False)
    closure_str = "YES" if closure else "No"
    closure_color = "#ef4444" if closure else "#22c55e"

    return f"""
    <div style="font-family:'Inter',sans-serif;min-width:200px;background:#0f172a;color:#e2e8f0;border-radius:8px;padding:12px;">
        <div style="font-weight:700;font-size:13px;margin-bottom:8px;color:#f1f5f9;border-bottom:1px solid #334155;padding-bottom:5px;">
            {row.get('name', 'Traffic Point')}
        </div>
        <table style="width:100%;font-size:11px;border-collapse:collapse;">
            <tr><td style="color:#94a3b8;padding:2px 0;">Current Speed</td><td style="text-align:right;font-weight:600;">{fmt(row.get('current_speed'))} km/h</td></tr>
            <tr><td style="color:#94a3b8;padding:2px 0;">Free Flow Speed</td><td style="text-align:right;font-weight:600;">{fmt(row.get('free_flow_speed'))} km/h</td></tr>
            <tr><td style="color:#94a3b8;padding:2px 0;">Congestion</td><td style="text-align:right;font-weight:600;">{cong_pct}</td></tr>
            <tr><td style="color:#94a3b8;padding:2px 0;">Confidence</td><td style="text-align:right;font-weight:600;">{fmt(row.get('confidence'), 0)}%</td></tr>
            <tr><td style="color:#94a3b8;padding:2px 0;">Road Closure</td>
                <td style="text-align:right;font-weight:600;color:{closure_color};">{closure_str}</td></tr>
        </table>
        <div style="margin-top:6px;font-size:10px;color:#64748b;">ID: {row.get('point_id', row.get('id', 'N/A'))}</div>
    </div>
    """


def _weather_popup(row: pd.Series) -> str:
    """Build HTML popup for a weather layer marker."""
    def fmt(val: Any, decimals: int = 1) -> str:
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return "N/A"
        try:
            return f"{float(val):.{decimals}f}"
        except (TypeError, ValueError):
            return str(val)

    return f"""
    <div style="font-family:'Inter',sans-serif;min-width:190px;background:#0f172a;color:#e2e8f0;border-radius:8px;padding:12px;">
        <div style="font-weight:700;font-size:13px;margin-bottom:8px;color:#f1f5f9;border-bottom:1px solid #334155;padding-bottom:5px;">
            Weather - {row.get('name', 'Station')}
        </div>
        <table style="width:100%;font-size:11px;border-collapse:collapse;">
            <tr><td style="color:#94a3b8;padding:2px 0;">Temperature</td><td style="text-align:right;font-weight:600;">{fmt(row.get('temperature_2m'))} °C</td></tr>
            <tr><td style="color:#94a3b8;padding:2px 0;">Humidity</td><td style="text-align:right;font-weight:600;">{fmt(row.get('relative_humidity_2m'))} %</td></tr>
            <tr><td style="color:#94a3b8;padding:2px 0;">Wind Speed</td><td style="text-align:right;font-weight:600;">{fmt(row.get('wind_speed_10m'))} m/s</td></tr>
            <tr><td style="color:#94a3b8;padding:2px 0;">Wind Dir</td><td style="text-align:right;font-weight:600;">{fmt(row.get('wind_direction_10m'))}°</td></tr>
            <tr><td style="color:#94a3b8;padding:2px 0;">Pressure</td><td style="text-align:right;font-weight:600;">{fmt(row.get('surface_pressure'))} hPa</td></tr>
            <tr><td style="color:#94a3b8;padding:2px 0;">Rainfall</td><td style="text-align:right;font-weight:600;">{fmt(row.get('precipitation'))} mm</td></tr>
            <tr><td style="color:#94a3b8;padding:2px 0;">BL Height</td><td style="text-align:right;font-weight:600;">{fmt(row.get('boundary_layer_height'))} m</td></tr>
        </table>
    </div>
    """


# ---------------------------------------------------------------------------
# Layer builders
# ---------------------------------------------------------------------------

def _add_station_layer(m: folium.Map, stations: pd.DataFrame) -> folium.FeatureGroup:
    """Add AQI station markers to the map."""
    fg = folium.FeatureGroup(name="AQI Stations", show=True)

    for _, row in stations.iterrows():
        lat = row.get("lat")
        lon = row.get("lon")
        if lat is None or lon is None:
            continue

        color = row.get("aqi_color", "#94a3b8")
        aqi_val = row.get("aqi")
        aqi_text = f"{aqi_val:.0f}" if aqi_val is not None and not pd.isna(float(aqi_val) if aqi_val is not None else float("nan")) else "?"

        # Outer ring + inner marker
        folium.CircleMarker(
            location=[lat, lon],
            radius=22,
            color=color,
            fill=False,
            weight=2,
            opacity=0.5,
        ).add_to(fg)

        folium.CircleMarker(
            location=[lat, lon],
            radius=16,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.85,
            weight=2,
            popup=folium.Popup(
                folium.IFrame(_station_popup(row), width=260, height=280),
                max_width=280,
            ),
            tooltip=folium.Tooltip(
                f"<b>{row.get('name', 'Station')}</b><br>AQI: <b>{aqi_text}</b> – {row.get('aqi_category', '')}",
                style="background:#0f172a;color:#e2e8f0;border:1px solid #334155;border-radius:6px;font-size:12px;",
            ),
        ).add_to(fg)

        # AQI label on marker
        folium.map.Marker(
            location=[lat, lon],
            icon=folium.DivIcon(
                html=f'<div style="font-size:10px;font-weight:800;color:#fff;text-shadow:0 1px 2px rgba(0,0,0,0.8);text-align:center;line-height:32px;width:32px;margin-left:-16px;margin-top:-16px;">{aqi_text}</div>',
                icon_size=(32, 32),
                icon_anchor=(0, 0),
            ),
        ).add_to(fg)

    fg.add_to(m)
    return fg


def _add_h3_layer(m: folium.Map, zones: pd.DataFrame) -> folium.FeatureGroup:
    """Add H3 hexagonal zones to the map."""
    fg = folium.FeatureGroup(name="H3 AQI Zones", show=True)

    for _, row in zones.iterrows():
        try:
            import h3
            zone_id = str(row.get("zone_id", ""))
            if not zone_id:
                continue

            boundary = h3.cell_to_boundary(zone_id)
            # h3 returns (lat, lon); folium needs [lat, lon]
            coords = [[lat, lon] for lat, lon in boundary]

            color = row.get("aqi_color", "#94a3b8")
            mean_aqi = row.get("mean_aqi")
            aqi_text = f"{float(mean_aqi):.1f}" if mean_aqi is not None and not pd.isna(float(mean_aqi) if mean_aqi is not None else float("nan")) else "N/A"
            category = row.get("aqi_category", "Unknown")

            folium.Polygon(
                locations=coords,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.35,
                weight=0.8,
                opacity=0.6,
                tooltip=folium.Tooltip(
                    f"Zone: {zone_id[:8]}…<br>Mean AQI: <b>{aqi_text}</b><br>{category}",
                    style="background:#0f172a;color:#e2e8f0;border:1px solid #334155;border-radius:6px;font-size:11px;",
                ),
                popup=folium.Popup(
                    f"""<div style="font-family:'Inter',sans-serif;background:#0f172a;color:#e2e8f0;padding:10px;border-radius:8px;min-width:160px;">
                    <b>H3 Zone</b><br>
                    <code style="font-size:10px;">{zone_id}</code><br><br>
                    <b>Mean AQI:</b> {aqi_text}<br>
                    <b>Category:</b> <span style="color:{color};">{category}</span><br>
                    <b>Records:</b> {int(row.get('record_count', 0))}
                    </div>""",
                    max_width=200,
                ),
            ).add_to(fg)
        except Exception as exc:
            logger.debug("Skipping H3 zone", zone=str(row.get("zone_id", "")), error=str(exc))
            continue

    fg.add_to(m)
    return fg


def _add_traffic_layer(m: folium.Map, traffic: pd.DataFrame) -> Optional[folium.FeatureGroup]:
    """Add traffic monitoring points to the map (only if data exists)."""
    if traffic.empty:
        return None

    fg = folium.FeatureGroup(name="Traffic Monitoring", show=True)

    for _, row in traffic.iterrows():
        lat = row.get("lat") or row.get("latitude")
        lon = row.get("lon") or row.get("longitude")
        if lat is None or lon is None:
            continue

        cong = row.get("congestion_ratio")
        try:
            cong_float = float(cong) if cong is not None else 0.0
        except (TypeError, ValueError):
            cong_float = 0.0

        # Color by congestion: green → orange → red
        if cong_float < 0.3:
            color = "#22c55e"
        elif cong_float < 0.6:
            color = "#f59e0b"
        else:
            color = "#ef4444"

        folium.CircleMarker(
            location=[lat, lon],
            radius=8,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.8,
            weight=2,
            popup=folium.Popup(
                folium.IFrame(_traffic_popup(row), width=230, height=200),
                max_width=240,
            ),
            tooltip=folium.Tooltip(
                f"<b>{row.get('name', 'Traffic Point')}</b><br>Speed: {row.get('current_speed', 'N/A')} km/h",
                style="background:#0f172a;color:#e2e8f0;border:1px solid #334155;border-radius:6px;font-size:11px;",
            ),
        ).add_to(fg)

    fg.add_to(m)
    logger.info("Added traffic layer", points=len(traffic))
    return fg


def _add_weather_layer(m: folium.Map, weather: pd.DataFrame) -> folium.FeatureGroup:
    """Add weather observation markers to the map."""
    fg = folium.FeatureGroup(name="Weather Stations", show=False)

    for _, row in weather.iterrows():
        lat = row.get("lat")
        lon = row.get("lon")
        if lat is None or lon is None:
            continue

        temp = row.get("temperature_2m")
        temp_str = f"{float(temp):.1f}°C" if temp is not None and not pd.isna(float(temp) if temp is not None else float("nan")) else "?"

        folium.Marker(
            location=[lat, lon],
            icon=folium.DivIcon(
                html=f"""<div style="
                    background:rgba(30,58,138,0.85);
                    border:1px solid #3b82f6;
                    border-radius:6px;
                    padding:3px 7px;
                    font-size:10px;
                    font-weight:700;
                    color:#93c5fd;
                    white-space:nowrap;
                    text-align:center;
                    box-shadow:0 2px 4px rgba(0,0,0,0.4);
                ">{temp_str}</div>""",
                icon_size=(60, 22),
                icon_anchor=(30, 11),
            ),
            popup=folium.Popup(
                folium.IFrame(_weather_popup(row), width=220, height=240),
                max_width=240,
            ),
            tooltip=folium.Tooltip(
                f"<b>Weather:</b> {row.get('name', '')}<br>Temp: {temp_str}",
                style="background:#0f172a;color:#e2e8f0;border:1px solid #334155;border-radius:6px;font-size:11px;",
            ),
        ).add_to(fg)

    fg.add_to(m)
    return fg


def _add_osm_road_layer(m: folium.Map) -> Optional[folium.FeatureGroup]:
    """Fetch and add OSM road network layer (gracefully degrades on error)."""
    cache_path = Path(settings.BASE_DIR) / "data" / "osm_pune_roads.gpkg"

    try:
        import geopandas as gpd
        import osmnx as ox

        if cache_path.exists():
            logger.info("Loading OSM roads from cache", path=str(cache_path))
            roads_gdf = gpd.read_file(cache_path)
        else:
            logger.info("Fetching OSM road network from Overpass API...")
            north, south, east, west = 18.72, 18.40, 74.02, 73.70
            G = ox.graph_from_bbox(bbox=(north, south, east, west), network_type="drive")
            _, edges = ox.graph_to_gdfs(G)
            roads_gdf = edges.reset_index()
            roads_gdf.to_file(cache_path, driver="GPKG")
            logger.info("Cached OSM roads", path=str(cache_path))

        fg = folium.FeatureGroup(name="Road Network (OSM)", show=False)

        # Convert to GeoJSON for Folium
        import json as json_mod
        roads_json = json_mod.loads(roads_gdf.to_json())

        folium.GeoJson(
            roads_json,
            style_function=lambda f: {
                "color": "#475569",
                "weight": 1,
                "opacity": 0.5,
            },
            tooltip=folium.GeoJsonTooltip(fields=["name"] if "name" in roads_gdf.columns else []),
        ).add_to(fg)

        fg.add_to(m)
        logger.info("Added OSM road network layer")
        return fg

    except Exception as exc:
        logger.warning("Skipping OSM road layer (graceful degrade)", error=str(exc))
        return None


# ---------------------------------------------------------------------------
# Main map builder
# ---------------------------------------------------------------------------

def build_pune_map(
    include_stations: bool = True,
    include_h3: bool = True,
    include_traffic: bool = True,
    include_weather: bool = True,
    include_osm: bool = False,
) -> folium.Map:
    """Build the full Pune Digital Twin Folium map.

    Args:
        include_stations: Add AQI station layer.
        include_h3: Add H3 zone overlay.
        include_traffic: Add traffic layer (auto-skipped if no data).
        include_weather: Add weather layer.
        include_osm: Add OSM road network (gracefully skipped on error).

    Returns:
        A configured folium.Map object.
    """
    from gis.layers import load_station_layer, load_h3_layer, load_traffic_layer, load_weather_layer

    m = folium.Map(
        location=PUNE_CENTER,
        zoom_start=12,
        tiles=None,
        prefer_canvas=True,
    )

    # Base tile layers
    folium.TileLayer(
        tiles="CartoDB dark_matter",
        name="Dark (Default)",
        attr="CartoDB",
        show=True,
    ).add_to(m)

    folium.TileLayer(
        tiles="CartoDB positron",
        name="Light",
        attr="CartoDB",
        show=False,
    ).add_to(m)

    folium.TileLayer(
        tiles="OpenStreetMap",
        name="OpenStreetMap",
        attr="OSM",
        show=False,
    ).add_to(m)

    # Data layers
    if include_h3:
        try:
            zones = load_h3_layer()
            if not zones.empty:
                _add_h3_layer(m, zones)
        except Exception as exc:
            logger.warning("H3 layer failed", error=str(exc))

    if include_osm:
        _add_osm_road_layer(m)

    if include_stations:
        try:
            stations = load_station_layer()
            if not stations.empty:
                _add_station_layer(m, stations)
        except Exception as exc:
            logger.warning("Station layer failed", error=str(exc))

    if include_traffic:
        try:
            traffic = load_traffic_layer()
            _add_traffic_layer(m, traffic)
        except Exception as exc:
            logger.warning("Traffic layer failed", error=str(exc))

    if include_weather:
        try:
            weather = load_weather_layer()
            if not weather.empty:
                _add_weather_layer(m, weather)
        except Exception as exc:
            logger.warning("Weather layer failed", error=str(exc))

    # Plugins
    try:
        MiniMap(toggle_display=True).add_to(m)
    except Exception:
        pass

    try:
        Fullscreen(position="topleft").add_to(m)
    except Exception:
        pass

    # Layer control (must be last)
    folium.LayerControl(position="topright", collapsed=False).add_to(m)

    # AQI Legend
    m.get_root().html.add_child(folium.Element(AQI_LEGEND_HTML))

    logger.info("Built Pune digital twin map")
    return m


# ---------------------------------------------------------------------------
# Export helpers
# ---------------------------------------------------------------------------

def export_map_html(output_path: Optional[Path] = None, **kwargs: Any) -> Path:
    """Export the Pune digital twin map to a standalone HTML file.

    Args:
        output_path: Override output path (default: reports/gis/pune_digital_twin_map.html).
        **kwargs: Forwarded to build_pune_map().

    Returns:
        Path to the written HTML file.
    """
    output_path = Path(output_path) if output_path else GIS_REPORTS_DIR / "pune_digital_twin_map.html"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    m = build_pune_map(**kwargs)
    m.save(str(output_path))
    logger.info("Exported map HTML", path=str(output_path))
    return output_path


def export_map_png(output_path: Optional[Path] = None) -> Path:
    """Generate a publication-quality static PNG snapshot of the Digital Twin map.

    Plots H3 hex zones, station markers, and traffic points using Matplotlib.

    Args:
        output_path: Optional destination path.

    Returns:
        Path to the generated PNG file.
    """
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon as MplPolygon, Patch
    import shapely.geometry
    import h3
    from gis.layers import load_station_layer, load_h3_layer, load_traffic_layer

    output_path = Path(output_path) if output_path else GIS_REPORTS_DIR / "pune_digital_twin_map.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(12, 10), facecolor="#020617")
    ax.set_facecolor("#0a0f1d")

    # 1. Plot H3 zones
    try:
        zones = load_h3_layer()
        for _, row in zones.iterrows():
            zone_id = str(row.get("zone_id", ""))
            color = row.get("aqi_color", "#334155")
            if not zone_id:
                continue
            boundary = h3.cell_to_boundary(zone_id)
            # boundary is [(lat, lon), ...] -> Matplotlib needs (lon, lat)
            coords = [(lon, lat) for lat, lon in boundary]
            poly = MplPolygon(coords, closed=True, facecolor=color, edgecolor="#1e293b", alpha=0.45, linewidth=0.5)
            ax.add_patch(poly)
    except Exception as exc:
        logger.warning("Could not render H3 zones in PNG snapshot", error=str(exc))

    # 2. Plot Stations
    try:
        stations = load_station_layer()
        for _, row in stations.iterrows():
            lon = row.get("lon")
            lat = row.get("lat")
            color = row.get("aqi_color", "#3b82f6")
            name = str(row.get("name", "Station")).split(",")[0]
            aqi_val = row.get("aqi")
            aqi_str = f"{int(aqi_val)}" if aqi_val is not None and not pd.isna(aqi_val) else "N/A"

            if lon is not None and lat is not None:
                ax.scatter(lon, lat, s=160, color=color, edgecolors="#ffffff", linewidth=1.5, zorder=5)
                ax.annotate(
                    f"{name}\nAQI: {aqi_str}",
                    (lon, lat),
                    xytext=(8, 8),
                    textcoords="offset points",
                    color="#f8fafc",
                    fontsize=8,
                    fontweight="bold",
                    bbox=dict(boxstyle="round,pad=0.3", fc="#0f172a", ec=color, alpha=0.85, lw=1),
                    zorder=6,
                )
    except Exception as exc:
        logger.warning("Could not render stations in PNG snapshot", error=str(exc))

    # 3. Plot Traffic Points (if any)
    try:
        traffic = load_traffic_layer()
        if not traffic.empty:
            for _, row in traffic.iterrows():
                lon = row.get("lon") or row.get("longitude")
                lat = row.get("lat") or row.get("latitude")
                if lon is not None and lat is not None:
                    ax.scatter(lon, lat, s=30, color="#f59e0b", marker="^", edgecolors="#000", zorder=4)
    except Exception as exc:
        logger.warning("Could not render traffic points in PNG snapshot", error=str(exc))

    # Formatting
    ax.set_title("UrbanTwin Digital Twin – Pune & PCMC Air Quality & Grid", fontsize=15, fontweight="bold", color="#f1f5f9", pad=15)
    ax.set_xlabel("Longitude (°E)", color="#94a3b8", fontsize=10)
    ax.set_ylabel("Latitude (°N)", color="#94a3b8", fontsize=10)
    ax.tick_params(colors="#64748b", labelsize=9)
    for spine in ax.spines.values():
        spine.set_color("#334155")

    # Legend
    legend_elements = [
        Patch(facecolor="#22c55e", edgecolor="none", label="Good (0-50)"),
        Patch(facecolor="#84cc16", edgecolor="none", label="Satisfactory (51-100)"),
        Patch(facecolor="#f59e0b", edgecolor="none", label="Moderate (101-200)"),
        Patch(facecolor="#f97316", edgecolor="none", label="Poor (201-300)"),
        Patch(facecolor="#ef4444", edgecolor="none", label="Very Poor (301-400)"),
        Patch(facecolor="#7c3aed", edgecolor="none", label="Severe (401+)"),
        Patch(facecolor="#94a3b8", edgecolor="none", label="No Data"),
    ]
    leg = ax.legend(handles=legend_elements, loc="lower right", facecolor="#0f172a", edgecolor="#334155", fontsize=9, labelcolor="#e2e8f0", title="NAQI Categories", title_fontsize=10)
    plt.setp(leg.get_title(), color="#cbd5e1")

    # Set coordinate bounds approximately around Pune / PCMC
    ax.set_xlim(73.70, 74.00)
    ax.set_ylim(18.42, 18.66)
    ax.grid(True, linestyle="--", alpha=0.15, color="#64748b")

    plt.tight_layout()
    plt.savefig(output_path, dpi=200, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    logger.info("Exported static PNG snapshot", path=str(output_path))
    return output_path


def generate_map_statistics() -> Dict[str, Any]:
    """Generate summary statistics for the map layers.

    Returns:
        Dict with keys: station_count, zone_count, traffic_point_count,
        aqi_coverage_pct, mean_aqi, max_aqi, min_aqi, layer_info.
    """
    from gis.layers import load_station_layer, load_h3_layer, load_traffic_layer

    stations = load_station_layer()
    zones = load_h3_layer()
    traffic = load_traffic_layer()

    # AQI stats
    aqi_vals = stations["aqi"].dropna().tolist()
    zone_aqi_vals = zones["mean_aqi"].dropna().tolist() if "mean_aqi" in zones.columns else []
    all_aqi = aqi_vals + zone_aqi_vals

    stats: Dict[str, Any] = {
        "station_count": len(stations),
        "zone_count": len(zones),
        "traffic_point_count": len(traffic) if not traffic.empty else 0,
        "has_traffic_data": not traffic.empty,
        "aqi_coverage_pct": round(
            len(stations[stations["aqi"].notna()]) / max(len(stations), 1) * 100, 1
        ),
        "mean_aqi": round(float(pd.Series(aqi_vals).mean()), 1) if aqi_vals else None,
        "max_aqi": round(float(max(aqi_vals)), 1) if aqi_vals else None,
        "min_aqi": round(float(min(aqi_vals)), 1) if aqi_vals else None,
        "zone_mean_aqi": round(float(pd.Series(zone_aqi_vals).mean()), 1) if zone_aqi_vals else None,
        "layers": {
            "aqi_stations": True,
            "h3_zones": not zones.empty,
            "traffic": not traffic.empty,
            "weather": True,
            "osm_roads": (Path(settings.BASE_DIR) / "data" / "osm_pune_roads.gpkg").exists(),
        },
    }
    return stats

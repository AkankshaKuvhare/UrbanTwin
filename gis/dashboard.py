"""GIS Dashboard & API for UrbanTwin.

Provides:
  - GET /dashboard/map          – Full-screen interactive GIS dashboard (HTML)
  - GET /api/v1/map             – Map metadata & statistics (JSON)
  - GET /api/v1/zones           – H3 zones with AQI data (JSON)
  - GET /api/v1/stations        – AQI station readings (JSON)
  - GET /api/v1/map/geojson     – Trigger GeoJSON export for all layers
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse

from config.logging import get_logger
from config.settings import settings

logger = get_logger("urbantwin.gis.dashboard")

GIS_REPORTS_DIR = Path(settings.BASE_DIR) / "reports" / "gis"
GIS_REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
router = APIRouter(prefix="/dashboard", tags=["gis_dashboard"])
api_router = APIRouter(prefix="/api/v1", tags=["gis_api"])


# ---------------------------------------------------------------------------
# Dashboard HTML builder
# ---------------------------------------------------------------------------

def build_gis_dashboard_html() -> str:
    """Build the full-screen GIS dashboard HTML page."""
    from gis.map_builder import generate_map_statistics

    try:
        stats = generate_map_statistics()
    except Exception as exc:
        logger.warning("Stats generation failed", error=str(exc))
        stats = {
            "station_count": 5,
            "zone_count": 251,
            "traffic_point_count": 0,
            "has_traffic_data": False,
            "aqi_coverage_pct": 0,
            "mean_aqi": None,
            "max_aqi": None,
            "min_aqi": None,
        }

    mean_aqi = stats.get("mean_aqi", "N/A")
    max_aqi = stats.get("max_aqi", "N/A")
    min_aqi = stats.get("min_aqi", "N/A")
    station_count = stats.get("station_count", 5)
    zone_count = stats.get("zone_count", 251)
    traffic_count = stats.get("traffic_point_count", 0)
    coverage = stats.get("aqi_coverage_pct", 0)
    has_traffic = stats.get("has_traffic_data", False)

    mean_aqi_str = f"{mean_aqi}" if mean_aqi is not None else "N/A"
    max_aqi_str = f"{max_aqi}" if max_aqi is not None else "N/A"
    min_aqi_str = f"{min_aqi}" if min_aqi is not None else "N/A"

    traffic_badge = (
        '<span style="background:#22c55e20;color:#22c55e;border:1px solid #22c55e;border-radius:4px;padding:2px 8px;font-size:10px;">LIVE</span>'
        if has_traffic
        else '<span style="background:#64748b20;color:#64748b;border:1px solid #64748b;border-radius:4px;padding:2px 8px;font-size:10px;">NO DATA</span>'
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>UrbanTwin – GIS Digital Twin Map | Pune & PCMC</title>
<script src="https://cdn.tailwindcss.com"></script>
<link rel="preconnect" href="https://fonts.googleapis.com"/>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet"/>
<style>
  * {{ font-family: 'Inter', sans-serif; box-sizing: border-box; }}
  body {{ background: #020617; color: #e2e8f0; margin: 0; padding: 0; overflow: hidden; height: 100vh; }}
  .sidebar {{ background: #0f172a; border-right: 1px solid #1e293b; height: 100vh; overflow-y: auto; }}
  .kpi-card {{ background: linear-gradient(135deg, #0f172a, #1e293b); border: 1px solid #334155; border-radius: 12px; padding: 14px 16px; transition: border-color 0.2s; }}
  .kpi-card:hover {{ border-color: #475569; }}
  .layer-toggle {{ background: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 8px 12px; cursor: pointer; transition: all 0.2s; display: flex; align-items: center; gap: 8px; margin-bottom: 6px; width: 100%; text-align: left; }}
  .layer-toggle.active {{ border-color: #3b82f6; background: #1e3a5f; }}
  .layer-toggle:hover {{ border-color: #475569; }}
  .dot {{ width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }}
  iframe {{ border: none; width: 100%; height: 100%; }}
  ::-webkit-scrollbar {{ width: 5px; }} ::-webkit-scrollbar-track {{ background: #0f172a; }} ::-webkit-scrollbar-thumb {{ background: #334155; border-radius: 3px; }}
  .section-title {{ font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.1em; color: #64748b; margin-bottom: 10px; margin-top: 16px; }}
  .badge {{ display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 10px; font-weight: 600; }}
  .aqi-good {{ background: #22c55e20; color: #22c55e; border: 1px solid #22c55e40; }}
  .aqi-moderate {{ background: #f59e0b20; color: #f59e0b; border: 1px solid #f59e0b40; }}
  .aqi-poor {{ background: #ef444420; color: #ef4444; border: 1px solid #ef444440; }}
</style>
</head>
<body>
<div style="display:flex;height:100vh;width:100vw;">

  <!-- Sidebar -->
  <div class="sidebar" style="width:300px;min-width:300px;padding:16px;display:flex;flex-direction:column;gap:10px;">

    <!-- Header -->
    <div style="padding-bottom:12px;border-bottom:1px solid #1e293b;">
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:4px;">
        <div style="width:32px;height:32px;background:linear-gradient(135deg,#3b82f6,#8b5cf6);border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:16px;">🗺️</div>
        <div>
          <div style="font-size:16px;font-weight:800;color:#f1f5f9;">UrbanTwin</div>
          <div style="font-size:10px;color:#64748b;">GIS Digital Twin – Pune & PCMC</div>
        </div>
      </div>
    </div>

    <!-- KPI Cards -->
    <div class="section-title">Overview</div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">
      <div class="kpi-card">
        <div style="font-size:20px;font-weight:800;color:#3b82f6;">{station_count}</div>
        <div style="font-size:10px;color:#64748b;margin-top:2px;">Stations</div>
      </div>
      <div class="kpi-card">
        <div style="font-size:20px;font-weight:800;color:#8b5cf6;">{zone_count}</div>
        <div style="font-size:10px;color:#64748b;margin-top:2px;">H3 Zones</div>
      </div>
      <div class="kpi-card">
        <div style="font-size:20px;font-weight:800;color:#f59e0b;">{mean_aqi_str}</div>
        <div style="font-size:10px;color:#64748b;margin-top:2px;">Mean AQI</div>
      </div>
      <div class="kpi-card">
        <div style="font-size:20px;font-weight:800;color:#22c55e;">{coverage}%</div>
        <div style="font-size:10px;color:#64748b;margin-top:2px;">Coverage</div>
      </div>
    </div>

    <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">
      <div class="kpi-card" style="border-left:3px solid #22c55e;">
        <div style="font-size:14px;font-weight:700;color:#22c55e;">{min_aqi_str}</div>
        <div style="font-size:10px;color:#64748b;">Min AQI</div>
      </div>
      <div class="kpi-card" style="border-left:3px solid #ef4444;">
        <div style="font-size:14px;font-weight:700;color:#ef4444;">{max_aqi_str}</div>
        <div style="font-size:10px;color:#64748b;">Max AQI</div>
      </div>
    </div>

    <!-- Layer Controls -->
    <div class="section-title">Map Layers</div>
    <button class="layer-toggle active" onclick="toggleLayer(this,'aqi-stations')">
      <span class="dot" style="background:#3b82f6;"></span>
      <span style="font-size:12px;font-weight:500;flex:1;">AQI Stations</span>
      <span style="font-size:10px;color:#3b82f6;">{station_count}</span>
    </button>
    <button class="layer-toggle active" onclick="toggleLayer(this,'h3-zones')">
      <span class="dot" style="background:#8b5cf6;"></span>
      <span style="font-size:12px;font-weight:500;flex:1;">H3 AQI Zones</span>
      <span style="font-size:10px;color:#8b5cf6;">{zone_count}</span>
    </button>
    <button class="layer-toggle {'active' if has_traffic else ''}" onclick="toggleLayer(this,'traffic')">
      <span class="dot" style="background:#f59e0b;"></span>
      <span style="font-size:12px;font-weight:500;flex:1;">Traffic</span>
      {traffic_badge}
    </button>
    <button class="layer-toggle" onclick="toggleLayer(this,'weather')">
      <span class="dot" style="background:#06b6d4;"></span>
      <span style="font-size:12px;font-weight:500;flex:1;">Weather</span>
    </button>
    <button class="layer-toggle" onclick="toggleLayer(this,'osm')">
      <span class="dot" style="background:#475569;"></span>
      <span style="font-size:12px;font-weight:500;flex:1;">Road Network</span>
      <span style="font-size:10px;color:#64748b;">OSM</span>
    </button>

    <!-- AQI Scale -->
    <div class="section-title">AQI Scale (India NAQI)</div>
    <div style="display:flex;flex-direction:column;gap:4px;">
      {"".join(f'<div style="display:flex;align-items:center;gap:8px;font-size:11px;"><span style="width:10px;height:10px;border-radius:2px;background:{c};display:inline-block;flex-shrink:0;"></span><span style="color:#94a3b8;">{label}</span></div>'
        for c, label in [
          ("#22c55e","0–50: Good"),
          ("#84cc16","51–100: Satisfactory"),
          ("#f59e0b","101–200: Moderate"),
          ("#f97316","201–300: Poor"),
          ("#ef4444","301–400: Very Poor"),
          ("#7c3aed","401+: Severe"),
          ("#94a3b8","N/A: No data"),
        ]
      )}
    </div>

    <!-- API Links -->
    <div class="section-title">API Endpoints</div>
    <div style="display:flex;flex-direction:column;gap:4px;">
      {"".join(f'<a href="{url}" target="_blank" style="font-size:10px;color:#3b82f6;text-decoration:none;font-family:monospace;background:#1e293b;padding:4px 8px;border-radius:4px;display:block;overflow:hidden;text-overflow:ellipsis;">{url}</a>'
        for url in ["/api/v1/stations","/api/v1/zones","/api/v1/map","/api/v1/map/geojson"]
      )}
    </div>

    <!-- Export links -->
    <div class="section-title">Downloads</div>
    <div style="display:flex;flex-direction:column;gap:4px;">
      <a href="/api/v1/map/geojson" target="_blank"
         style="font-size:11px;color:#22c55e;text-decoration:none;background:#1e293b;padding:6px 10px;border-radius:6px;border:1px solid #334155;display:flex;align-items:center;gap:6px;">
        📦 Export GeoJSON Files
      </a>
      <a href="/dashboard/map/static"
         style="font-size:11px;color:#94a3b8;text-decoration:none;background:#1e293b;padding:6px 10px;border-radius:6px;border:1px solid #334155;display:flex;align-items:center;gap:6px;">
        🗺️ Standalone Map HTML
      </a>
    </div>

    <div style="margin-top:auto;padding-top:12px;border-top:1px solid #1e293b;font-size:10px;color:#475569;text-align:center;">
      UrbanTwin Digital Twin &copy; 2025 &bull; Pune &amp; PCMC
    </div>
  </div>

  <!-- Map iframe -->
  <div style="flex:1;position:relative;">
    <div id="map-loading" style="position:absolute;inset:0;background:#020617;display:flex;align-items:center;justify-content:center;z-index:100;flex-direction:column;gap:16px;">
      <div style="width:48px;height:48px;border:4px solid #334155;border-top-color:#3b82f6;border-radius:50%;animation:spin 1s linear infinite;"></div>
      <div style="color:#64748b;font-size:14px;">Loading Digital Twin Map…</div>
    </div>
    <iframe id="map-frame" src="/dashboard/map/embed"
      onload="document.getElementById('map-loading').style.display='none';"
      style="width:100%;height:100vh;border:none;">
    </iframe>
  </div>
</div>

<style>
@keyframes spin {{ to {{ transform: rotate(360deg); }} }}
</style>

<script>
function toggleLayer(btn, layerName) {{
  btn.classList.toggle('active');
  const isActive = btn.classList.contains('active');
  const frame = document.getElementById('map-frame');
  try {{
    const mapWindow = frame.contentWindow;
    // Signal the embedded map about layer visibility change
    mapWindow.postMessage({{ action: 'toggleLayer', layer: layerName, visible: isActive }}, '*');
  }} catch(e) {{
    // Cross-origin – reload with query params
    const url = new URL(frame.src, window.location.origin);
    url.searchParams.set(layerName, isActive ? '1' : '0');
    frame.src = url.toString();
  }}
}}
</script>
</body>
</html>"""


def export_gis_dashboard_html(output_path: Optional[Path] = None) -> Path:
    """Export the GIS dashboard HTML to a file.

    Args:
        output_path: Optional override path.

    Returns:
        Path to the written HTML file.
    """
    output_path = Path(output_path) if output_path else GIS_REPORTS_DIR / "gis_dashboard.html"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_gis_dashboard_html(), encoding="utf-8")
    logger.info("Exported GIS dashboard HTML", path=str(output_path))
    return output_path


# ---------------------------------------------------------------------------
# Dashboard routes
# ---------------------------------------------------------------------------

@router.get("/map", response_class=HTMLResponse, summary="GIS Digital Twin Map Dashboard")
async def gis_map_dashboard() -> HTMLResponse:
    """Full-screen interactive GIS dashboard for the Pune Digital Twin."""
    try:
        html = build_gis_dashboard_html()
        return HTMLResponse(content=html)
    except Exception as exc:
        logger.error("GIS dashboard build failed", error=str(exc))
        raise HTTPException(status_code=500, detail=f"Dashboard error: {exc}")


@router.get("/map/embed", response_class=HTMLResponse, summary="Embedded Folium Map")
async def gis_map_embed() -> HTMLResponse:
    """Serve the embedded Folium map (used inside the dashboard iframe)."""
    try:
        from gis.map_builder import build_pune_map

        m = build_pune_map(include_osm=False)
        html_content = m.get_root().render()
        return HTMLResponse(content=html_content)
    except Exception as exc:
        logger.error("Folium embed map failed", error=str(exc))
        # Return minimal error page
        return HTMLResponse(
            content=f"""<html><body style="background:#020617;color:#ef4444;font-family:monospace;padding:20px;">
            <h3>Map Error</h3><pre>{exc}</pre></body></html>""",
            status_code=200,
        )


@router.get("/map/static", response_class=HTMLResponse, summary="Standalone Map HTML")
async def gis_map_static() -> HTMLResponse:
    """Serve a standalone full-featured Folium map HTML."""
    try:
        from gis.map_builder import build_pune_map

        m = build_pune_map(include_osm=False)
        html_content = m.get_root().render()
        return HTMLResponse(content=html_content)
    except Exception as exc:
        logger.error("Static map failed", error=str(exc))
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# API routes
# ---------------------------------------------------------------------------

@api_router.get("/map", summary="Map metadata and statistics")
async def get_map_metadata() -> JSONResponse:
    """Return map statistics, layer availability, and AQI summary."""
    try:
        from gis.map_builder import generate_map_statistics

        stats = generate_map_statistics()
        stats["endpoint"] = "/api/v1/map"
        stats["dashboard"] = "/dashboard/map"
        return JSONResponse(content=stats)
    except Exception as exc:
        logger.error("Map metadata endpoint failed", error=str(exc))
        raise HTTPException(status_code=500, detail=str(exc))


@api_router.get("/stations", summary="AQI station readings")
async def get_stations(
    station_id: Optional[str] = Query(None, description="Filter by station ID"),
) -> JSONResponse:
    """Return latest AQI and pollutant readings for all (or a specific) station."""
    try:
        from gis.layers import load_station_layer

        stations = load_station_layer()
        if station_id:
            stations = stations[stations["station_id"].astype(str) == str(station_id)]
            if stations.empty:
                raise HTTPException(status_code=404, detail=f"Station '{station_id}' not found")

        records = json.loads(stations.to_json(orient="records", date_format="iso"))
        return JSONResponse(content={
            "count": len(records),
            "stations": records,
        })
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Stations endpoint failed", error=str(exc))
        raise HTTPException(status_code=500, detail=str(exc))


@api_router.get("/zones", summary="H3 zone AQI data")
async def get_zones(
    limit: int = Query(100, ge=1, le=500, description="Max zones to return"),
    min_aqi: Optional[float] = Query(None, description="Filter zones with mean_aqi >= this value"),
) -> JSONResponse:
    """Return H3 zones with mean AQI, color, and category data."""
    try:
        from gis.layers import load_h3_layer

        zones = load_h3_layer()
        # Drop heavy geometry column for API response
        drop_cols = [c for c in ["geometry", "geometry_wkt"] if c in zones.columns]
        if drop_cols:
            zones = zones.drop(columns=drop_cols)

        if min_aqi is not None and "mean_aqi" in zones.columns:
            zones = zones[zones["mean_aqi"] >= min_aqi]

        zones = zones.head(limit)
        records = json.loads(zones.to_json(orient="records", date_format="iso"))

        return JSONResponse(content={
            "count": len(records),
            "resolution": settings.H3_RESOLUTION,
            "zones": records,
        })
    except Exception as exc:
        logger.error("Zones endpoint failed", error=str(exc))
        raise HTTPException(status_code=500, detail=str(exc))


@api_router.get("/map/geojson", summary="Export GeoJSON for all layers")
async def export_map_geojson() -> JSONResponse:
    """Trigger GeoJSON export for all layers and return file paths."""
    try:
        from gis.geojson_export import export_all_geojson

        paths = export_all_geojson()
        return JSONResponse(content={
            "exported": {k: str(v) for k, v in paths.items()},
            "count": len(paths),
            "message": "GeoJSON files written to reports/gis/",
        })
    except Exception as exc:
        logger.error("GeoJSON export endpoint failed", error=str(exc))
        raise HTTPException(status_code=500, detail=str(exc))

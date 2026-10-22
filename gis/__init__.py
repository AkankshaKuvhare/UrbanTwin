"""GIS module for UrbanTwin – Interactive Digital Twin Map of Pune & PCMC."""

from gis.layers import (
    load_station_layer,
    load_h3_layer,
    load_traffic_layer,
    load_weather_layer,
    get_aqi_color,
    get_aqi_category,
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
    router as gis_dashboard_router,
    api_router as gis_api_router,
    build_gis_dashboard_html,
    export_gis_dashboard_html,
)

__all__ = [
    # Layers
    "load_station_layer",
    "load_h3_layer",
    "load_traffic_layer",
    "load_weather_layer",
    "get_aqi_color",
    "get_aqi_category",
    # GeoJSON exports
    "export_stations_geojson",
    "export_h3_zones_geojson",
    "export_traffic_geojson",
    "export_all_geojson",
    "validate_geojson",
    # Map builder
    "build_pune_map",
    "export_map_html",
    "export_map_png",
    "generate_map_statistics",
    # Dashboard & API routers
    "gis_dashboard_router",
    "gis_api_router",
    "build_gis_dashboard_html",
    "export_gis_dashboard_html",
]

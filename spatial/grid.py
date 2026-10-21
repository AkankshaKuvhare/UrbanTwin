"""Spatial grid generation interfaces for UrbanTwin.

Generates Uber H3 discrete global grid systems (Resolution 7) covering
Pune Municipal Corporation (PMC) and Pimpri-Chinchwad Municipal Corporation (PCMC).
"""

from typing import List, Optional, Tuple
import geopandas as gpd
import h3
import pandas as pd
from shapely.geometry import Polygon

from config.settings import settings

# PMC + PCMC Spatial Bounding Box
PMC_PCMC_BBOX = {
    "min_lat": 18.40,
    "max_lat": 18.72,
    "min_lon": 73.70,
    "max_lon": 74.02,
}


def generate_h3_grid_pmc_pcmc(
    resolution: int = 7,
    bbox: Optional[dict] = None,
) -> gpd.GeoDataFrame:
    """Generate H3 hexagonal grid cells covering Pune (PMC + PCMC).

    Args:
        resolution: H3 resolution level (default: 7, ~1.2km edge length).
        bbox: Dictionary with min_lat, max_lat, min_lon, max_lon.

    Returns:
        GeoDataFrame with columns:
            zone_id (H3 index), resolution, centroid_lat, centroid_lon, geometry (Polygon).
    """
    bounds = bbox or PMC_PCMC_BBOX

    # Construct boundary polygon in (lat, lon) order for H3 LatLngPoly
    lat_lng_coords = [
        (bounds["min_lat"], bounds["min_lon"]),
        (bounds["min_lat"], bounds["max_lon"]),
        (bounds["max_lat"], bounds["max_lon"]),
        (bounds["max_lat"], bounds["min_lon"]),
    ]

    h3_polygon = h3.LatLngPoly(lat_lng_coords)
    cell_ids = list(h3.polygon_to_cells(h3_polygon, resolution))

    records = []
    for cell in sorted(cell_ids):
        centroid_lat, centroid_lon = h3.cell_to_latlng(cell)
        boundary_latlng = h3.cell_to_boundary(cell)
        # Convert (lat, lon) to (lon, lat) for standard GIS / Shapely Polygon
        lonlat_coords = [(lon, lat) for lat, lon in boundary_latlng]
        polygon_geom = Polygon(lonlat_coords)

        records.append({
            "zone_id": str(cell),
            "resolution": int(resolution),
            "centroid_lat": round(centroid_lat, 6),
            "centroid_lon": round(centroid_lon, 6),
            "geometry": polygon_geom,
        })

    gdf = gpd.GeoDataFrame(records, crs="EPSG:4326")
    return gdf


class H3HexGrid:
    """H3 Hexagonal grid generator for UrbanTwin spatial tessellation."""

    def __init__(self, resolution: int = 7) -> None:
        self.resolution = resolution

    def generate_grid(self, bbox: Optional[dict] = None) -> gpd.GeoDataFrame:
        """Generate H3 grid cells for PMC + PCMC."""
        return generate_h3_grid_pmc_pcmc(resolution=self.resolution, bbox=bbox)

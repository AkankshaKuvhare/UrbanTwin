"""Spatial Snapping and Entity Resolution Engine for UrbanTwin.

Maps heterogeneous observation entities (AQI monitoring stations, weather references)
to standard H3 Resolution 7 hexagonal zones, computing planar/great-circle distances
and building the audited entity_correspondence table.
"""

from typing import Any, Dict, List, Optional, Tuple, Union
import h3
import pandas as pd

from spatial.grid import generate_h3_grid_pmc_pcmc
from spatial.utils import haversine_distance_km, haversine_distance_m

# Known coordinates for Pune continuous air quality monitoring stations
PUNE_STATION_COORDINATES: Dict[str, Dict[str, Any]] = {
    "11613": {
        "station_name": "Revenue Colony-Shivajinagar, Pune - IITM",
        "latitude": 18.5314,
        "longitude": 73.8446,
        "city": "Pune",
    },
    "3409439": {
        "station_name": "Savitribai Phule Pune University, Pune - MPCB",
        "latitude": 18.5529,
        "longitude": 73.8260,
        "city": "Pune",
    },
    "5661": {
        "station_name": "Karve Road Pune, Pune - MPCB",
        "latitude": 18.5020,
        "longitude": 73.8270,
        "city": "Pune",
    },
    "3409438": {
        "station_name": "Katraj Dairy, Pune - MPCB",
        "latitude": 18.4550,
        "longitude": 73.8580,
        "city": "Pune",
    },
    "3409436": {
        "station_name": "Park Street Wakad, Pimpri Chinchwad - MPCB",
        "latitude": 18.6015,
        "longitude": 73.7645,
        "city": "Pimpri Chinchwad",
    },
}

# City-wide weather reference point (Pune center)
PUNE_WEATHER_CENTER = {
    "weather_id": "openmeteo_pune_center",
    "latitude": 18.5204,
    "longitude": 73.8567,
}


def classify_distance_validity(distance_km: float) -> str:
    """Classify spatial correspondence validity based on distance threshold rules.

    Rules:
        - distance <= 1.5 km: valid
        - 1.5 km < distance <= 3.0 km: warning
        - distance > 3.0 km: invalid (kept but flagged)
    """
    if distance_km <= 1.5:
        return "valid"
    elif distance_km <= 3.0:
        return "warning"
    else:
        return "invalid"


class SpatialEntityResolver:
    """Resolves sensor and meteorological entities to H3 discrete global grid cells."""

    def __init__(self, resolution: int = 7) -> None:
        self.resolution = resolution
        self.zones_gdf = generate_h3_grid_pmc_pcmc(resolution=self.resolution)
        self.zone_centroids = {
            row["zone_id"]: (row["centroid_lat"], row["centroid_lon"])
            for _, row in self.zones_gdf.iterrows()
        }

    def assign_station_to_zone(
        self, station_id: str, latitude: float, longitude: float
    ) -> Dict[str, Any]:
        """Assign an individual station point to its enclosing H3 cell."""
        zone_id = str(h3.latlng_to_cell(latitude, longitude, self.resolution))

        if zone_id in self.zone_centroids:
            centroid_lat, centroid_lon = self.zone_centroids[zone_id]
            dist_m = haversine_distance_m(latitude, longitude, centroid_lat, centroid_lon)
            dist_km = haversine_distance_km(latitude, longitude, centroid_lat, centroid_lon)
            status = classify_distance_validity(dist_km)
        else:
            # Point is outside the PMC+PCMC grid boundaries
            min_dist_km = float("inf")
            best_zone = zone_id
            for z, (c_lat, c_lon) in self.zone_centroids.items():
                d = haversine_distance_km(latitude, longitude, c_lat, c_lon)
                if d < min_dist_km:
                    min_dist_km = d
                    best_zone = z
            zone_id = best_zone
            dist_km = min_dist_km
            dist_m = dist_km * 1000.0
            status = classify_distance_validity(dist_km)

        return {
            "station_id": str(station_id),
            "zone_id": zone_id,
            "distance_m": dist_m,
            "distance_km": dist_km,
            "method": "h3_latlng_to_cell",
            "is_valid": status,
            "snap_status": status,
        }

    def build_station_zone_mapping(
        self, stations_dict: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> pd.DataFrame:
        """Assign all AQI monitoring stations to their corresponding H3 zones."""
        source_stations = stations_dict or PUNE_STATION_COORDINATES
        records = []

        for st_id, info in source_stations.items():
            assigned = self.assign_station_to_zone(
                station_id=st_id,
                latitude=info["latitude"],
                longitude=info["longitude"],
            )
            records.append({
                "station_id": assigned["station_id"],
                "station_name": info.get("station_name", f"Station {st_id}"),
                "latitude": info["latitude"],
                "longitude": info["longitude"],
                "zone_id": assigned["zone_id"],
                "distance_m": assigned["distance_m"],
                "distance_km": assigned["distance_km"],
                "method": assigned["method"],
                "is_valid": assigned["is_valid"],
                "snap_status": assigned["is_valid"],
            })

        return pd.DataFrame(records)

    def resolve_all_stations(self) -> pd.DataFrame:
        """Alias for resolving all known Pune stations with snap status."""
        return self.build_station_zone_mapping()

    def resolve_point(
        self, latitude: float, longitude: float, entity_name: str = "point"
    ) -> Dict[str, Any]:
        """Resolve arbitrary point to H3 zone with snap status."""
        res = self.assign_station_to_zone(station_id=entity_name, latitude=latitude, longitude=longitude)
        res["snap_status"] = res["is_valid"]
        return res

    def build_weather_zone_mapping(
        self,
        weather_center: Optional[Dict[str, Any]] = None,
    ) -> pd.DataFrame:
        """Assign city-wide weather observations across all H3 zones."""
        wc = weather_center or PUNE_WEATHER_CENTER
        w_lat, w_lon = wc["latitude"], wc["longitude"]
        w_id = wc["weather_id"]

        records = []
        for _, row in self.zones_gdf.iterrows():
            z_id = row["zone_id"]
            c_lat, c_lon = row["centroid_lat"], row["centroid_lon"]
            dist_km = haversine_distance_km(w_lat, w_lon, c_lat, c_lon)

            records.append({
                "zone_id": z_id,
                "weather_station_id": w_id,
                "weather_lat": w_lat,
                "weather_lon": w_lon,
                "distance_km": dist_km,
                "method": "city_wide_broadcast",
                "is_valid": classify_distance_validity(dist_km),
            })

        return pd.DataFrame(records)

    def build_entity_correspondence_table(
        self,
        station_mapping_df: Optional[pd.DataFrame] = None,
        weather_mapping_df: Optional[pd.DataFrame] = None,
    ) -> pd.DataFrame:
        """Create the master entity_correspondence table combining station and weather entities."""
        st_map = station_mapping_df if station_mapping_df is not None else self.build_station_zone_mapping()
        wt_map = weather_mapping_df if weather_mapping_df is not None else self.build_weather_zone_mapping()

        rows = []

        # Stations
        for _, row in st_map.iterrows():
            rows.append({
                "entity_id": str(row["station_id"]),
                "entity_type": "station",
                "zone_id": str(row["zone_id"]),
                "distance_km": float(row["distance_km"]),
                "mapping_method": str(row["method"]),
                "is_valid": str(row["is_valid"]),
            })

        # Weather
        for _, row in wt_map.iterrows():
            rows.append({
                "entity_id": str(row["weather_station_id"]),
                "entity_type": "weather",
                "zone_id": str(row["zone_id"]),
                "distance_km": float(row["distance_km"]),
                "mapping_method": str(row["method"]),
                "is_valid": str(row["is_valid"]),
            })

        return pd.DataFrame(rows)

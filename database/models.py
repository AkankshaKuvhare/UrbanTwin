"""SQLAlchemy ORM models defining the UrbanTwin research domain schema.

Includes models for Station and AQIObservation (CongestAir module)
as well as spatial zones, raw entities, entity spatial correspondence,
and fused hourly observation tables with real vs. synthetic isolation.
"""

from datetime import date, datetime
from typing import Optional
from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from geoalchemy2 import Geometry

from database.base import Base, TimestampMixin


class Station(Base):
    """Monitoring station entity (CPCB / MPCB / IITM air quality monitoring stations)."""

    __tablename__ = "stations"

    station_id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    station_name: Mapped[str] = mapped_column(String(255), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    observations = relationship("AQIObservation", back_populates="station", cascade="all, delete-orphan")


class AQIObservation(Base):
    """Daily or hourly historical air quality observation record."""

    __tablename__ = "aqi_observations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    station_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("stations.station_id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    observation_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    aqi: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    pm25: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    pm10: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    no2: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    co: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    so2: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    o3: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    dominant_pollutant: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    station = relationship("Station", back_populates="observations")

    __table_args__ = (
        UniqueConstraint("station_id", "observation_date", name="uq_station_observation_date"),
        Index("ix_aqi_obs_station_date", "station_id", "observation_date"),
    )


class SpatialZone(Base, TimestampMixin):
    """Represents a standardized spatial partition over Pune (e.g., H3 index or 1km grid)."""

    __tablename__ = "spatial_zones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    zone_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    zone_type: Mapped[str] = mapped_column(String(32), default="h3_res7", nullable=False)  # 'h3_res7' or 'grid_1km'
    centroid_lat: Mapped[float] = mapped_column(Float, nullable=False)
    centroid_lon: Mapped[float] = mapped_column(Float, nullable=False)
    
    # PostGIS geometry column for boundary polygon
    geom = Column(Geometry(geometry_type="POLYGON", srid=4326), nullable=True)

    # Relationships
    correspondences = relationship("EntityCorrespondence", back_populates="zone", cascade="all, delete-orphan")
    observations = relationship("FusedObservation", back_populates="zone", cascade="all, delete-orphan")


class RawEntity(Base, TimestampMixin):
    """Represents an external entity (AQI monitor, traffic sensor node, weather station)."""

    __tablename__ = "raw_entities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    raw_entity_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    entity_type: Mapped[str] = mapped_column(String(32), index=True, nullable=False)  # 'aqi', 'traffic', 'weather'
    source_name: Mapped[str] = mapped_column(String(64), nullable=False)              # 'openaq', 'tomtom', 'openmeteo'
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # PostGIS point geometry
    geom = Column(Geometry(geometry_type="POINT", srid=4326), nullable=True)

    # Unique constraint per source
    __table_args__ = (
        UniqueConstraint("raw_entity_id", "source_name", "is_synthetic", name="uq_raw_entity_source"),
    )


class EntityCorrespondence(Base, TimestampMixin):
    """Entity resolution correspondence mapping raw entities to standardized spatial zones.
    
    This correspondence table is a standalone publishable research artifact.
    """

    __tablename__ = "entity_correspondences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    raw_entity_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    entity_type: Mapped[str] = mapped_column(String(32), index=True, nullable=False)  # 'aqi', 'traffic', 'weather'
    zone_id: Mapped[str] = mapped_column(String(64), ForeignKey("spatial_zones.zone_id"), index=True, nullable=False)
    distance_km: Mapped[float] = mapped_column(Float, nullable=False)
    method: Mapped[str] = mapped_column(String(64), default="nearest_neighbor", nullable=False)
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationship
    zone = relationship("SpatialZone", back_populates="correspondences")

    __table_args__ = (
        UniqueConstraint("raw_entity_id", "entity_type", "zone_id", "is_synthetic", name="uq_entity_zone_corr"),
    )


class FusedObservation(Base, TimestampMixin):
    """Master space-time table: zone x hourly-timestamp fused multi-modal data.
    
    Includes air quality metrics, traffic congestion indicators, and meteorological covariates.
    """

    __tablename__ = "fused_observations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    zone_id: Mapped[str] = mapped_column(String(64), ForeignKey("spatial_zones.zone_id"), index=True, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Air Quality Metrics
    pm25: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    pm10: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    no2: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    co: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    aqi_calculated: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Traffic Congestion Metrics
    congestion_index: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    current_speed_kmh: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    free_flow_speed_kmh: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    travel_time_delay_sec: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Meteorological Covariates
    temperature_c: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    relative_humidity: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    wind_speed_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    wind_direction_deg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    boundary_layer_height_m: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    precipitation_mm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Relationship
    zone = relationship("SpatialZone", back_populates="observations")

    __table_args__ = (
        UniqueConstraint("zone_id", "timestamp", "is_synthetic", name="uq_zone_timestamp_synthetic"),
        Index("ix_fused_zone_timestamp", "zone_id", "timestamp"),
    )


class FusedZoneTime(Base):
    """Milestone 5 Master Analytical Dataset Table (single source of truth).
    
    Space-time panel mapping H3 zones x timestamps fusing AQI, weather, and traffic placeholders.
    """

    __tablename__ = "fused_zone_time"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    zone_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    observation_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    station_id: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)

    # Air Quality Metrics
    aqi: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    pm25: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    pm10: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    no2: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    co: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    so2: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    o3: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    dominant_pollutant: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    # Weather Metrics (from Open-Meteo)
    temperature_2m: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    relative_humidity_2m: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    precipitation: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    wind_speed_10m: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    wind_direction_10m: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    surface_pressure: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    boundary_layer_height: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Traffic Placeholders (traffic is not available yet -> NULLABLE)
    traffic_speed: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    traffic_congestion: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    traffic_travel_time: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    traffic_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Missingness Indicators
    weather_missing: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    aqi_missing: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    traffic_missing: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("zone_id", "observation_datetime", "station_id", name="uq_fused_zone_dt_station"),
        Index("ix_fused_zt_zone_dt", "zone_id", "observation_datetime"),
    )


class TrafficObservation(Base):
    """Milestone 7 TomTom Traffic Flow Observations Table.
    
    Append-only repository of arterial corridor flow conditions across Pune.
    Maintains strict isolation from air quality and weather.
    """

    __tablename__ = "traffic_observations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    point_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    current_speed: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    free_flow_speed: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    current_travel_time: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    free_flow_travel_time: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    road_closure: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    frc: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    source: Mapped[str] = mapped_column(String(32), default="tomtom", nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("point_id", "timestamp", name="uq_traffic_point_timestamp"),
        Index("ix_traffic_point_time", "point_id", "timestamp"),
    )

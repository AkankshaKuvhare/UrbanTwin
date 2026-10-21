"""Application settings and configuration management for UrbanTwin.

Uses pydantic-settings to validate and parse environment variables.
"""

from enum import Enum
from pathlib import Path
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class EnvironmentType(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class DataMode(str, Enum):
    REAL = "real"
    SYNTHETIC = "synthetic"


class Settings(BaseSettings):
    """Central configuration class for UrbanTwin research monorepo."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # General Application Settings
    APP_NAME: str = "UrbanTwin"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: EnvironmentType = EnvironmentType.DEVELOPMENT
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Structured Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # "json" or "console"

    # PostgreSQL & PostGIS Database Connections
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = "urbantwin"
    DB_PASSWORD: str = "urbantwin_secret"
    DB_NAME: str = "urbantwin_db"
    DATABASE_URL: str = "postgresql+psycopg2://urbantwin:urbantwin_secret@localhost:5432/urbantwin_db"
    ASYNC_DATABASE_URL: str = "postgresql+asyncpg://urbantwin:urbantwin_secret@localhost:5432/urbantwin_db"

    # External APIs
    OPENAQ_API_KEY: Optional[str] = None
    OPENAQ_BASE_URL: str = "https://api.openaq.org/v3"
    TOMTOM_API_KEY: Optional[str] = None
    TOMTOM_BASE_URL: str = "https://api.tomtom.com/traffic"
    COLLECTION_INTERVAL: str = "30 minutes"
    OPENMETEO_BASE_URL: str = "https://archive-api.open-meteo.com/v1/archive"

    # Spatial Bounds - Pune, Maharashtra, India
    PUNE_BBOX_MIN_LAT: float = 18.40
    PUNE_BBOX_MAX_LAT: float = 18.65
    PUNE_BBOX_MIN_LON: float = 73.75
    PUNE_BBOX_MAX_LON: float = 74.05
    DEFAULT_CRS: str = "EPSG:4326"
    PROJECTED_CRS: str = "EPSG:32643"  # UTM Zone 43N for meter-distance operations
    H3_RESOLUTION: int = 7

    # Data Architecture: Strict Separation of Real and Synthetic Data
    DATA_MODE: DataMode = DataMode.SYNTHETIC
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    REAL_DATA_DIR: Path = BASE_DIR / "data" / "real"
    SYNTHETIC_DATA_DIR: Path = BASE_DIR / "data" / "synthetic"

    # Scheduler Configuration
    ENABLE_SCHEDULER: bool = False
    POLLING_INTERVAL_MINUTES: int = 60

    @property
    def active_data_dir(self) -> Path:
        """Returns the data directory based on active DATA_MODE."""
        return self.SYNTHETIC_DATA_DIR if self.DATA_MODE == DataMode.SYNTHETIC else self.REAL_DATA_DIR


# Cached singleton instance of settings
settings = Settings()

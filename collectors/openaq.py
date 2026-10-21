"""Collector interface for OpenAQ Air Quality Data (Pune stations).

Acquires PM2.5, PM10, NO2, and CO sensor observations across Pune coordinates.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Optional
import pandas as pd

from collectors.base import BaseCollector
from config.settings import DataMode


class OpenAQCollector(BaseCollector):
    """Collector interface for OpenAQ v3 API."""

    @property
    def source_name(self) -> str:
        return "openaq"

    def fetch_raw(
        self,
        start_time: datetime,
        end_time: datetime,
        **kwargs: Any,
    ) -> Any:
        """Fetch raw air quality measurements from OpenAQ API or generate synthetic series.
        
        TODO: Implement REST client for OpenAQ v3 /locations and /measurements endpoints
        with rate-limit handling and pagination.
        """
        raise NotImplementedError("OpenAQCollector.fetch_raw is not yet implemented.")

    def parse_to_dataframe(self, raw_data: Any) -> pd.DataFrame:
        """Parse raw OpenAQ JSON response into normalized DataFrame.
        
        Expected output columns:
        - raw_entity_id: str (station / sensor id)
        - timestamp: datetime (UTC+05:30)
        - latitude: float
        - longitude: float
        - parameter: str (pm25, pm10, no2, co)
        - value: float
        - unit: str
        """
        raise NotImplementedError("OpenAQCollector.parse_to_dataframe is not yet implemented.")

    def validate(self, df: pd.DataFrame) -> bool:
        """Validate air quality data ranges (e.g. PM2.5 >= 0, plausible physical bounds)."""
        raise NotImplementedError("OpenAQCollector.validate is not yet implemented.")

    def save(self, df: pd.DataFrame, filename: Optional[str] = None) -> Path:
        """Save parsed air quality observations to parquet."""
        raise NotImplementedError("OpenAQCollector.save is not yet implemented.")

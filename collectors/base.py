"""Abstract Base Class for Data Collectors in UrbanTwin.

Defines the contract for raw data acquisition, parsing, validation,
and persistence, with explicit support for real vs. synthetic execution.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd
from pydantic import BaseModel

from config.logging import get_logger
from config.settings import DataMode, settings

logger = get_logger(__name__)


class CollectorMetadata(BaseModel):
    """Metadata recorded with every collection run."""
    source_name: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    records_fetched: int = 0
    is_synthetic: bool = False
    status: str = "pending"
    error_message: Optional[str] = None


class BaseCollector(ABC):
    """Abstract collector interface for acquiring and normalizing external data."""

    def __init__(self, data_mode: Optional[DataMode] = None) -> None:
        """Initialize collector with explicit data mode (real or synthetic)."""
        self.data_mode = data_mode or settings.DATA_MODE
        self.is_synthetic = self.data_mode == DataMode.SYNTHETIC
        self.output_dir: Path = (
            settings.SYNTHETIC_DATA_DIR if self.is_synthetic else settings.REAL_DATA_DIR
        ) / "raw"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger = get_logger(self.__class__.__name__)

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Unique identifier of the data source (e.g. 'openaq', 'openmeteo', 'tomtom')."""
        pass

    @abstractmethod
    def fetch_raw(
        self,
        start_time: datetime,
        end_time: datetime,
        **kwargs: Any,
    ) -> Any:
        """Fetch raw payload from external API or generate synthetic mock data.
        
        Args:
            start_time: Beginning of query window.
            end_time: End of query window.
            **kwargs: Provider-specific parameters (coordinates, bounding box, pollutants).

        Returns:
            Raw response payload (JSON dict, list, or binary stream).
        """
        pass

    @abstractmethod
    def parse_to_dataframe(self, raw_data: Any) -> pd.DataFrame:
        """Parse raw response into a standardized intermediate Pandas DataFrame.
        
        Args:
            raw_data: Unprocessed response from `fetch_raw`.

        Returns:
            Standardized DataFrame with normalized column names and timestamps.
        """
        pass

    @abstractmethod
    def validate(self, df: pd.DataFrame) -> bool:
        """Validate parsed data against quality rules (schema, ranges, null rates).
        
        Args:
            df: Parsed DataFrame to inspect.

        Returns:
            True if dataset passes validation checks, raises or returns False otherwise.
        """
        pass

    @abstractmethod
    def save(self, df: pd.DataFrame, filename: Optional[str] = None) -> Path:
        """Persist parsed data to disk in parquet/csv format respecting real/synthetic split.
        
        Args:
            df: Validated DataFrame.
            filename: Target filename.

        Returns:
            Path to saved file.
        """
        pass

    def run(
        self,
        start_time: datetime,
        end_time: datetime,
        **kwargs: Any,
    ) -> Path:
        """Execute full collection pipeline: fetch -> parse -> validate -> save.
        
        Default template method orchestrating lifecycle and logging.
        """
        self.logger.info(
            "Starting data collection run",
            source=self.source_name,
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat(),
            synthetic=self.is_synthetic,
        )
        raw = self.fetch_raw(start_time, end_time, **kwargs)
        df = self.parse_to_dataframe(raw)
        self.validate(df)
        path = self.save(df)
        self.logger.info(
            "Completed data collection run",
            source=self.source_name,
            output_path=str(path),
            record_count=len(df),
        )
        return path

"""Abstract Base Class for Data and Analysis Pipelines in UrbanTwin."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel

from config.logging import get_logger
from config.settings import DataMode, settings


class PipelineResult(BaseModel):
    """Execution status and metric summary for pipeline runs."""
    pipeline_name: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    success: bool = False
    metrics: Dict[str, Any] = {}
    error_message: Optional[str] = None


class BasePipeline(ABC):
    """Abstract interface defining the execution lifecycle of research pipelines."""

    def __init__(self, data_mode: Optional[DataMode] = None) -> None:
        self.data_mode = data_mode or settings.DATA_MODE
        self.is_synthetic = self.data_mode == DataMode.SYNTHETIC
        self.logger = get_logger(self.__class__.__name__)

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the pipeline stage."""
        pass

    @abstractmethod
    def execute(self, **kwargs: Any) -> PipelineResult:
        """Run the end-to-end pipeline workflow.
        
        Args:
            **kwargs: Arbitrary pipeline parameters (date ranges, target zones, flags).

        Returns:
            PipelineResult detailing execution outcome.
        """
        pass

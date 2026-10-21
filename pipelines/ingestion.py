"""Data Ingestion Pipeline Interface (Stage 1).

Orchestrates multi-modal collection from OpenAQ, TomTom, and Open-Meteo.
"""

from typing import Any
from pipelines.base import BasePipeline, PipelineResult


class DataIngestionPipeline(BasePipeline):
    """Pipeline coordinating raw data acquisition across all three domains."""

    @property
    def name(self) -> str:
        return "data_ingestion_stage_1"

    def execute(self, **kwargs: Any) -> PipelineResult:
        """Run all collectors for the configured time window.
        
        TODO: Coordinate OpenAQ, OpenMeteo, and TomTom collectors,
        saving raw partitioned parquet files to data/raw/ respecting real/synthetic flags.
        """
        raise NotImplementedError("DataIngestionPipeline.execute is not yet implemented.")

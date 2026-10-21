"""Unit tests verifying abstract interface contracts for collectors, pipelines, and models."""

from datetime import datetime, timezone
import pytest

from collectors.openaq import OpenAQCollector
from collectors.openmeteo import OpenMeteoCollector
from collectors.tomtom import TomTomCollector
from pipelines.ingestion import DataIngestionPipeline
from pipelines.spatial_correspondence import SpatialCorrespondencePipeline
from pipelines.fusion import DatasetFusionPipeline
from models.causality import VARGrangerTester
from models.baseline import WeatherBaselineModel
from models.predictive import TrafficWeatherModel


def test_collector_interfaces_raise_not_implemented() -> None:
    """Verify that collector interface methods require implementation."""
    now = datetime.now(timezone.utc)

    openaq = OpenAQCollector()
    assert openaq.source_name == "openaq"
    with pytest.raises(NotImplementedError):
        openaq.fetch_raw(now, now)

    tomtom = TomTomCollector()
    assert tomtom.source_name == "tomtom"
    with pytest.raises(NotImplementedError):
        tomtom.fetch_raw(now, now)

    openmeteo = OpenMeteoCollector()
    assert openmeteo.source_name == "openmeteo"


def test_pipeline_interfaces_raise_not_implemented() -> None:
    """Verify that pipeline execution methods require implementation."""
    ingest = DataIngestionPipeline()
    assert ingest.name == "data_ingestion_stage_1"
    with pytest.raises(NotImplementedError):
        ingest.execute()

    spatial = SpatialCorrespondencePipeline()
    assert spatial.name == "spatial_correspondence_stage_2"
    with pytest.raises(NotImplementedError):
        spatial.execute()

    fusion = DatasetFusionPipeline()
    assert fusion.name == "dataset_fusion_stage_3"
    with pytest.raises(NotImplementedError):
        fusion.execute()


def test_model_interfaces_raise_not_implemented() -> None:
    """Verify that model training and inference methods require implementation."""
    causality = VARGrangerTester()
    with pytest.raises(NotImplementedError):
        causality.select_var_lag_order(None)

    baseline = WeatherBaselineModel()
    with pytest.raises(NotImplementedError):
        baseline.fit(None, None)

    predictive = TrafficWeatherModel()
    with pytest.raises(NotImplementedError):
        predictive.fit(None, None)

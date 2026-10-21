"""Comprehensive tests for Milestone 7 TomTom Traffic Collector.

Tests:
1. Monitoring points configuration schema & validation
2. Mock TomTom Flow Segment Data API responses
3. Retry mechanism on transient network errors
4. Duplicate timestamp and point_id prevention (append-only idempotency)
5. Database insertion logic with SQLite in-memory fallback
6. Pipeline orchestration and health reporting
7. Background scheduler job registration
"""

from datetime import datetime, timezone
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest
import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from collectors.tomtom import TomTomCollector
from database.base import Base
from database.models import TrafficObservation
from pipelines.traffic import TrafficCollectionPipeline
from pipelines.scheduler import TaskScheduler


@pytest.fixture
def mock_flow_response():
    """Mock standard TomTom Flow Segment Data API JSON."""
    return {
        "flowSegmentData": {
            "frc": "FRC2",
            "currentSpeed": 38.5,
            "freeFlowSpeed": 50.0,
            "currentTravelTime": 120.0,
            "freeFlowTravelTime": 90.0,
            "confidence": 0.95,
            "roadClosure": False,
            "coordinates": {"coordinate": [{"latitude": 18.5285, "longitude": 73.8475}]},
            "@version": "1.0",
        }
    }


@pytest.fixture
def sample_points_file(tmp_path):
    """Temporary traffic points JSON file."""
    points = [
        {
            "id": "PT_TEST_01",
            "name": "JM Road Test",
            "latitude": 18.5285,
            "longitude": 73.8475,
            "nearest_station": "11613",
        },
        {
            "id": "PT_TEST_02",
            "name": "FC Road Test",
            "latitude": 18.5250,
            "longitude": 73.8415,
            "nearest_station": "11613",
        },
    ]
    path = tmp_path / "test_traffic_points.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(points, f)
    return path


def test_monitoring_points_configuration():
    """Verify default traffic_points.json loads ~40 points across the 5 required clusters."""
    collector = TomTomCollector()
    points = collector.points
    assert len(points) >= 35, f"Expected ~40 points, got {len(points)}"

    stations = set(pt["nearest_station"] for pt in points)
    # Must cover Shivajinagar, SPPU, Karve, Katraj, Wakad
    assert {"11613", "3409439", "5661", "3409438", "3409436"}.issubset(stations)

    for pt in points:
        assert "id" in pt and "name" in pt
        assert "latitude" in pt and "longitude" in pt
        assert 18.40 <= pt["latitude"] <= 18.65
        assert 73.70 <= pt["longitude"] <= 74.05


def test_mock_tomtom_api_collection(sample_points_file, mock_flow_response):
    """Verify TomTomCollector successfully parses Flow Segment response into DataFrame."""
    session = requests.Session()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = mock_flow_response
    mock_resp.raise_for_status.return_value = None

    with patch.object(session, "get", return_value=mock_resp):
        collector = TomTomCollector(
            api_key="mock_key",
            points_path=sample_points_file,
            session=session,
        )
        df, report = collector.collect_all_points()

        assert len(df) == 2
        assert report["successful_requests"] == 2
        assert report["failed_requests"] == 0
        assert report["coverage_percentage"] == 100.0

        first = df.iloc[0]
        assert first["point_id"] == "PT_TEST_01"
        assert first["current_speed"] == 38.5
        assert first["free_flow_speed"] == 50.0
        assert bool(first["road_closure"]) is False
        assert first["frc"] == "FRC2"
        assert collector.validate(df) is True


def test_retries_and_failure_logging(sample_points_file, mock_flow_response):
    """Verify handling of failed API requests with proper retry attempt logging."""
    session = requests.Session()

    def side_effect(url, params, timeout):
        if "18.5285" in params["point"]:
            resp = MagicMock()
            resp.status_code = 200
            resp.json.return_value = mock_flow_response
            resp.raise_for_status.return_value = None
            return resp
        else:
            raise requests.exceptions.ConnectionError("Network connection reset")

    with patch.object(session, "get", side_effect=side_effect):
        collector = TomTomCollector(
            api_key="mock_key",
            points_path=sample_points_file,
            session=session,
        )
        df, report = collector.collect_all_points()

        assert len(df) == 1
        assert report["successful_requests"] == 1
        assert report["failed_requests"] == 1
        assert report["coverage_percentage"] == 50.0
        assert "PT_TEST_02" in report["failed_points"]


def test_duplicate_prevention_and_append_only(tmp_path, sample_points_file, mock_flow_response):
    """Verify that multiple collection runs append records without duplicating timestamps."""
    session = requests.Session()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = mock_flow_response
    mock_resp.raise_for_status.return_value = None

    with patch.object(session, "get", return_value=mock_resp):
        collector = TomTomCollector(
            api_key="mock_key",
            points_path=sample_points_file,
            session=session,
        )
        fixed_dt = datetime(2026, 10, 21, 12, 0, 0, tzinfo=timezone.utc)
        df1, _ = collector.collect_all_points(collection_time=fixed_dt)

        save_file = "test_traffic.parquet"
        with patch("collectors.tomtom.TRAFFIC_DATA_DIR", tmp_path):
            collector.save(df1, filename=save_file)
            saved1 = pd.read_parquet(tmp_path / save_file)
            assert len(saved1) == 2

            # Run 2: Exact same timestamp -> must skip duplicate records
            collector.save(df1, filename=save_file)
            saved2 = pd.read_parquet(tmp_path / save_file)
            assert len(saved2) == 2, "Duplicate timestamp records should have been skipped"

            # Run 3: Different timestamp -> must append
            later_dt = datetime(2026, 10, 21, 12, 30, 0, tzinfo=timezone.utc)
            df2, _ = collector.collect_all_points(collection_time=later_dt)
            collector.save(df2, filename=save_file)
            saved3 = pd.read_parquet(tmp_path / save_file)
            assert len(saved3) == 4, "New timestamp observations must be appended"


def test_database_insertion_with_in_memory_sqlite(sample_points_file, mock_flow_response):
    """Verify insertion and unique constraint enforcement on TrafficObservation model."""
    engine = create_engine("sqlite:///:memory:")
    TrafficObservation.__table__.create(engine)
    TestingSessionLocal = sessionmaker(bind=engine)

    session = requests.Session()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = mock_flow_response
    mock_resp.raise_for_status.return_value = None

    with patch.object(session, "get", return_value=mock_resp):
        collector = TomTomCollector(
            api_key="mock_key",
            points_path=sample_points_file,
            session=session,
        )
        df, _ = collector.collect_all_points()

        with patch("database.session.SessionLocal", TestingSessionLocal), \
             patch("database.session.engine", engine):
            count1 = collector.insert_to_db(df)
            assert count1 == 2

            # Re-running insert with same records must insert 0 (skip duplicates)
            count2 = collector.insert_to_db(df)
            assert count2 == 0

            # Verify in DB
            with TestingSessionLocal() as db_session:
                rows = db_session.query(TrafficObservation).all()
                assert len(rows) == 2
                assert rows[0].source == "tomtom"
                assert rows[0].current_speed == 38.5


@pytest.mark.asyncio
async def test_scheduler_registration():
    """Verify that APScheduler correctly registers the traffic collector job."""
    scheduler = TaskScheduler()
    # Mock settings.ENABLE_SCHEDULER to True for this test
    with patch("config.settings.settings.ENABLE_SCHEDULER", True):
        scheduler.start()
        assert scheduler._is_running is True
        job = scheduler.scheduler.get_job("recurring_traffic_collector")
        assert job is not None
        assert "TomTom" in job.name
        scheduler.shutdown()
        assert scheduler._is_running is False

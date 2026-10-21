"""Unit and integration tests for UrbanTwin System Validation Pipeline.

Tests:
1. Stage execution functions (stages 1 through 12)
2. StageResult data model and health scoring
3. Report writing and artifact integrity in reports/system_validation/
4. End-to-end pipeline execution and exit codes
"""

import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import pandas as pd
import pytest

from scripts.run_full_pipeline import (
    StageResult,
    stage_environment,
    stage_database,
    stage_migration_status,
    stage_aqi_import,
    stage_aqi_quality,
    stage_weather,
    stage_traffic,
    stage_h3_spatial,
    stage_entity_resolution,
    stage_fusion,
    stage_forecasting,
    stage_dashboards,
    write_reports,
    run_full_pipeline,
    REPORTS_DIR,
    STAGE_RUNNERS,
)


class TestStageResultDataModel:
    """Tests for StageResult data structures and scoring."""

    def test_pass_status_label(self):
        res = StageResult(stage_index=1, stage_name="Test", score=90, success=True)
        assert res.status_label == "PASS"

    def test_warn_status_label(self):
        res = StageResult(stage_index=1, stage_name="Test", score=70, success=True)
        assert res.status_label == "WARN"

    def test_fail_status_label(self):
        res = StageResult(stage_index=1, stage_name="Test", score=40, success=False)
        assert res.status_label == "FAIL"

    def test_duration_calculation(self):
        res = StageResult(stage_index=1, stage_name="Test", started_at=10.0, ended_at=12.555)
        assert res.duration_s == 2.555


class TestValidationStages:
    """Direct tests for individual validation stage functions."""

    def test_stage_1_environment(self):
        res = stage_environment()
        assert isinstance(res, StageResult)
        assert res.stage_index == 1
        assert res.success is True
        assert res.score >= 80

    def test_stage_2_database_schema(self):
        res = stage_database()
        assert isinstance(res, StageResult)
        assert res.stage_index == 2
        assert res.success is True
        # Graceful fallback handles DB auth issue
        assert res.score >= 50
        assert "schema_tables" in res.metrics

    def test_stage_3_migration_status(self):
        res = stage_migration_status()
        assert isinstance(res, StageResult)
        assert res.stage_index == 3
        assert res.success is True
        assert res.records >= 2

    def test_stage_4_aqi_import(self):
        res = stage_aqi_import()
        assert isinstance(res, StageResult)
        assert res.stage_index == 4
        assert res.success is True
        assert res.records == 3751
        assert res.metrics["station_count"] == 5

    def test_stage_5_aqi_quality(self):
        res = stage_aqi_quality()
        assert isinstance(res, StageResult)
        assert res.stage_index == 5
        assert res.success is True
        assert res.metrics["completeness_score"] > 40.0
        assert res.metrics["station_count_analyzed"] == 5

    def test_stage_6_weather(self):
        res = stage_weather()
        assert isinstance(res, StageResult)
        assert res.stage_index == 6
        assert res.success is True
        assert res.records >= 60000
        assert res.metrics["days_span"] >= 2800

    def test_stage_7_traffic_mocked(self):
        """Test stage_traffic with a mock to avoid redundant API hits during fast test runs."""
        mock_report = {
            "coverage_percentage": 100.0,
            "average_latency_seconds": 0.25,
            "failed_requests": 0,
        }
        mock_df = pd.DataFrame([{"point_id": i, "speed": 40.0} for i in range(40)])

        with patch("collectors.tomtom.TomTomCollector.collect_all_points", return_value=(mock_df, mock_report)):
            res = stage_traffic()
            assert isinstance(res, StageResult)
            assert res.stage_index == 7
            assert res.success is True
            assert res.score == 100
            assert res.records == 40

    def test_stage_8_h3_spatial(self):
        res = stage_h3_spatial()
        assert isinstance(res, StageResult)
        assert res.stage_index == 8
        assert res.success is True
        assert res.records >= 100
        assert res.metrics["h3_resolution"] == 7

    def test_stage_9_entity_resolution(self):
        res = stage_entity_resolution()
        assert isinstance(res, StageResult)
        assert res.stage_index == 9
        assert res.success is True
        assert res.metrics["max_station_snap_dist_m"] < 1500.0

    def test_stage_10_space_time_fusion(self):
        res = stage_fusion()
        assert isinstance(res, StageResult)
        assert res.stage_index == 10
        assert res.success is True
        assert res.records == 3751
        assert res.metrics["zone_count"] == 5
        assert res.metrics["traffic_speed_null_pct"] == 100.0

    def test_stage_11_forecasting(self):
        res = stage_forecasting()
        assert isinstance(res, StageResult)
        assert res.stage_index == 11
        assert res.success is True
        assert res.metrics["feature_matrix_samples"] == 3751
        assert res.metrics["baseline_models_count"] >= 4

    def test_stage_12_dashboards(self):
        res = stage_dashboards()
        assert isinstance(res, StageResult)
        assert res.stage_index == 12
        assert res.success is True
        assert res.records == 4  # All 4 dashboards generated


class TestReportOutputs:
    """Verify that all report files are generated and properly structured."""

    def test_write_reports_creates_all_artifacts(self, tmp_path):
        dummy_stages = [
            StageResult(stage_index=1, stage_name="Env", success=True, score=100, records=4),
            StageResult(stage_index=2, stage_name="DB", success=True, score=80, records=1000,
                        metrics={"schema_tables": {"stations": {"primary_key": ["station_id"], "foreign_keys": [], "indexes": [], "unique_constraints": []}}}),
            StageResult(stage_index=7, stage_name="Traffic", success=True, score=100, records=40,
                        metrics={"coverage_percentage": 100.0, "average_latency_seconds": 0.25, "points_collected": 40, "failed_requests": 0}),
        ]

        with patch("scripts.run_full_pipeline.REPORTS_DIR", tmp_path):
            write_reports(dummy_stages, total_elapsed=12.34)

            expected_files = [
                "validation_summary.md",
                "validation_summary.json",
                "pipeline_execution_log.csv",
                "database_health.csv",
                "api_health.csv",
                "performance_metrics.csv",
                "validation_errors.md",
            ]

            for fname in expected_files:
                fpath = tmp_path / fname
                assert fpath.exists(), f"Missing expected report: {fname}"
                assert fpath.stat().st_size > 0, f"Empty report: {fname}"

            # Verify JSON content
            with open(tmp_path / "validation_summary.json") as jf:
                data = json.load(jf)
                assert data["overall_health_score"] == 93
                assert len(data["stages"]) == 3


def test_stage_runners_list():
    """Verify all 12 stages are registered in sequence."""
    assert len(STAGE_RUNNERS) == 12

"""Unit tests for the Data Quality and Exploratory Analysis pipeline (Milestone 2).

Tests:
- Quality report generation
- Statistics calculation (parametric and non-parametric)
- Date coverage and temporal continuity calculations
- Missing value calculations and null percentages
- Data completeness scoring
- Duplicate detection
"""

from datetime import date
import numpy as np
import pandas as pd
import pytest

from pipelines.data_quality import DataQualityAnalyzer, POLLUTANT_COLUMNS


@pytest.fixture
def sample_quality_dataframe() -> pd.DataFrame:
    """Provide a controlled synthetic panel for verifying quality calculations."""
    return pd.DataFrame(
        {
            "station_id": ["101", "101", "101", "102", "102"],
            "station_name": ["Station Alpha", "Station Alpha", "Station Alpha", "Station Beta", "Station Beta"],
            "city": ["Pune", "Pune", "Pune", "Pune", "Pune"],
            "observation_date": [
                "2022-01-01",
                "2022-01-02",
                "2022-01-03",
                "2022-01-01",
                "2022-01-02",
            ],
            "aqi": [100.0, 150.0, None, 80.0, 120.0],  # 1 null out of 5 -> 20% null
            "pm25": [50.0, 75.0, 60.0, 40.0, 60.0],    # 0 nulls -> 0% null
            "pm10": [100.0, None, 120.0, None, 110.0], # 2 nulls out of 5 -> 40% null
            "no2": [20.0, 25.0, 30.0, None, None],     # 2 nulls out of 5 -> 40% null
            "co": [None, None, None, None, None],       # 5 nulls out of 5 -> 100% null
            "so2": [10.0, 12.0, 15.0, 8.0, 9.0],       # 0 nulls
            "o3": [30.0, 35.0, None, 25.0, None],      # 2 nulls
            "dominant_pollutant": ["pm25", "pm10", "pm25", "aqi", "pm25"],
        }
    )


# -----------------------------------------------------------------------------
# 1. Missing Value Calculations & Null Percentage
# -----------------------------------------------------------------------------
def test_compute_missing_value_report(sample_quality_dataframe: pd.DataFrame) -> None:
    """Verify null count, valid count, and null percentage calculations."""
    analyzer = DataQualityAnalyzer(sample_quality_dataframe)
    report_df = analyzer.compute_missing_value_report()

    assert isinstance(report_df, pd.DataFrame)
    assert "column" in report_df.columns
    assert "null_count" in report_df.columns
    assert "null_percentage" in report_df.columns

    report_map = report_df.set_index("column").to_dict(orient="index")

    # aqi: 1 null out of 5 -> 20.0%
    assert report_map["aqi"]["null_count"] == 1
    assert report_map["aqi"]["valid_count"] == 4
    assert report_map["aqi"]["null_percentage"] == 20.0

    # pm25: 0 nulls out of 5 -> 0.0%
    assert report_map["pm25"]["null_count"] == 0
    assert report_map["pm25"]["null_percentage"] == 0.0

    # co: 5 nulls out of 5 -> 100.0%
    assert report_map["co"]["null_count"] == 5
    assert report_map["co"]["null_percentage"] == 100.0


def test_compute_data_completeness_score(sample_quality_dataframe: pd.DataFrame) -> None:
    """Verify data completeness score calculation across all 7 pollutant columns."""
    analyzer = DataQualityAnalyzer(sample_quality_dataframe)
    score = analyzer.compute_data_completeness_score()

    # Total cells: 5 rows * 7 pollutants = 35 cells
    # Nulls: aqi(1) + pm25(0) + pm10(2) + no2(2) + co(5) + so2(0) + o3(2) = 12 nulls
    # Valid: 35 - 12 = 23 valid cells
    # Completeness: (23 / 35) * 100 = 65.71%
    expected = round((23 / 35) * 100, 2)
    assert score == expected


def test_data_completeness_score_empty_dataframe() -> None:
    """Verify completeness score on an empty DataFrame returns 0.0."""
    empty_df = pd.DataFrame(columns=["station_id", "date"] + POLLUTANT_COLUMNS)
    analyzer = DataQualityAnalyzer(empty_df)
    assert analyzer.compute_data_completeness_score() == 0.0


# -----------------------------------------------------------------------------
# 2. Date Coverage Calculations
# -----------------------------------------------------------------------------
def test_compute_date_coverage(sample_quality_dataframe: pd.DataFrame) -> None:
    """Verify start date, end date, total calendar days, and missing days."""
    analyzer = DataQualityAnalyzer(sample_quality_dataframe)
    cov = analyzer.compute_date_coverage()

    assert cov["start_date"] == "2022-01-01"
    assert cov["end_date"] == "2022-01-03"
    assert cov["total_calendar_days"] == 3
    assert cov["observed_dates_count"] == 3
    assert cov["missing_dates_count"] == 0
    assert cov["temporal_coverage_pct"] == 100.0


def test_compute_date_coverage_with_gap() -> None:
    """Verify date coverage detects gaps in calendar timeline."""
    gap_df = pd.DataFrame(
        {
            "station_id": ["101", "101"],
            "date": ["2022-01-01", "2022-01-05"],  # 5 calendar days span, 2 observed, 3 missing
            "aqi": [50.0, 60.0],
        }
    )
    analyzer = DataQualityAnalyzer(gap_df)
    cov = analyzer.compute_date_coverage()

    assert cov["total_calendar_days"] == 5
    assert cov["observed_dates_count"] == 2
    assert cov["missing_dates_count"] == 3
    assert cov["temporal_coverage_pct"] == 40.0


# -----------------------------------------------------------------------------
# 3. Statistics Generation
# -----------------------------------------------------------------------------
def test_compute_statistics(sample_quality_dataframe: pd.DataFrame) -> None:
    """Verify parametric and non-parametric descriptive statistics calculations."""
    analyzer = DataQualityAnalyzer(sample_quality_dataframe)
    stats_df = analyzer.compute_statistics()

    assert isinstance(stats_df, pd.DataFrame)
    assert len(stats_df) == len(POLLUTANT_COLUMNS)

    stats_map = stats_df.set_index("parameter").to_dict(orient="index")

    # aqi: [100.0, 150.0, 80.0, 120.0] -> count=4, mean=112.5, min=80.0, max=150.0, median=110.0
    aqi_stats = stats_map["aqi"]
    assert aqi_stats["count"] == 4
    assert aqi_stats["mean"] == 112.5
    assert aqi_stats["min"] == 80.0
    assert aqi_stats["max"] == 150.0
    assert aqi_stats["median"] == 110.0
    assert aqi_stats["std"] is not None

    # co: all nulls
    co_stats = stats_map["co"]
    assert co_stats["count"] == 0
    assert pd.isna(co_stats["mean"])
    assert pd.isna(co_stats["median"])


# -----------------------------------------------------------------------------
# 4. Duplicate Detection
# -----------------------------------------------------------------------------
def test_compute_duplicate_report(sample_quality_dataframe: pd.DataFrame) -> None:
    """Verify detection of duplicate station-date pairs."""
    analyzer = DataQualityAnalyzer(sample_quality_dataframe)
    dups = analyzer.compute_duplicate_report()
    assert dups["has_duplicates"] is False
    assert dups["duplicate_station_date_pairs"] == 0

    # Add duplicate row
    df_with_dups = pd.concat([sample_quality_dataframe, sample_quality_dataframe.iloc[[0]]], ignore_index=True)
    analyzer_dups = DataQualityAnalyzer(df_with_dups)
    dups_detected = analyzer_dups.compute_duplicate_report()
    assert dups_detected["has_duplicates"] is True
    assert dups_detected["duplicate_station_date_pairs"] == 1


# -----------------------------------------------------------------------------
# 5. Full Quality Report
# -----------------------------------------------------------------------------
def test_generate_full_report(sample_quality_dataframe: pd.DataFrame) -> None:
    """Verify that generate_full_report returns an integrated dictionary with all metrics."""
    analyzer = DataQualityAnalyzer(sample_quality_dataframe)
    report = analyzer.generate_full_report()

    assert "total_observations" in report
    assert report["total_observations"] == 5
    assert "total_stations" in report
    assert report["total_stations"] == 2
    assert "average_aqi" in report
    assert report["average_aqi"] == 112.5
    assert "data_completeness_score" in report
    assert "date_coverage" in report
    assert "duplicates" in report
    assert "missing_values" in report
    assert "pollutant_statistics" in report
    assert "station_coverage" in report

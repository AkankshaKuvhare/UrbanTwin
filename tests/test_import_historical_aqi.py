"""Unit tests for the historical AQI importer pipeline (CongestAir module).

Covers:
- CSV schema validation
- Date parsing edge cases
- Numeric pollutant cleaning and invalid value nullification
- Duplicate handling and in-memory deduplication
- Database insertion and idempotent re-runs
"""

from datetime import date
from pathlib import Path
import tempfile
import numpy as np
import pandas as pd
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from collectors.import_historical_aqi import (
    HistoricalAQIImporter,
    clean_numeric_value,
    parse_observation_date,
    validate_csv_schema,
)
from database.base import Base
from database.models import AQIObservation, Station


# -----------------------------------------------------------------------------
# 1. CSV Schema Validation Tests
# -----------------------------------------------------------------------------
def test_validate_csv_schema_success() -> None:
    """Verify that a DataFrame containing all required columns passes validation."""
    valid_df = pd.DataFrame(
        {
            "city": ["Pune"],
            "station_name": ["Shivajinagar"],
            "station_id": ["11613"],
            "date": ["2020-11-13"],
            "aqi": [112.9],
            "pm25": [45.0],
            "pm10": [118.9],
        }
    )
    is_valid, missing = validate_csv_schema(valid_df)
    assert is_valid is True
    assert missing == []


def test_validate_csv_schema_missing_columns() -> None:
    """Verify that missing mandatory columns are detected and reported."""
    invalid_df = pd.DataFrame(
        {
            "city": ["Pune"],
            "aqi": [100.0],
            # missing: station_name, station_id, date
        }
    )
    is_valid, missing = validate_csv_schema(invalid_df)
    assert is_valid is False
    assert "station_name" in missing
    assert "station_id" in missing
    assert "date" in missing


# -----------------------------------------------------------------------------
# 2. Date Parsing Tests
# -----------------------------------------------------------------------------
@pytest.mark.parametrize(
    "raw_input, expected_date",
    [
        ("2020-11-13", date(2020, 11, 13)),
        ("2021-01-01 00:00:00", date(2021, 1, 1)),
        (date(2022, 5, 20), date(2022, 5, 20)),
        ("2026-10-21", date(2026, 10, 21)),
    ],
)
def test_parse_observation_date_valid(raw_input, expected_date) -> None:
    """Verify valid date formats parse to datetime.date."""
    assert parse_observation_date(raw_input) == expected_date


@pytest.mark.parametrize(
    "invalid_input",
    [
        "not-a-date",
        "",
        "   ",
        None,
        float("nan"),
        "9999-99-99",
    ],
)
def test_parse_observation_date_invalid(invalid_input) -> None:
    """Verify invalid date representations return None safely."""
    assert parse_observation_date(invalid_input) is None


# -----------------------------------------------------------------------------
# 3. Numeric Cleaning & Nullification Tests
# -----------------------------------------------------------------------------
def test_clean_numeric_value_valid() -> None:
    """Verify valid non-negative numbers are preserved."""
    val, nullified = clean_numeric_value(45.67)
    assert val == 45.67
    assert nullified is False

    # Zero is physically valid
    val_zero, nullified_zero = clean_numeric_value(0.0)
    assert val_zero == 0.0
    assert nullified_zero is False

    # String float
    val_str, _ = clean_numeric_value("128.5")
    assert val_str == 128.5


def test_clean_numeric_value_negative_nullified() -> None:
    """Verify negative pollutant values are replaced with None and flagged as nullified."""
    val, nullified = clean_numeric_value(-15.4)
    assert val is None
    assert nullified is True

    val_str_neg, nullified_str_neg = clean_numeric_value("-999")
    assert val_str_neg is None
    assert nullified_str_neg is True


def test_clean_numeric_value_non_numeric_and_empty() -> None:
    """Verify non-numeric values, NaN, and empty strings are converted to None."""
    val, nullified = clean_numeric_value("N/A")
    assert val is None
    assert nullified is False

    val_empty, _ = clean_numeric_value("")
    assert val_empty is None

    val_nan, _ = clean_numeric_value(np.nan)
    assert val_nan is None

    val_corrupt, nullified_corrupt = clean_numeric_value("corrupt_sensor_string")
    assert val_corrupt is None
    assert nullified_corrupt is True


# -----------------------------------------------------------------------------
# 4. Duplicate Handling Tests
# -----------------------------------------------------------------------------
def test_duplicate_handling_in_memory() -> None:
    """Verify in-memory preparation handles duplicated (station_id, date) rows gracefully."""
    df_with_dupes = pd.DataFrame(
        {
            "city": ["Pune", "Pune", "Pune"],
            "station_name": ["Shivajinagar", "Shivajinagar", "Shivajinagar"],
            "station_id": ["11613", "11613", "11613"],
            "date": ["2020-11-13", "2020-11-13", "2020-11-14"],  # First two are duplicates
            "aqi": [112.9, 115.0, 95.0],
            "pm25": [45.0, 46.0, 30.0],
        }
    )

    importer = HistoricalAQIImporter(db_url="sqlite:///:memory:")
    stations, observations, stats = importer.prepare_data(df_with_dupes)

    # Only 1 unique station
    assert len(stations) == 1
    assert stations[0]["station_id"] == "11613"

    # Only 2 unique observations (first duplicate dropped)
    assert len(observations) == 2
    assert stats["duplicate_records_in_csv"] == 1


# -----------------------------------------------------------------------------
# 5. Database Insert & Idempotency Tests
# -----------------------------------------------------------------------------
@pytest.fixture
def sqlite_test_db():
    """Create a temporary SQLite database for testing insertion and idempotency."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    db_url = f"sqlite:///{db_path}"
    engine = create_engine(db_url)
    Base.metadata.create_all(engine, tables=[Station.__table__, AQIObservation.__table__])

    yield db_url, engine

    # Cleanup
    engine.dispose()
    try:
        Path(db_path).unlink(missing_ok=True)
    except Exception:
        pass


def test_database_insert_and_idempotency(sqlite_test_db, tmp_path) -> None:
    """Verify that records are inserted correctly and running again is strictly idempotent."""
    db_url, engine = sqlite_test_db

    sample_csv = tmp_path / "test_aqi.csv"
    sample_df = pd.DataFrame(
        {
            "city": ["Pune", "Pune", "Pune"],
            "station_name": ["Shivajinagar", "Shivajinagar", "Karve Road"],
            "station_id": ["11613", "11613", "5661"],
            "date": ["2020-11-13", "2020-11-14", "2020-11-13"],
            "co": [None, 1.2, -5.0],  # -5.0 will be nullified
            "no2": [15.2, 18.4, 22.1],
            "o3": [30.0, 28.5, None],
            "pm10": [118.9, 161.1, 99.6],
            "pm25": [45.0, 85.4, 68.3],
            "so2": [8.2, 7.5, 9.1],
            "aqi": [112.9, 184.4, 126.0],
            "dominant_pollutant": ["pm10", "pm25", "pm25"],
        }
    )
    sample_df.to_csv(sample_csv, index=False)

    log_dir = tmp_path / "logs"
    importer = HistoricalAQIImporter(db_url=db_url, log_dir=log_dir)

    # First run
    summary_1 = importer.run(sample_csv)
    assert summary_1["status"] == "success"
    assert summary_1["stations_inserted"] == 2
    assert summary_1["observations_inserted"] == 3
    assert summary_1["invalid_values_nullified"] == 1  # -5.0 nullified

    # Verify rows in DB
    with Session(engine) as session:
        stations = session.scalars(select(Station)).all()
        assert len(stations) == 2

        observations = session.scalars(select(AQIObservation)).all()
        assert len(observations) == 3

        # Check nullified co on Karve Road
        karve_obs = session.scalar(
            select(AQIObservation).where(AQIObservation.station_id == "5661")
        )
        assert karve_obs.co is None
        assert karve_obs.aqi == 126.0
        assert karve_obs.dominant_pollutant == "pm25"

    # Second run (Idempotent test on identical dataset)
    summary_2 = importer.run(sample_csv)
    assert summary_2["status"] == "success"
    # No new stations or observations should be added
    with Session(engine) as session:
        stations_after = session.scalars(select(Station)).all()
        assert len(stations_after) == 2

        obs_after = session.scalars(select(AQIObservation)).all()
        assert len(obs_after) == 3

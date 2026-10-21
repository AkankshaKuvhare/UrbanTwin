"""Unit tests for the Open-Meteo Weather Collector."""

from datetime import date, datetime
from pathlib import Path
import tempfile
import numpy as np
import pandas as pd
import pytest

from collectors.openmeteo import OpenMeteoCollector


def test_openmeteo_collector_initialization() -> None:
    """Verify collector initialization and default properties."""
    collector = OpenMeteoCollector()
    assert collector.source_name == "openmeteo"
    assert collector.cache_dir.exists()


def test_openmeteo_validate_valid_dataframe() -> None:
    """Verify physical climatological validation passes on realistic data."""
    collector = OpenMeteoCollector()
    sample_df = pd.DataFrame(
        {
            "timestamp": pd.date_range("2022-01-01", periods=24, freq="h"),
            "date": [date(2022, 1, 1)] * 24,
            "hour": list(range(24)),
            "latitude": [18.5204] * 24,
            "longitude": [73.8567] * 24,
            "elevation_m": [560.0] * 24,
            "temperature_c": [22.5] * 24,
            "relative_humidity": [55.0] * 24,
            "precipitation_mm": [0.0] * 24,
            "wind_speed_ms": [3.2] * 24,
            "wind_direction_deg": [180.0] * 24,
            "surface_pressure_hpa": [950.0] * 24,
            "boundary_layer_height_m": [800.0] * 24,
        }
    )
    assert collector.validate(sample_df) is True


def test_openmeteo_validate_negative_wind_speed_raises() -> None:
    """Verify negative wind speed triggers a validation error."""
    collector = OpenMeteoCollector()
    invalid_df = pd.DataFrame(
        {
            "temperature_c": [25.0],
            "relative_humidity": [50.0],
            "wind_speed_ms": [-5.0],  # Impossible negative speed
            "boundary_layer_height_m": [500.0],
        }
    )
    with pytest.raises(ValueError, match="negative wind speed"):
        collector.validate(invalid_df)


def test_openmeteo_save_persists_csv_and_parquet(tmp_path) -> None:
    """Verify save method persists both parquet and csv files."""
    collector = OpenMeteoCollector()
    collector.output_dir = tmp_path

    sample_df = pd.DataFrame(
        {
            "timestamp": pd.date_range("2022-01-01", periods=5, freq="h"),
            "date": [date(2022, 1, 1)] * 5,
            "temperature_c": [20.0, 21.0, 22.0, 23.0, 24.0],
            "relative_humidity": [60.0, 58.0, 55.0, 52.0, 50.0],
            "wind_speed_ms": [2.0, 2.5, 3.0, 3.5, 4.0],
            "boundary_layer_height_m": [400.0, 500.0, 600.0, 700.0, 800.0],
        }
    )

    saved_parquet = collector.save(sample_df, filename="test_weather")
    assert saved_parquet.exists()
    assert (tmp_path / "test_weather.csv").exists()

    loaded_df = pd.read_parquet(saved_parquet)
    assert len(loaded_df) == 5
    assert "temperature_c" in loaded_df.columns

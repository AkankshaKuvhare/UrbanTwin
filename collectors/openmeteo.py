"""Collector for Open-Meteo Historical Meteorological Data.

Acquires hourly weather covariates (temperature, relative humidity, precipitation,
wind speed, wind direction, surface pressure, boundary layer height) for Pune, India
using the official Open-Meteo SDK with persistent caching and retry resilience.
"""

import argparse
from datetime import datetime
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Union

import numpy as np
import openmeteo_requests
import pandas as pd
import requests_cache
from retry_requests import retry

# Ensure project root is in sys.path when executed directly as a script
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from collectors.base import BaseCollector
from config.logging import get_logger
from config.settings import DataMode, settings

logger = get_logger(__name__)

PUNE_DEFAULT_LAT = 18.5204
PUNE_DEFAULT_LON = 73.8567
OPENMETEO_ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"

HOURLY_VARIABLES = [
    "temperature_2m",
    "relative_humidity_2m",
    "precipitation",
    "wind_speed_10m",
    "wind_direction_10m",
    "surface_pressure",
    "boundary_layer_height",
]


class OpenMeteoCollector(BaseCollector):
    """Production collector for Open-Meteo ERA5 / ECMWF reanalysis weather archive."""

    def __init__(
        self,
        data_mode: Optional[DataMode] = None,
        cache_dir: Optional[Union[str, Path]] = None,
    ) -> None:
        super().__init__(data_mode=data_mode)
        self.cache_dir = Path(cache_dir) if cache_dir else settings.BASE_DIR / ".cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup cached session with retry logic
        self.cache_session = requests_cache.CachedSession(
            str(self.cache_dir / "openmeteo_cache"),
            expire_after=-1,  # Historical archive data is immutable
        )
        self.retry_session = retry(self.cache_session, retries=5, backoff_factor=0.2)
        self.client = openmeteo_requests.Client(session=self.retry_session)

    @property
    def source_name(self) -> str:
        return "openmeteo"

    def fetch_raw(
        self,
        start_time: datetime,
        end_time: datetime,
        **kwargs: Any,
    ) -> Any:
        """Fetch raw hourly meteorological data from Open-Meteo archive API.

        Args:
            start_time: Beginning of historical date range.
            end_time: End of historical date range.
            **kwargs: latitude, longitude, timezone.

        Returns:
            Open-Meteo Response object.
        """
        lat = kwargs.get("latitude", PUNE_DEFAULT_LAT)
        lon = kwargs.get("longitude", PUNE_DEFAULT_LON)
        tz = kwargs.get("timezone", "auto")

        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": start_time.strftime("%Y-%m-%d"),
            "end_date": end_time.strftime("%Y-%m-%d"),
            "hourly": HOURLY_VARIABLES,
            "timezone": tz,
        }

        self.logger.info(
            "Querying Open-Meteo archive API",
            url=OPENMETEO_ARCHIVE_URL,
            latitude=lat,
            longitude=lon,
            start_date=params["start_date"],
            end_date=params["end_date"],
        )

        responses = self.client.weather_api(OPENMETEO_ARCHIVE_URL, params=params)
        if not responses:
            raise ValueError(f"No weather data returned from Open-Meteo for lat={lat}, lon={lon}")

        return responses[0]

    def parse_to_dataframe(self, raw_data: Any) -> pd.DataFrame:
        """Parse raw Open-Meteo protobuf response into a standardized DataFrame.

        Args:
            raw_data: Open-Meteo Response object from fetch_raw.

        Returns:
            Standardized DataFrame with normalized timestamps and weather covariates.
        """
        response = raw_data
        hourly = response.Hourly()

        # Extract timestamps
        time_start = pd.to_datetime(hourly.Time(), unit="s", utc=True)
        time_end = pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True)
        interval = pd.Timedelta(seconds=hourly.Interval())

        tz_raw = response.Timezone()
        tz_str = tz_raw.decode() if isinstance(tz_raw, bytes) else str(tz_raw)

        timestamps = pd.date_range(
            start=time_start,
            end=time_end,
            freq=interval,
            inclusive="left",
        ).tz_convert(tz_str)

        data = {
            "timestamp": timestamps,
            "date": timestamps.date,
            "hour": timestamps.hour,
            "latitude": response.Latitude(),
            "longitude": response.Longitude(),
            "elevation_m": response.Elevation(),
            "temperature_2m": hourly.Variables(0).ValuesAsNumpy(),
            "relative_humidity_2m": hourly.Variables(1).ValuesAsNumpy(),
            "precipitation": hourly.Variables(2).ValuesAsNumpy(),
            "wind_speed_10m": hourly.Variables(3).ValuesAsNumpy(),
            "wind_direction_10m": hourly.Variables(4).ValuesAsNumpy(),
            "surface_pressure": hourly.Variables(5).ValuesAsNumpy(),
            "boundary_layer_height": hourly.Variables(6).ValuesAsNumpy(),
        }

        df = pd.DataFrame(data)

        # Map to common canonical naming convention
        df["temperature_c"] = df["temperature_2m"]
        df["relative_humidity"] = df["relative_humidity_2m"]
        df["precipitation_mm"] = df["precipitation"]
        df["wind_speed_ms"] = df["wind_speed_10m"]
        df["wind_direction_deg"] = df["wind_direction_10m"]
        df["surface_pressure_hpa"] = df["surface_pressure"]
        df["boundary_layer_height_m"] = df["boundary_layer_height"]

        return df

    def validate(self, df: pd.DataFrame) -> bool:
        """Validate weather measurements against physical climatological limits for Pune.

        Raises:
            ValueError if severe physical anomalies are encountered.
        """
        if df.empty:
            raise ValueError("Validation failed: Empty weather DataFrame.")

        # 1. Temperature check (-10C to +60C)
        t_min = df["temperature_c"].min()
        t_max = df["temperature_c"].max()
        if t_min < -10.0 or t_max > 60.0:
            self.logger.warning("Unusual temperature detected", t_min=t_min, t_max=t_max)

        # 2. Relative Humidity (0 to 100%)
        rh_min = df["relative_humidity"].min()
        rh_max = df["relative_humidity"].max()
        if rh_min < 0.0 or rh_max > 100.5:
            self.logger.warning("Relative humidity outside normal bounds", rh_min=rh_min, rh_max=rh_max)

        # 3. Wind Speed (non-negative)
        ws_min = df["wind_speed_ms"].min()
        if ws_min < 0.0:
            raise ValueError(f"Physical anomaly: negative wind speed {ws_min}")

        # 4. Planetary Boundary Layer Height (non-negative)
        blh_min = df["boundary_layer_height_m"].min()
        if blh_min < 0.0:
            self.logger.warning("Negative boundary layer height detected, clipping to 0", blh_min=blh_min)
            df["boundary_layer_height_m"] = df["boundary_layer_height_m"].clip(lower=0.0)

        self.logger.info(
            "Meteorological validation passed",
            total_hourly_records=len(df),
            date_range=f"{df['date'].min()} to {df['date'].max()}",
            mean_temp=round(float(df['temperature_c'].mean()), 2),
            mean_humidity=round(float(df['relative_humidity'].mean()), 2),
        )
        return True

    def save(self, df: pd.DataFrame, filename: Optional[str] = None) -> Path:
        """Persist weather dataset to both CSV and Parquet files.

        Args:
            df: Validated weather DataFrame.
            filename: Base filename without extension (default: pune_historical_weather_hourly).

        Returns:
            Path to saved parquet file.
        """
        base_name = filename or "pune_historical_weather_hourly"
        
        # Save to output_dir (data/real/raw or data/synthetic/raw)
        parquet_path = self.output_dir / f"{base_name}.parquet"
        csv_path = self.output_dir / f"{base_name}.csv"

        df.to_parquet(parquet_path, index=False)
        df.to_csv(csv_path, index=False)

        # Also place a copy directly in data/ for easy discovery
        convenience_csv = settings.BASE_DIR / "data" / f"{base_name}.csv"
        df.to_csv(convenience_csv, index=False)

        self.logger.info(
            "Saved weather observations",
            parquet=str(parquet_path),
            csv=str(csv_path),
            records=len(df),
        )
        return parquet_path


def main() -> None:
    """CLI entrypoint to run historical weather acquisition for Pune."""
    parser = argparse.ArgumentParser(description="UrbanTwin - Open-Meteo Historical Weather Collector")
    parser.add_argument("--latitude", type=float, default=PUNE_DEFAULT_LAT, help="Latitude (default: 18.5204)")
    parser.add_argument("--longitude", type=float, default=PUNE_DEFAULT_LON, help="Longitude (default: 73.8567)")
    parser.add_argument("--start-date", type=str, default="2018-03-09", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", type=str, default="2026-01-28", help="End date (YYYY-MM-DD)")

    args = parser.parse_args()

    start_dt = datetime.strptime(args.start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(args.end_date, "%Y-%m-%d")

    collector = OpenMeteoCollector()
    saved_path = collector.run(
        start_time=start_dt,
        end_time=end_dt,
        latitude=args.latitude,
        longitude=args.longitude,
    )
    print(f"\nSuccessfully collected and saved historical weather data to: {saved_path}")


if __name__ == "__main__":
    main()

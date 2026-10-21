"""Historical AQI Data Importer for UrbanTwin (CongestAir Module).

Reads, validates, cleans, and bulk-ingests historical air quality monitoring CSV
data (e.g., all_stations_combined.csv) into PostgreSQL/SQLite database with
full idempotency and detailed audit logging.
"""

import argparse
from datetime import date, datetime
import math
from pathlib import Path
import sys
import time
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from sqlalchemy import create_engine, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

# Ensure project root is in sys.path when executed directly as a script
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Project imports
from config.settings import settings
from database.base import Base
from database.models import AQIObservation, Station

# Required columns in the historical AQI dataset
REQUIRED_CSV_COLUMNS = [
    "city",
    "station_name",
    "station_id",
    "date",
]

NUMERIC_POLLUTANT_FIELDS = [
    "aqi",
    "pm25",
    "pm10",
    "no2",
    "co",
    "so2",
    "o3",
]


def validate_csv_schema(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """Validate that the incoming DataFrame contains all mandatory columns.

    Args:
        df: Input DataFrame to check.

    Returns:
        Tuple of (is_valid, list of missing columns).
    """
    missing_cols = [col for col in REQUIRED_CSV_COLUMNS if col not in df.columns]
    return (len(missing_cols) == 0, missing_cols)


def clean_numeric_value(val: Any) -> Tuple[Optional[float], bool]:
    """Validate and clean numeric pollutant and AQI values.

    Replaces invalid, unparseable, infinite, or negative (< 0) pollutant values
    with None (SQL NULL).

    Args:
        val: Raw input scalar.

    Returns:
        Tuple of (cleaned_value, was_nullified_due_to_invalidity).
    """
    if val is None or (isinstance(val, (float, np.floating)) and np.isnan(val)):
        return None, False

    if isinstance(val, str):
        val_str = val.strip()
        if not val_str or val_str.lower() in ("nan", "none", "null", "n/a", "-"):
            return None, False
        try:
            val = float(val_str)
        except (ValueError, TypeError):
            return None, True

    try:
        f_val = float(val)
        if math.isnan(f_val) or math.isinf(f_val):
            return None, False
        # Negative concentrations or AQI are physically impossible -> nullify
        if f_val < 0.0:
            return None, True
        return round(f_val, 4), False
    except (ValueError, TypeError):
        return None, True


def parse_observation_date(val: Any) -> Optional[date]:
    """Parse string or timestamp into a Python datetime.date object.

    Args:
        val: Date representation (string 'YYYY-MM-DD' or timestamp).

    Returns:
        datetime.date object if valid, else None.
    """
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return None

    if isinstance(val, date) and not isinstance(val, datetime):
        return val

    if isinstance(val, datetime):
        return val.date()

    val_str = str(val).strip()
    if not val_str:
        return None

    try:
        # Fast path for ISO 'YYYY-MM-DD'
        return datetime.strptime(val_str[:10], "%Y-%m-%d").date()
    except ValueError:
        try:
            # Fallback to pandas robust parser
            dt = pd.to_datetime(val_str, errors="coerce")
            if pd.isna(dt):
                return None
            return dt.date()
        except Exception:
            return None


class HistoricalAQIImporter:
    """Production-grade importer for historical AQI station and observation records."""

    def __init__(
        self,
        db_url: Optional[str] = None,
        log_dir: Optional[Union[str, Path]] = None,
        batch_size: int = 1000,
    ) -> None:
        """Initialize importer with database target and logging configuration.

        Args:
            db_url: Database connection URL (reads settings.DATABASE_URL by default).
            log_dir: Directory where import log files are written.
            batch_size: Bulk insert batch size.
        """
        self.db_url = db_url or settings.DATABASE_URL
        self.batch_size = batch_size
        self.log_dir = Path(log_dir) if log_dir else settings.BASE_DIR / "logs" / "imports"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / f"import_aqi_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        self.engine: Engine = create_engine(self.db_url)
        self.SessionLocal = sessionmaker(bind=self.engine)

    def log(self, message: str) -> None:
        """Write formatted log entry to both stdout and persistent import log file."""
        timestamp = datetime.now().isoformat()
        formatted_message = f"[{timestamp}] {message}"
        print(formatted_message)
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(formatted_message + "\n")
        except Exception as e:
            print(f"Failed to write to log file: {e}", file=sys.stderr)

    def prepare_data(
        self, df: pd.DataFrame
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, int]]:
        """Clean and transform raw DataFrame into station and observation records.

        Args:
            df: Raw DataFrame from all_stations_combined.csv.

        Returns:
            Tuple of (unique_station_records, observation_records, statistics_dict).
        """
        stats = {
            "total_rows_read": len(df),
            "invalid_dates_dropped": 0,
            "invalid_values_nullified": 0,
            "duplicate_records_in_csv": 0,
        }

        # 1. Extract unique stations
        stations_df = (
            df[["station_id", "station_name", "city"]]
            .dropna(subset=["station_id"])
            .copy()
        )
        stations_df["station_id"] = stations_df["station_id"].astype(str).str.strip()
        stations_df["station_name"] = stations_df["station_name"].astype(str).str.strip()
        stations_df["city"] = stations_df["city"].astype(str).str.strip()
        stations_df = stations_df.drop_duplicates(subset=["station_id"])

        station_records: List[Dict[str, Any]] = stations_df.to_dict(orient="records")

        # 2. Extract and clean observations
        observations: List[Dict[str, Any]] = []
        seen_keys = set()

        for idx, row in df.iterrows():
            raw_station_id = row.get("station_id")
            if pd.isna(raw_station_id):
                continue
            station_id = str(raw_station_id).strip()

            obs_date = parse_observation_date(row.get("date"))
            if obs_date is None:
                stats["invalid_dates_dropped"] += 1
                continue

            dedup_key = (station_id, obs_date)
            if dedup_key in seen_keys:
                stats["duplicate_records_in_csv"] += 1
                continue
            seen_keys.add(dedup_key)

            # Clean all pollutant numeric fields
            cleaned_row: Dict[str, Any] = {
                "station_id": station_id,
                "observation_date": obs_date,
            }

            for col in NUMERIC_POLLUTANT_FIELDS:
                if col in row:
                    val, was_nullified = clean_numeric_value(row[col])
                    cleaned_row[col] = val
                    if was_nullified:
                        stats["invalid_values_nullified"] += 1
                else:
                    cleaned_row[col] = None

            # Dominant pollutant string
            dom_pol = row.get("dominant_pollutant")
            if pd.isna(dom_pol) or not str(dom_pol).strip():
                cleaned_row["dominant_pollutant"] = None
            else:
                cleaned_row["dominant_pollutant"] = str(dom_pol).strip()[:64]

            observations.append(cleaned_row)

        return station_records, observations, stats

    def insert_stations_idempotent(self, session: Session, stations: List[Dict[str, Any]]) -> int:
        """Insert stations into the database only once.

        Args:
            session: Active SQLAlchemy session.
            stations: List of station dictionaries.

        Returns:
            Number of newly inserted stations.
        """
        if not stations:
            return 0

        dialect = session.bind.dialect.name if session.bind else "postgresql"
        inserted_count = 0

        if dialect == "postgresql":
            stmt = pg_insert(Station).values(stations)
            stmt = stmt.on_conflict_do_nothing(index_elements=["station_id"])
            res = session.execute(stmt)
            inserted_count = res.rowcount if res.rowcount is not None and res.rowcount >= 0 else len(stations)
        elif dialect == "sqlite":
            stmt = sqlite_insert(Station).values(stations)
            stmt = stmt.on_conflict_do_nothing(index_elements=["station_id"])
            res = session.execute(stmt)
            inserted_count = res.rowcount if res.rowcount is not None and res.rowcount >= 0 else len(stations)
        else:
            # Universal fallback: query existing IDs and insert missing
            existing_ids = set(session.scalars(select(Station.station_id)).all())
            new_stations = [s for s in stations if s["station_id"] not in existing_ids]
            if new_stations:
                session.bulk_insert_mappings(Station, new_stations)
                inserted_count = len(new_stations)

        session.commit()
        return inserted_count

    def insert_observations_idempotent(
        self, session: Session, observations: List[Dict[str, Any]]
    ) -> Tuple[int, int]:
        """Bulk insert AQI observations with idempotent duplicate conflict handling.

        Args:
            session: Active SQLAlchemy session.
            observations: List of cleaned observation dictionaries.

        Returns:
            Tuple of (inserted_count, skipped_count).
        """
        if not observations:
            return 0, 0

        dialect = session.bind.dialect.name if session.bind else "postgresql"
        inserted_total = 0
        skipped_total = 0

        for i in range(0, len(observations), self.batch_size):
            batch = observations[i : i + self.batch_size]

            if dialect == "postgresql":
                stmt = pg_insert(AQIObservation).values(batch)
                stmt = stmt.on_conflict_do_nothing(
                    index_elements=["station_id", "observation_date"]
                )
                res = session.execute(stmt)
                rc = res.rowcount if res.rowcount is not None and res.rowcount >= 0 else len(batch)
                inserted_total += rc
                skipped_total += len(batch) - rc
            elif dialect == "sqlite":
                stmt = sqlite_insert(AQIObservation).values(batch)
                stmt = stmt.on_conflict_do_nothing(
                    index_elements=["station_id", "observation_date"]
                )
                res = session.execute(stmt)
                rc = res.rowcount if res.rowcount is not None and res.rowcount >= 0 else len(batch)
                inserted_total += rc
                skipped_total += len(batch) - rc
            else:
                # Portable query-based fallback
                for rec in batch:
                    exists = session.scalar(
                        select(AQIObservation.id).where(
                            AQIObservation.station_id == rec["station_id"],
                            AQIObservation.observation_date == rec["observation_date"],
                        )
                    )
                    if not exists:
                        session.add(AQIObservation(**rec))
                        inserted_total += 1
                    else:
                        skipped_total += 1

            session.commit()

        return inserted_total, skipped_total

    def run(self, csv_path: Union[str, Path]) -> Dict[str, Any]:
        """Execute full historical ingestion pipeline on target CSV file.

        Args:
            csv_path: Path to all_stations_combined.csv.

        Returns:
            Dictionary containing comprehensive execution summary.
        """
        start_time = time.time()
        csv_file = Path(csv_path)

        self.log(f"Starting historical AQI import from: {csv_file}")

        if not csv_file.exists():
            error_msg = f"Target CSV file not found: {csv_file}"
            self.log(f"ERROR: {error_msg}")
            raise FileNotFoundError(error_msg)

        # 1. Read CSV
        try:
            df = pd.read_csv(csv_file)
            self.log(f"Loaded CSV file with {len(df)} rows and {len(df.columns)} columns.")
        except Exception as exc:
            self.log(f"ERROR: Failed to read CSV: {exc}")
            raise

        # 2. Validate schema
        is_valid, missing_cols = validate_csv_schema(df)
        if not is_valid:
            error_msg = f"CSV validation failed. Missing required columns: {missing_cols}"
            self.log(f"ERROR: {error_msg}")
            raise ValueError(error_msg)

        self.log("CSV schema validation passed successfully.")

        # 3. Clean and prepare data
        station_records, observation_records, prep_stats = self.prepare_data(df)
        self.log(
            f"Prepared data: {len(station_records)} stations, "
            f"{len(observation_records)} valid observations, "
            f"{prep_stats['invalid_values_nullified']} invalid values nullified."
        )

        # 4. Database Ingestion
        Base.metadata.create_all(self.engine, tables=[Station.__table__, AQIObservation.__table__])

        with self.SessionLocal() as session:
            self.log(f"Inserting {len(station_records)} stations idempotently...")
            stations_inserted = self.insert_stations_idempotent(session, station_records)
            self.log(f"Stations inserted: {stations_inserted}")

            self.log(f"Bulk inserting {len(observation_records)} observations...")
            obs_inserted, obs_skipped = self.insert_observations_idempotent(
                session, observation_records
            )
            self.log(f"Observations inserted: {obs_inserted}, skipped (already existed): {obs_skipped}")

        elapsed_time = round(time.time() - start_time, 2)

        summary = {
            "status": "success",
            "csv_path": str(csv_file),
            "log_file": str(self.log_file),
            "total_rows_read": prep_stats["total_rows_read"],
            "stations_processed": len(station_records),
            "stations_inserted": stations_inserted,
            "observations_processed": len(observation_records),
            "observations_inserted": obs_inserted,
            "observations_skipped": obs_skipped,
            "invalid_dates_dropped": prep_stats["invalid_dates_dropped"],
            "invalid_values_nullified": prep_stats["invalid_values_nullified"],
            "elapsed_time_seconds": elapsed_time,
        }

        self.log(f"Historical AQI import completed in {elapsed_time}s. Summary: {summary}")
        return summary


def main() -> None:
    """CLI entrypoint for running historical AQI ingestion."""
    parser = argparse.ArgumentParser(
        description="UrbanTwin - CongestAir Historical AQI Importer"
    )
    parser.add_argument(
        "--csv-path",
        type=str,
        default="data/all_stations_combined.csv",
        help="Path to all_stations_combined.csv (default: data/all_stations_combined.csv)",
    )
    parser.add_argument(
        "--db-url",
        type=str,
        default=None,
        help="Database URL (default: read from .env via settings.DATABASE_URL)",
    )

    args = parser.parse_args()

    target_csv = Path(args.csv_path)
    if not target_csv.exists():
        # Check fallback common paths
        fallback = settings.BASE_DIR / "data" / "real" / "raw" / "all_stations_combined.csv"
        if fallback.exists():
            target_csv = fallback
        else:
            download_fallback = Path.home() / "Downloads" / "all_stations_combined.csv"
            if download_fallback.exists():
                target_csv = download_fallback

    importer = HistoricalAQIImporter(db_url=args.db_url)
    try:
        summary = importer.run(csv_path=target_csv)
        print("\n--- IMPORT SUMMARY ---")
        for k, v in summary.items():
            print(f"  {k}: {v}")
    except Exception as err:
        print(f"\nFATAL: Ingestion failed with error: {err}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

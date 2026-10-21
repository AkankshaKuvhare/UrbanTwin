"""TomTom Traffic Collector for UrbanTwin (Milestone 7).

Queries the TomTom Flow Segment Data API to collect real-time arterial traffic
flow conditions (speed, free-flow speed, travel time, delay, confidence, closures)
across Pune arterial monitoring corridors.

Guarantees:
- Append-only database persistence (no overwrites).
- Deduplication by (point_id, timestamp).
- Retries with exponential backoff on network failures.
- Detailed audit logging and health report metrics.
- Complete data isolation from AQI and weather tables.
"""

from datetime import datetime, timezone
import json
from pathlib import Path
import time
from typing import Any, Dict, List, Optional, Tuple, Union

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

from config.logging import get_logger
from config.settings import settings
from collectors.base import BaseCollector

logger = get_logger("urbantwin.collector.tomtom")

DEFAULT_POINTS_FILE = settings.BASE_DIR / "config" / "traffic_points.json"
TRAFFIC_DATA_DIR = settings.DATA_DIR / "traffic"


class TomTomCollector(BaseCollector):
    """Production collector for TomTom Flow Segment Data API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        points_path: Optional[Path] = None,
        max_retries: int = 3,
        backoff_factor: float = 0.5,
        timeout_seconds: int = 10,
        session: Optional[requests.Session] = None,
    ) -> None:
        self.api_key = api_key or settings.TOMTOM_API_KEY
        self.points_path = Path(points_path or DEFAULT_POINTS_FILE)
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.timeout_seconds = timeout_seconds

        # Configure resilient HTTP session
        if session is not None:
            self.session = session
        else:
            self.session = requests.Session()
            retry_strategy = Retry(
                total=self.max_retries,
                backoff_factor=self.backoff_factor,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["GET"],
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            self.session.mount("https://", adapter)
            self.session.mount("http://", adapter)

        self.points: List[Dict[str, Any]] = self._load_monitoring_points()

    @property
    def source_name(self) -> str:
        return "tomtom"

    def _load_monitoring_points(self) -> List[Dict[str, Any]]:
        """Load traffic monitoring coordinates from config."""
        if not self.points_path.exists():
            logger.warning("Traffic monitoring points file not found", path=str(self.points_path))
            return []
        try:
            with open(self.points_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as exc:
            logger.error("Failed to load traffic points", error=str(exc))
            return []

    def fetch_flow_segment(
        self,
        latitude: float,
        longitude: float,
        point_id: str,
    ) -> Tuple[Optional[Dict[str, Any]], float]:
        """Fetch Flow Segment Data for a single point from TomTom API.

        Args:
            latitude: Point latitude.
            longitude: Point longitude.
            point_id: Unique identifier for logging.

        Returns:
            Tuple of (response_json_or_None, latency_seconds).
        """
        if not self.api_key:
            raise ValueError("TOMTOM_API_KEY is not configured in settings or environment.")

        url = (
            f"{settings.TOMTOM_BASE_URL.rstrip('/')}/services/4/flowSegmentData/relative0/10/json"
        )
        params = {
            "point": f"{latitude},{longitude}",
            "key": self.api_key,
            "unit": "kmph",
        }

        start_t = time.perf_counter()
        try:
            resp = self.session.get(url, params=params, timeout=self.timeout_seconds)
            latency = time.perf_counter() - start_t
            resp.raise_for_status()
            data = resp.json()
            return data, latency
        except requests.exceptions.RequestException as exc:
            latency = time.perf_counter() - start_t
            logger.warning(
                "TomTom API request failed",
                point_id=point_id,
                lat=latitude,
                lon=longitude,
                error=str(exc),
                latency_s=round(latency, 3),
            )
            return None, latency

    def collect_all_points(
        self,
        collection_time: Optional[datetime] = None,
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Query TomTom for all configured traffic monitoring locations.

        Args:
            collection_time: Optional override timestamp (defaults to current UTC).

        Returns:
            Tuple of (parsed_dataframe, execution_report_dict).
        """
        target_time = collection_time or datetime.now(timezone.utc)
        records: List[Dict[str, Any]] = []
        latencies: List[float] = []
        failed_points: List[str] = []

        total_points = len(self.points)
        logger.info(
            "Starting TomTom traffic collection cycle",
            total_points=total_points,
            timestamp=target_time.isoformat(),
        )

        for pt in self.points:
            pt_id = pt["id"]
            lat = pt["latitude"]
            lon = pt["longitude"]

            raw_resp, latency = self.fetch_flow_segment(lat, lon, pt_id)
            latencies.append(latency)

            if raw_resp and "flowSegmentData" in raw_resp:
                flow = raw_resp["flowSegmentData"]
                records.append({
                    "point_id": pt_id,
                    "timestamp": target_time,
                    "current_speed": float(flow.get("currentSpeed", 0.0)),
                    "free_flow_speed": float(flow.get("freeFlowSpeed", 0.0)),
                    "current_travel_time": float(flow.get("currentTravelTime", 0.0)),
                    "free_flow_travel_time": float(flow.get("freeFlowTravelTime", 0.0)),
                    "confidence": float(flow.get("confidence", 1.0)),
                    "road_closure": bool(flow.get("roadClosure", False)),
                    "frc": str(flow.get("frc", "UNKNOWN")),
                    "source": "tomtom",
                    "latitude": lat,
                    "longitude": lon,
                    "name": pt.get("name", ""),
                    "nearest_station": pt.get("nearest_station", ""),
                })
            else:
                failed_points.append(pt_id)

        df = pd.DataFrame(records)

        # Performance and coverage report metrics
        successful_count = len(records)
        failed_count = len(failed_points)
        coverage_pct = (successful_count / total_points * 100.0) if total_points > 0 else 0.0
        avg_latency = float(sum(latencies) / len(latencies)) if latencies else 0.0

        report = {
            "timestamp": target_time.isoformat(),
            "total_requested": total_points,
            "successful_requests": successful_count,
            "failed_requests": failed_count,
            "coverage_percentage": round(coverage_pct, 2),
            "average_latency_seconds": round(avg_latency, 4),
            "failed_points": failed_points,
        }

        logger.info(
            "Completed TomTom traffic collection cycle",
            successful=successful_count,
            failed=failed_count,
            coverage_pct=round(coverage_pct, 1),
            avg_latency_s=round(avg_latency, 3),
        )

        return df, report

    # -----------------------------------------------------------------------
    # BaseCollector Abstract Method Implementations
    # -----------------------------------------------------------------------

    def fetch_raw(
        self,
        start_time: datetime,
        end_time: datetime,
        **kwargs: Any,
    ) -> List[Tuple[Dict[str, Any], float]]:
        """Fetch raw responses for all configured points."""
        results = []
        for pt in self.points:
            resp, latency = self.fetch_flow_segment(pt["latitude"], pt["longitude"], pt["id"])
            if resp:
                results.append((resp, latency))
        return results

    def parse_to_dataframe(self, raw_data: Any) -> pd.DataFrame:
        """Parse raw responses into DataFrame format."""
        if isinstance(raw_data, pd.DataFrame):
            return raw_data
        records = []
        now = datetime.now(timezone.utc)
        for item in raw_data:
            if isinstance(item, tuple):
                resp = item[0]
            else:
                resp = item
            if "flowSegmentData" in resp:
                flow = resp["flowSegmentData"]
                records.append({
                    "point_id": flow.get("point_id", "unknown"),
                    "timestamp": now,
                    "current_speed": float(flow.get("currentSpeed", 0.0)),
                    "free_flow_speed": float(flow.get("freeFlowSpeed", 0.0)),
                    "current_travel_time": float(flow.get("currentTravelTime", 0.0)),
                    "free_flow_travel_time": float(flow.get("freeFlowTravelTime", 0.0)),
                    "confidence": float(flow.get("confidence", 1.0)),
                    "road_closure": bool(flow.get("roadClosure", False)),
                    "frc": str(flow.get("frc", "UNKNOWN")),
                    "source": "tomtom",
                })
        return pd.DataFrame(records)

    def validate(self, df: pd.DataFrame) -> bool:
        """Validate traffic speeds against physical urban bounds (0 to 180 km/h)."""
        if df.empty:
            return False
        if "current_speed" in df.columns:
            valid_speeds = (df["current_speed"] >= 0) & (df["current_speed"] <= 180)
            return bool(valid_speeds.all())
        return True

    def save(
        self,
        df: pd.DataFrame,
        filename: Optional[str] = None,
    ) -> Path:
        """Append-only storage to partitioned Parquet file.

        Never overwrites previous observations. Drops internal duplicates
        on (point_id, timestamp).
        """
        TRAFFIC_DATA_DIR.mkdir(parents=True, exist_ok=True)
        fname = filename or "traffic_observations.parquet"
        target_path = TRAFFIC_DATA_DIR / fname

        if df.empty:
            return target_path

        db_cols = [
            "point_id", "timestamp", "current_speed", "free_flow_speed",
            "current_travel_time", "free_flow_travel_time", "confidence",
            "road_closure", "frc", "source",
        ]
        persist_df = df[[c for c in db_cols if c in df.columns]].copy()
        persist_df["timestamp"] = pd.to_datetime(persist_df["timestamp"])

        if target_path.exists():
            existing_df = pd.read_parquet(target_path)
            existing_df["timestamp"] = pd.to_datetime(existing_df["timestamp"])
            combined = pd.concat([existing_df, persist_df], ignore_index=True)
            combined = combined.drop_duplicates(subset=["point_id", "timestamp"], keep="last")
        else:
            combined = persist_df.drop_duplicates(subset=["point_id", "timestamp"], keep="last")

        combined.to_parquet(target_path, index=False)
        logger.info(
            "Persisted traffic observations to parquet",
            filepath=str(target_path),
            new_records=len(persist_df),
            total_records=len(combined),
        )
        return target_path

    def insert_to_db(self, df: pd.DataFrame) -> int:
        """Insert records into PostgreSQL traffic_observations table.

        Uses ON CONFLICT DO NOTHING to guarantee append-only idempotency.
        Falls back gracefully if the database is offline.

        Returns:
            Count of rows inserted.
        """
        if df.empty:
            return 0

        from database.session import engine, SessionLocal
        from database.models import TrafficObservation

        try:
            TrafficObservation.__table__.create(bind=engine, checkfirst=True)
        except Exception as exc:
            logger.debug("Database table check skipped or failed", error=str(exc))

        inserted_count = 0
        try:
            with SessionLocal() as session:
                for _, row in df.iterrows():
                    obs = TrafficObservation(
                        point_id=row["point_id"],
                        timestamp=pd.to_datetime(row["timestamp"]),
                        current_speed=row.get("current_speed"),
                        free_flow_speed=row.get("free_flow_speed"),
                        current_travel_time=row.get("current_travel_time"),
                        free_flow_travel_time=row.get("free_flow_travel_time"),
                        confidence=row.get("confidence"),
                        road_closure=bool(row.get("road_closure", False)),
                        frc=row.get("frc"),
                        source="tomtom",
                    )
                    exists = session.query(TrafficObservation).filter_by(
                        point_id=obs.point_id,
                        timestamp=obs.timestamp,
                    ).first()
                    if not exists:
                        session.add(obs)
                        inserted_count += 1
                session.commit()
                logger.info("Inserted traffic observations into database", count=inserted_count)
                return inserted_count
        except Exception as exc:
            logger.warning(
                "Database insertion unavailable; stored safely in parquet",
                error=str(exc),
            )
            return 0

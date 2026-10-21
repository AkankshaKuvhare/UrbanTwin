"""Pipeline orchestrator and health reporting for TomTom Traffic Collection (Milestone 7).

Manages execution cycles, audits daily request counts, coverage percentages,
average latencies, and failed requests, and exports JSON and CSV reports.
"""

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from config.logging import get_logger
from config.settings import settings
from collectors.tomtom import TomTomCollector
from pipelines.base import BasePipeline, PipelineResult

logger = get_logger("urbantwin.pipeline.traffic")

REPORTS_DIR = settings.BASE_DIR / "reports" / "traffic"


class TrafficCollectionPipeline(BasePipeline):
    """Pipeline for orchestrated TomTom traffic flow data collection."""

    def __init__(
        self,
        collector: Optional[TomTomCollector] = None,
        reports_dir: Optional[Path] = None,
    ) -> None:
        super().__init__()
        self.collector = collector or TomTomCollector()
        self.reports_dir = Path(reports_dir or REPORTS_DIR)

    @property
    def name(self) -> str:
        return "traffic_collection_stage_7"

    def execute(self, **kwargs: Any) -> PipelineResult:
        """Run single collection cycle across all monitored arterial points."""
        start_time = datetime.now(timezone.utc)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        logger.info("Executing TrafficCollectionPipeline cycle")
        try:
            df, report = self.collector.collect_all_points()

            # 1. Append to parquet storage
            parquet_path = self.collector.save(df)

            # 2. Try inserting into database table
            inserted_db = self.collector.insert_to_db(df)
            report["db_rows_inserted"] = inserted_db

            # 3. Update cumulative daily metrics
            daily_metrics = self._update_daily_reports(report)

            execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()

            return PipelineResult(
                pipeline_name=self.name,
                started_at=start_time,
                completed_at=datetime.now(timezone.utc),
                success=True,
                metrics={
                    "records_collected": len(df),
                    "coverage_percentage": report["coverage_percentage"],
                    "failed_requests": report["failed_requests"],
                    "average_latency_seconds": report["average_latency_seconds"],
                    "db_rows_inserted": inserted_db,
                    "execution_time_seconds": execution_time,
                    "daily_request_count": daily_metrics.get("total_requests", len(df)),
                },
            )
        except Exception as exc:
            logger.error("TrafficCollectionPipeline failed", error=str(exc))
            return PipelineResult(
                pipeline_name=self.name,
                started_at=start_time,
                completed_at=datetime.now(timezone.utc),
                success=False,
                error_message=str(exc),
            )

    def _update_daily_reports(self, cycle_report: Dict[str, Any]) -> Dict[str, Any]:
        """Aggregate and persist daily collection audit logs."""
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        daily_json = self.reports_dir / f"traffic_health_{today_str}.json"
        daily_csv = self.reports_dir / "traffic_collection_history.csv"

        history_record = {
            "timestamp": cycle_report["timestamp"],
            "total_requested": cycle_report["total_requested"],
            "successful_requests": cycle_report["successful_requests"],
            "failed_requests": cycle_report["failed_requests"],
            "coverage_percentage": cycle_report["coverage_percentage"],
            "average_latency_seconds": cycle_report["average_latency_seconds"],
        }

        # Update CSV history
        df_new = pd.DataFrame([history_record])
        if daily_csv.exists():
            df_hist = pd.read_csv(daily_csv)
            df_hist = pd.concat([df_hist, df_new], ignore_index=True)
        else:
            df_hist = df_new
        df_hist.to_csv(daily_csv, index=False)

        # Aggregate daily health
        total_req = int(df_hist["total_requested"].sum())
        total_succ = int(df_hist["successful_requests"].sum())
        total_fail = int(df_hist["failed_requests"].sum())
        avg_cov = float(df_hist["coverage_percentage"].mean())
        avg_lat = float(df_hist["average_latency_seconds"].mean())

        daily_summary = {
            "date": today_str,
            "total_requests": total_req,
            "successful_requests": total_succ,
            "failed_requests": total_fail,
            "average_coverage_percentage": round(avg_cov, 2),
            "average_latency_seconds": round(avg_lat, 4),
            "last_cycle": cycle_report,
        }

        with open(daily_json, "w", encoding="utf-8") as f:
            json.dump(daily_summary, f, indent=2)

        return daily_summary

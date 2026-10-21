"""APScheduler background job scheduling scaffold for UrbanTwin.

Manages recurring jobs (hourly collector polling, live pipeline checks)
with start, stop, and status lifecycle hooks, with graceful fallback if
apscheduler is not yet installed in the local environment.
"""

from typing import Any, Optional

try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.interval import IntervalTrigger
    HAS_APSCHEDULER = True
except ImportError:
    HAS_APSCHEDULER = False

from config.logging import get_logger
from config.settings import settings

logger = get_logger(__name__)


class TaskScheduler:
    """Wrapper around AsyncIOScheduler for recurring pipeline jobs."""

    def __init__(self) -> None:
        self.scheduler: Any = AsyncIOScheduler() if HAS_APSCHEDULER else None
        self._is_running: bool = False

    def start(self) -> None:
        """Start background scheduler if enabled in settings."""
        if not settings.ENABLE_SCHEDULER:
            logger.info("Scheduler is disabled by configuration (ENABLE_SCHEDULER=False)")
            return

        if not HAS_APSCHEDULER:
            logger.warning("apscheduler package is not installed; background scheduling disabled")
            return

        if not self._is_running and self.scheduler is not None:
            self._register_jobs()
            self.scheduler.start()
            self._is_running = True
            logger.info("APScheduler initialized and running successfully")

    def shutdown(self) -> None:
        """Gracefully shut down background scheduler."""
        if self._is_running and self.scheduler is not None:
            self.scheduler.shutdown(wait=False)
            self._is_running = False
            logger.info("APScheduler shut down")

    def _register_jobs(self) -> None:
        """Register recurring background jobs."""
        if not HAS_APSCHEDULER or self.scheduler is None:
            return

        interval = getattr(settings, "POLLING_INTERVAL_MINUTES", 30)
        logger.info(
            "Registering recurring TomTom traffic collection job",
            interval_minutes=interval,
        )
        self.scheduler.add_job(
            func=self.trigger_traffic_collection,
            trigger=IntervalTrigger(minutes=interval),
            id="recurring_traffic_collector",
            name="TomTom Periodic Traffic Collector",
            replace_existing=True,
        )

    def trigger_traffic_collection(self) -> None:
        """Execute traffic collection cycle via pipeline."""
        from pipelines.traffic import TrafficCollectionPipeline
        pipeline = TrafficCollectionPipeline()
        result = pipeline.execute()
        logger.info("Executed scheduled traffic collection", success=result.success, metrics=result.metrics)


# Singleton instance
app_scheduler = TaskScheduler()

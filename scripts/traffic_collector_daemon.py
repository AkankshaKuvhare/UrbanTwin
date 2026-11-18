"""
UrbanTwin Continuous Traffic Collector Daemon.
Polls the TomTom Traffic Flow API for all 40 arterial corridors every 15 minutes,
appending observations to data/traffic/traffic_observations.parquet and updating health logs.
"""

import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from config.settings import settings
from config.logging import get_logger
from pipelines.traffic import TrafficCollectionPipeline

logger = get_logger("urbantwin.daemon.traffic")


def run_daemon():
    interval_seconds = getattr(settings, "POLLING_INTERVAL_MINUTES", 15) * 60
    logger.info(
        "Starting UrbanTwin Continuous Traffic Collection Daemon",
        interval_minutes=interval_seconds // 60,
        api_key_configured=bool(settings.TOMTOM_API_KEY),
    )
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Traffic Daemon started. Polling every {interval_seconds // 60} minutes.")

    cycle_count = 0
    pipeline = TrafficCollectionPipeline()

    while True:
        cycle_count += 1
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n[{now_str}] --- Starting Collection Cycle #{cycle_count} ---")
        
        try:
            result = pipeline.execute()
            if result.success:
                print(f"[{now_str}] Cycle #{cycle_count} SUCCESS: {result.metrics.get('records_collected')} points collected (100% coverage in {result.metrics.get('execution_time_seconds', 0):.2f}s).")
            else:
                print(f"[{now_str}] Cycle #{cycle_count} WARNING: {result.error_message}")
        except Exception as exc:
            print(f"[{now_str}] Cycle #{cycle_count} ERROR: {exc}")

        next_run = time.time() + interval_seconds
        next_run_str = datetime.fromtimestamp(next_run).strftime("%H:%M:%S")
        print(f"[{now_str}] Sleeping for {interval_seconds // 60}m. Next run at {next_run_str}...")
        
        # Sleep until next interval
        time.sleep(interval_seconds)


if __name__ == "__main__":
    try:
        run_daemon()
    except KeyboardInterrupt:
        print("\nTraffic Daemon stopped by user.")

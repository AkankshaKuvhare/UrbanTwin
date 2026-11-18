import sys, time
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from pipelines.traffic import TrafficCollectionPipeline

t0 = time.time()
print("Starting TrafficCollectionPipeline execute test...")
pipeline = TrafficCollectionPipeline()
res = pipeline.execute()
print(f"Executed in {time.time() - t0:.2f}s")
print(f"Success: {res.success}")
print("Metrics:", res.metrics)
if not res.success:
    print("Error:", res.error_message)

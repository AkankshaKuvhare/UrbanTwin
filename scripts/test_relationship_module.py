"""End-to-End Validation Script for UrbanTwin Milestone 8 Relationship Analytics.

Verifies:
1. Backend & Data Loading (Pollutants, Weather, Traffic)
2. Statistical Modules (Correlation, Scatter OLS, Seasonality, Network Graph, Feature Drivers)
3. Artifacts Generation (CSVs, JSONs, Publication-quality PNGs, HTML Report)
4. Dashboard Generation (/dashboard/relationships)
5. FastAPI Endpoints (/api/v1/relationships/*)

Usage:
    python scripts/test_relationship_module.py
"""

import os
import sys
import time
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
from fastapi.testclient import TestClient

from analytics.correlation import (
    compute_correlation_matrices,
    compute_correlation_summary,
    export_correlation_reports,
    get_active_variables,
)
from analytics.dashboard import (
    build_relationships_dashboard_html,
    export_relationships_dashboard_html,
    load_analytical_dataset,
    compute_kpis,
)
from analytics.feature_importance import (
    compute_or_load_feature_importance,
    export_importance_reports,
    get_attribution_summary,
)
from analytics.network_graph import (
    build_network_graph_data,
    export_network_reports,
)
from analytics.scatter_analysis import (
    compute_scatter_statistics,
    export_scatter_reports,
    get_active_scatter_pairs,
)
from analytics.seasonality import (
    compute_all_variables_seasonality,
    compute_seasonality_aggregates,
    export_seasonality_reports,
)
from analytics.time_series_analysis import (
    prepare_datetime_index,
    resample_time_series,
)
from config.settings import settings
from main import app

REPORTS_DIR = PROJECT_ROOT / "reports" / "relationships"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def _banner(title: str) -> None:
    line = "=" * 65
    print(f"\n{line}")
    print(f"  {title}")
    print(line)


def _ok(msg: str) -> None:
    safe = str(msg).encode("ascii", "replace").decode("ascii")
    print(f"  [OK]   {safe}")


def _warn(msg: str) -> None:
    safe = str(msg).encode("ascii", "replace").decode("ascii")
    print(f"  [WARN] {safe}")


def _err(msg: str) -> None:
    safe = str(msg).encode("ascii", "replace").decode("ascii")
    print(f"  [ERR]  {safe}")


def _info(msg: str) -> None:
    safe = str(msg).encode("ascii", "replace").decode("ascii")
    print(f"  [INFO] {safe}")


def test_backend_and_data() -> pd.DataFrame:
    """1. Verify backend data ingestion and active variables."""
    _banner("1. Backend & Analytical Dataset Ingestion")
    df = load_analytical_dataset()
    if df.empty:
        raise RuntimeError("Failed to load analytical dataset (fused_zone_time)")

    _ok(f"Loaded master dataset: {len(df):,} records, {len(df.columns)} columns")
    active_vars = get_active_variables(df)
    _ok(f"Identified {len(active_vars)} active numeric variables:")
    _info(f"  {active_vars}")

    kpis = compute_kpis(df)
    _ok(f"KPI Summary: {kpis['total_vars']} variables, {kpis['strong_relationships']} strong correlations, {kpis['avg_correlation']} avg r")
    return df


def test_correlation_module(df: pd.DataFrame) -> None:
    """2. Verify Pearson, Spearman, Kendall matrices and target summary."""
    _banner("2. Multi-Method Correlation Analysis")
    matrices = compute_correlation_matrices(df)
    for m in ["pearson", "spearman", "kendall"]:
        mat = matrices.get(m)
        if mat is not None and not mat.empty:
            _ok(f"{m.capitalize()} matrix computed: {mat.shape[0]}x{mat.shape[1]}")
        else:
            raise ValueError(f"Missing {m} correlation matrix")

    summary_df = compute_correlation_summary(df, target="aqi")
    _ok(f"Computed AQI correlation summary against {len(summary_df)} variables:")
    for _, r in summary_df.head(5).iterrows():
        _info(f"  {r['variable']} ({r['category']}): r={r['pearson_r']:+.4f}, rho={r['spearman_rho']:+.4f}, tau={r['kendall_tau']:+.4f}")


def test_scatter_module(df: pd.DataFrame) -> None:
    """3. Verify scatter OLS regression statistics."""
    _banner("3. Bivariate Scatter & OLS Regression")
    pairs = get_active_scatter_pairs(df)
    _ok(f"Active scatter pairs identified: {len(pairs)} pairs")
    stats_df = compute_scatter_statistics(df, pairs=pairs)
    _ok(f"Computed regression parameters for {len(stats_df)} pairs:")
    for _, r in stats_df.head(4).iterrows():
        _info(f"  {r['y_variable']} vs {r['x_variable']}: R^2={r['r_squared']:.4f}, r={r['pearson_r']:+.4f}, slope={r['slope']:.2f}")


def test_timeseries_module(df: pd.DataFrame) -> None:
    """4. Verify multi-tier time series resampling."""
    _banner("4. Time-Series Multi-Interval Resampling")
    for freq in ["D", "W", "ME", "YE"]:
        resampled = resample_time_series(df, freq=freq)
        _ok(f"Resampled frequency '{freq}': {len(resampled)} intervals, {len(resampled.columns)} variables")


def test_seasonality_module(df: pd.DataFrame) -> None:
    """5. Verify seasonal cyclic profile computations."""
    _banner("5. Seasonality & Cyclical Profile Extraction")
    aggs = compute_seasonality_aggregates(df, target_col="aqi")
    _ok(f"Monthly cycle: {len(aggs['monthly'])} months")
    _ok(f"Day-of-week cycle: {len(aggs['day_of_week'])} days")
    _ok(f"Month x Day matrix: {aggs['month_dow_pivot'].shape[0]}x{aggs['month_dow_pivot'].shape[1]}")


def test_network_graph_module(df: pd.DataFrame) -> None:
    """6. Verify force-directed network topology."""
    _banner("6. Force-Directed Dependency Network Graph")
    data = build_network_graph_data(df, threshold=0.20)
    _ok(f"Constructed network topology: {len(data['nodes'])} nodes, {len(data['edges'])} edges")
    _ok(f"Graph stats: density={data['stats']['density']}, threshold={data['stats']['threshold']}")


def test_feature_importance_module(df: pd.DataFrame) -> None:
    """7. Verify feature importance and attribution placeholders."""
    _banner("7. Predictive Feature Drivers & SHAP Placeholders")
    imp_df = compute_or_load_feature_importance(df)
    _ok(f"Computed feature importances for {len(imp_df)} predictors:")
    for _, r in imp_df.head(4).iterrows():
        _info(f"  {r['label']} ({r['category']}): {r['importance_pct']:.1f}%")

    attr = get_attribution_summary(df)
    _ok(f"SHAP Status: {attr['shap_placeholder']['status']}")
    _ok(f"Traffic Integration: {attr['traffic_placeholder']['status']}")


def test_reports_generation(df: pd.DataFrame) -> None:
    """8. Generate and verify all output reports in reports/relationships/."""
    _banner("8. Reports & Figure Artifacts Generation")
    export_correlation_reports(df, REPORTS_DIR)
    export_scatter_reports(df, REPORTS_DIR)
    export_seasonality_reports(df, REPORTS_DIR)
    export_network_reports(df, REPORTS_DIR)
    export_importance_reports(df, REPORTS_DIR)
    export_relationships_dashboard_html(REPORTS_DIR / "relationship_report.html")

    expected_files = [
        "correlation_matrix.csv",
        "correlation_summary.csv",
        "network_edges.csv",
        "seasonality.csv",
        "scatter_statistics.csv",
        "relationship_report.html",
        "correlation_matrices.json",
        "network_data.json",
        "explainability_attribution.json",
        "correlation_heatmap.png",
        "scatter_grid.png",
        "seasonality_overview.png",
        "network_graph.png",
        "feature_importance.png",
    ]

    missing = []
    for fname in expected_files:
        fpath = REPORTS_DIR / fname
        if fpath.exists() and fpath.stat().st_size > 0:
            _ok(f"Artifact created: {fname} ({fpath.stat().st_size:,} bytes)")
        else:
            missing.append(fname)
            _err(f"Missing or empty artifact: {fname}")

    if missing:
        raise FileNotFoundError(f"Failed to generate reports: {missing}")


def test_api_endpoints() -> None:
    """9. Test FastAPI relationship endpoints via TestClient."""
    _banner("9. FastAPI REST Endpoints Verification")
    client = TestClient(app)

    endpoints = [
        ("/api/v1/relationships/correlation?method=pearson", 200, "matrix"),
        ("/api/v1/relationships/correlation?method=spearman", 200, "matrix"),
        ("/api/v1/relationships/network?threshold=0.20", 200, "nodes"),
        ("/api/v1/relationships/scatter?x_var=pm25&y_var=aqi", 200, "regression_stats"),
        ("/api/v1/relationships/seasonality?target=aqi", 200, "monthly"),
        ("/api/v1/relationships/timeseries?freq=W", 200, "data"),
        ("/dashboard/relationships", 200, "text/html"),
    ]

    for url, exp_code, exp_key in endpoints:
        resp = client.get(url)
        if resp.status_code == exp_code:
            if "text/html" in resp.headers.get("content-type", ""):
                _ok(f"GET {url} -> {resp.status_code} ({len(resp.text):,} chars HTML)")
            else:
                data = resp.json()
                has_key = exp_key in data
                _ok(f"GET {url} -> {resp.status_code} (contains '{exp_key}': {has_key})")
        else:
            _err(f"GET {url} returned {resp.status_code} != {exp_code}")
            raise AssertionError(f"Endpoint test failed for {url}")


def main() -> int:
    start_time = time.monotonic()
    _banner("UrbanTwin Milestone 8: Relationship Analytics End-to-End Validation")

    try:
        df = test_backend_and_data()
        test_correlation_module(df)
        test_scatter_module(df)
        test_timeseries_module(df)
        test_seasonality_module(df)
        test_network_graph_module(df)
        test_feature_importance_module(df)
        test_reports_generation(df)
        test_api_endpoints()

        elapsed = time.monotonic() - start_time
        _banner("VALIDATION COMPLETE: ALL CHECKS PASSED")
        _ok(f"Milestone 8 fully operational in {elapsed:.2f} seconds!")
        _ok(f"Reports saved to: {REPORTS_DIR}")
        return 0
    except Exception as exc:
        _err(f"Validation failed: {exc}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

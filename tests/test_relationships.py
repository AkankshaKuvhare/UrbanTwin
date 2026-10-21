"""Unit and integration tests for UrbanTwin Milestone 8 Relationship Analytics.

Tests:
- Correlation matrices (Pearson, Spearman, Kendall)
- Bivariate scatter and OLS regression analysis
- Multi-tier time series resampling and synchronized timeline
- Seasonality and cyclic pattern extraction
- Force-directed relationship network graph topology
- Feature importance and attribution placeholders
- Standalone HTML dashboard generation
- CSV and artifact export integrity
- FastAPI REST endpoints
"""

import json
from pathlib import Path
from unittest.mock import patch
import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from analytics.correlation import (
    compute_correlation_matrices,
    compute_correlation_summary,
    export_correlation_reports,
    generate_correlation_heatmap_fig,
    get_active_variables,
    POLLUTANT_VARIABLES,
    WEATHER_VARIABLES,
    TRAFFIC_VARIABLES,
)
from analytics.dashboard import (
    build_relationships_dashboard_html,
    compute_kpis,
    export_relationships_dashboard_html,
    load_analytical_dataset,
)
from analytics.feature_importance import (
    compute_or_load_feature_importance,
    export_importance_reports,
    generate_feature_importance_fig,
    get_attribution_summary,
)
from analytics.network_graph import (
    build_network_graph_data,
    export_network_reports,
    generate_network_graph_fig,
)
from analytics.scatter_analysis import (
    compute_scatter_statistics,
    export_scatter_reports,
    generate_single_scatter_fig,
    get_active_scatter_pairs,
)
from analytics.seasonality import (
    compute_all_variables_seasonality,
    compute_seasonality_aggregates,
    export_seasonality_reports,
    generate_seasonality_figures,
)
from analytics.time_series_analysis import (
    generate_synchronized_timeline_fig,
    prepare_datetime_index,
    resample_time_series,
)
from main import app


@pytest.fixture
def sample_analytical_df() -> pd.DataFrame:
    """Create a realistic synthetic analytical DataFrame for testing."""
    dates = pd.date_range("2022-01-01", periods=120, freq="D")
    np.random.seed(42)

    # Correlated signals
    pm25 = np.random.uniform(20, 150, size=len(dates))
    # aqi strongly correlated with pm25
    aqi = pm25 * 1.2 + np.random.normal(0, 10, size=len(dates))
    temp = 20 + 10 * np.sin(np.linspace(0, 3.14, len(dates))) + np.random.normal(0, 2, size=len(dates))
    humidity = 80 - temp * 1.5 + np.random.normal(0, 5, size=len(dates))
    wind = np.random.uniform(2, 20, size=len(dates))

    data = {
        "observation_datetime": dates,
        "station_id": np.random.choice(["11613", "5661"], size=len(dates)),
        "aqi": aqi,
        "pm25": pm25,
        "pm10": pm25 * 1.5 + np.random.normal(0, 5, size=len(dates)),
        "no2": np.random.uniform(10, 80, size=len(dates)),
        "co": np.random.uniform(0.2, 3.0, size=len(dates)),
        "so2": np.random.uniform(2, 20, size=len(dates)),
        "o3": np.random.uniform(10, 60, size=len(dates)),
        "temperature_2m": temp,
        "relative_humidity_2m": humidity,
        "wind_speed_10m": wind,
        "wind_direction_10m": np.random.uniform(0, 360, size=len(dates)),
        "surface_pressure": np.random.uniform(940, 960, size=len(dates)),
        "precipitation": np.random.exponential(0.5, size=len(dates)),
        "boundary_layer_height": np.random.uniform(100, 1200, size=len(dates)),
        # Traffic initially null (by design)
        "traffic_speed": [np.nan] * len(dates),
        "traffic_congestion": [np.nan] * len(dates),
        "traffic_travel_time": [np.nan] * len(dates),
        "traffic_confidence": [np.nan] * len(dates),
    }
    return pd.DataFrame(data)


# ---------------------------------------------------------------------------
# 1. Correlation Analysis Tests
# ---------------------------------------------------------------------------

class TestCorrelationAnalysis:

    def test_get_active_variables(self, sample_analytical_df):
        active = get_active_variables(sample_analytical_df)
        assert "aqi" in active
        assert "pm25" in active
        assert "temperature_2m" in active
        # Traffic should not be active since all null
        assert "traffic_speed" not in active

    def test_traffic_variables_auto_included_when_non_null(self, sample_analytical_df):
        sample_analytical_df["traffic_speed"] = np.random.uniform(20, 60, size=len(sample_analytical_df))
        active = get_active_variables(sample_analytical_df)
        assert "traffic_speed" in active

    def test_compute_correlation_matrices(self, sample_analytical_df):
        matrices = compute_correlation_matrices(sample_analytical_df)
        for method in ["pearson", "spearman", "kendall"]:
            assert method in matrices
            mat = matrices[method]
            assert not mat.empty
            assert mat.loc["aqi", "aqi"] == 1.0
            # PM2.5 and AQI should have strong positive correlation
            assert mat.loc["aqi", "pm25"] > 0.8

    def test_compute_correlation_summary(self, sample_analytical_df):
        summary_df = compute_correlation_summary(sample_analytical_df, target="aqi")
        assert not summary_df.empty
        assert "abs_pearson_r" in summary_df.columns
        assert "relationship_strength" in summary_df.columns
        # Sorted by abs_pearson_r descending
        assert summary_df["abs_pearson_r"].is_monotonic_decreasing

    def test_generate_correlation_heatmap_fig(self, sample_analytical_df):
        matrices = compute_correlation_matrices(sample_analytical_df)
        fig = generate_correlation_heatmap_fig(matrices["pearson"])
        assert fig is not None
        assert len(fig.data) > 0


# ---------------------------------------------------------------------------
# 2. Scatter & Regression Tests
# ---------------------------------------------------------------------------

class TestScatterAnalysis:

    def test_get_active_scatter_pairs(self, sample_analytical_df):
        pairs = get_active_scatter_pairs(sample_analytical_df)
        assert ("pm25", "aqi") in pairs
        assert ("temperature_2m", "aqi") in pairs

    def test_compute_scatter_statistics(self, sample_analytical_df):
        stats_df = compute_scatter_statistics(sample_analytical_df)
        assert not stats_df.empty
        assert "r_squared" in stats_df.columns
        assert "slope" in stats_df.columns
        # PM2.5 vs AQI should have high R²
        pm25_row = stats_df[stats_df["x_variable"] == "pm25"].iloc[0]
        assert pm25_row["r_squared"] > 0.70

    def test_generate_single_scatter_fig(self, sample_analytical_df):
        fig = generate_single_scatter_fig(sample_analytical_df, x_col="pm25", y_col="aqi")
        assert fig is not None
        assert len(fig.data) == 2  # markers and regression trendline


# ---------------------------------------------------------------------------
# 3. Time Series Analysis Tests
# ---------------------------------------------------------------------------

class TestTimeSeriesAnalysis:

    def test_prepare_datetime_index(self, sample_analytical_df):
        clean = prepare_datetime_index(sample_analytical_df)
        assert isinstance(clean.index, pd.DatetimeIndex)
        assert clean.index.is_monotonic_increasing

    def test_resample_time_series_frequencies(self, sample_analytical_df):
        for freq in ["D", "W", "ME"]:
            resampled = resample_time_series(sample_analytical_df, freq=freq)
            assert not resampled.empty
            assert "aqi" in resampled.columns

    def test_generate_synchronized_timeline_fig(self, sample_analytical_df):
        fig = generate_synchronized_timeline_fig(sample_analytical_df, freq="W")
        assert fig is not None
        assert len(fig.data) >= 3


# ---------------------------------------------------------------------------
# 4. Seasonality Tests
# ---------------------------------------------------------------------------

class TestSeasonalityAnalysis:

    def test_compute_seasonality_aggregates(self, sample_analytical_df):
        aggs = compute_seasonality_aggregates(sample_analytical_df, target_col="aqi")
        assert "monthly" in aggs
        assert "weekly" in aggs
        assert "day_of_week" in aggs
        assert "month_dow_pivot" in aggs
        assert len(aggs["day_of_week"]) == 7

    def test_generate_seasonality_figures(self, sample_analytical_df):
        figs = generate_seasonality_figures(sample_analytical_df, target_col="aqi")
        assert "monthly" in figs
        assert "day_of_week" in figs
        assert "heatmap" in figs


# ---------------------------------------------------------------------------
# 5. Network Graph Tests
# ---------------------------------------------------------------------------

class TestNetworkGraph:

    def test_build_network_graph_data(self, sample_analytical_df):
        data = build_network_graph_data(sample_analytical_df, threshold=0.15)
        assert "nodes" in data
        assert "edges" in data
        assert "stats" in data
        assert len(data["nodes"]) > 0

        # Verify node fields
        first_node = data["nodes"][0]
        assert "mean" in first_node
        assert "std" in first_node
        assert "missing_pct" in first_node
        assert "centrality" in first_node

    def test_network_edge_coloring(self, sample_analytical_df):
        data = build_network_graph_data(sample_analytical_df, threshold=0.15)
        for edge in data["edges"]:
            if edge["correlation"] >= 0:
                assert edge["color"] == "#22c55e"  # Positive Green
            else:
                assert edge["color"] == "#ef4444"  # Negative Red

    def test_generate_network_graph_fig(self, sample_analytical_df):
        fig = generate_network_graph_fig(sample_analytical_df, threshold=0.15)
        assert fig is not None
        assert len(fig.data) >= 2


# ---------------------------------------------------------------------------
# 6. Feature Importance & Explainability Tests
# ---------------------------------------------------------------------------

class TestFeatureImportance:

    def test_compute_or_load_feature_importance(self, sample_analytical_df):
        imp_df = compute_or_load_feature_importance(sample_analytical_df)
        assert not imp_df.empty
        assert "feature" in imp_df.columns
        assert "importance" in imp_df.columns

    def test_get_attribution_summary(self, sample_analytical_df):
        meta = get_attribution_summary(sample_analytical_df)
        assert "shap_placeholder" in meta
        assert "traffic_placeholder" in meta
        assert meta["traffic_placeholder"]["status"] == "Pending Ingestion"

    def test_generate_feature_importance_fig(self, sample_analytical_df):
        imp_df = compute_or_load_feature_importance(sample_analytical_df)
        fig = generate_feature_importance_fig(imp_df)
        assert fig is not None


# ---------------------------------------------------------------------------
# 7. Dashboard and Reports Export Tests
# ---------------------------------------------------------------------------

class TestDashboardAndReports:

    def test_compute_kpis(self, sample_analytical_df):
        kpis = compute_kpis(sample_analytical_df)
        assert kpis["total_vars"] > 0
        assert kpis["strong_relationships"] >= 1
        assert 0.0 <= kpis["missing_pct"] <= 100.0

    def test_build_relationships_dashboard_html(self, sample_analytical_df):
        with patch("analytics.dashboard.load_analytical_dataset", return_value=sample_analytical_df):
            html = build_relationships_dashboard_html()
            assert isinstance(html, str)
            assert "Relationship Analytics" in html
            assert "Correlation Heatmap" in html
            assert "Force-Directed Network" in html

    def test_export_all_reports(self, sample_analytical_df, tmp_path):
        export_correlation_reports(sample_analytical_df, tmp_path)
        export_scatter_reports(sample_analytical_df, tmp_path)
        export_seasonality_reports(sample_analytical_df, tmp_path)
        export_network_reports(sample_analytical_df, tmp_path)
        export_importance_reports(sample_analytical_df, tmp_path)

        with patch("analytics.dashboard.load_analytical_dataset", return_value=sample_analytical_df):
            export_relationships_dashboard_html(tmp_path / "relationship_report.html")

        expected_artifacts = [
            "correlation_matrix.csv",
            "correlation_summary.csv",
            "network_edges.csv",
            "seasonality.csv",
            "scatter_statistics.csv",
            "relationship_report.html",
            "correlation_heatmap.png",
            "scatter_grid.png",
            "seasonality_overview.png",
            "network_graph.png",
            "feature_importance.png",
        ]
        for f in expected_artifacts:
            p = tmp_path / f
            assert p.exists(), f"Missing artifact: {f}"
            assert p.stat().st_size > 0, f"Empty artifact: {f}"


# ---------------------------------------------------------------------------
# 8. FastAPI Endpoints Tests
# ---------------------------------------------------------------------------

class TestFastAPIRelationshipEndpoints:

    def test_correlation_endpoint(self):
        client = TestClient(app)
        res = client.get("/api/v1/relationships/correlation?method=pearson")
        assert res.status_code == 200
        data = res.json()
        assert "matrix" in data
        assert "target_summary" in data

    def test_network_endpoint(self):
        client = TestClient(app)
        res = client.get("/api/v1/relationships/network?threshold=0.20")
        assert res.status_code == 200
        data = res.json()
        assert "nodes" in data
        assert "edges" in data

    def test_scatter_endpoint(self):
        client = TestClient(app)
        res = client.get("/api/v1/relationships/scatter?x_var=pm25&y_var=aqi")
        assert res.status_code == 200
        data = res.json()
        assert "regression_stats" in data
        assert "all_pairs_summary" in data

    def test_seasonality_endpoint(self):
        client = TestClient(app)
        res = client.get("/api/v1/relationships/seasonality?target=aqi")
        assert res.status_code == 200
        data = res.json()
        assert "monthly" in data
        assert "day_of_week" in data

    def test_timeseries_endpoint(self):
        client = TestClient(app)
        res = client.get("/api/v1/relationships/timeseries?freq=W")
        assert res.status_code == 200
        data = res.json()
        assert "data" in data

    def test_dashboard_route(self):
        client = TestClient(app)
        res = client.get("/dashboard/relationships")
        assert res.status_code == 200
        assert "text/html" in res.headers["content-type"]
        assert len(res.text) > 5000

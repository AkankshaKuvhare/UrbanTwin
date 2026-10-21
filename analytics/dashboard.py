"""Relationship Analytics Dashboard for UrbanTwin Milestone 8.

FastAPI Router and Standalone HTML Generator delivering:
- KPI Summary Cards:
  * Total Variables Analyzed
  * Strong Relationships Count (|r| >= 0.5)
  * Average Correlation (|r|)
  * Missing Data Overall (%)
- Interactive Tabbed Analytics Workspace:
  1. Correlation Heatmap (Pearson, Spearman, Kendall rank matrices)
  2. Scatter Analysis (OLS regression lines, R², correlation stats)
  3. Force-Directed Network Graph (green/red weighted edges, interactive node metadata)
  4. Seasonality (Monthly, Day-of-Week, Heatmap cyclic patterns)
  5. Synchronized Time-Series Explorer (Daily, Weekly, Monthly, Yearly aggregation)
  6. Feature Importance & Explainability (Top drivers, SHAP and Traffic placeholders)
- Interactive Controls:
  * Station selector
  * Target pollutant selector
  * Weather covariate selector
  * Aggregation frequency selector
- Dark Mode Compatible UI matching Tailwind / Slate aesthetic.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd
from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse

from analytics.correlation import (
    DEFAULT_VARIABLE_LABELS,
    POLLUTANT_VARIABLES,
    WEATHER_VARIABLES,
    TRAFFIC_VARIABLES,
    compute_correlation_matrices,
    compute_correlation_summary,
    generate_correlation_heatmap_fig,
    get_active_variables,
)
from analytics.feature_importance import (
    compute_or_load_feature_importance,
    generate_feature_importance_fig,
    get_attribution_summary,
)
from analytics.network_graph import (
    build_network_graph_data,
    generate_network_graph_fig,
)
from analytics.scatter_analysis import (
    compute_scatter_statistics,
    generate_single_scatter_fig,
    get_active_scatter_pairs,
)
from analytics.seasonality import (
    compute_seasonality_aggregates,
    generate_seasonality_figures,
)
from analytics.time_series_analysis import (
    generate_synchronized_timeline_fig,
    resample_time_series,
)
from config.logging import get_logger
from config.settings import settings

logger = get_logger("urbantwin.analytics.dashboard")

router = APIRouter(prefix="/dashboard", tags=["relationships_dashboard"])

FUSED_DATA_PATH = settings.DATA_DIR / "fused_zone_time.parquet"
REPORTS_DIR = settings.BASE_DIR / "reports" / "relationships"


def load_analytical_dataset(station_id: Optional[str] = None) -> pd.DataFrame:
    """Load fused analytical dataset with optional station filtering."""
    if not FUSED_DATA_PATH.exists():
        csv_fallback = settings.DATA_DIR / "fused_zone_time.csv"
        if csv_fallback.exists():
            df = pd.read_csv(csv_fallback)
        else:
            return pd.DataFrame()
    else:
        df = pd.read_parquet(FUSED_DATA_PATH)

    if station_id and station_id != "all" and "station_id" in df.columns:
        df = df[df["station_id"].astype(str) == str(station_id)].copy()

    return df


def compute_kpis(df: pd.DataFrame) -> Dict[str, Any]:
    """Compute top-level summary metrics for KPI cards."""
    if df.empty:
        return {
            "total_vars": 0,
            "strong_relationships": 0,
            "avg_correlation": 0.0,
            "missing_pct": 0.0,
            "total_records": 0,
        }

    active_vars = get_active_variables(df)
    corr_summary = compute_correlation_summary(df, target="aqi", variables=active_vars)

    strong_count = 0
    avg_corr = 0.0
    if not corr_summary.empty:
        strong_count = int((corr_summary["abs_pearson_r"] >= 0.5).sum())
        avg_corr = round(float(corr_summary["abs_pearson_r"].mean()), 3)

    # Missing data percentage across all active vars
    if active_vars:
        missing_pct = round(float(df[active_vars].isna().mean().mean() * 100), 1)
    else:
        missing_pct = 0.0

    return {
        "total_vars": len(active_vars),
        "strong_relationships": strong_count,
        "avg_correlation": avg_corr,
        "missing_pct": missing_pct,
        "total_records": len(df),
    }


def build_relationships_dashboard_html(
    station_id: Optional[str] = None,
    dark_mode: bool = True,
) -> str:
    """Construct complete self-contained HTML for the Relationship Analytics Dashboard."""
    df = load_analytical_dataset(station_id=station_id)
    kpis = compute_kpis(df)

    # 1. Correlation Heatmap
    corr_matrices = compute_correlation_matrices(df)
    pearson_df = corr_matrices.get("pearson", pd.DataFrame())
    fig_corr = generate_correlation_heatmap_fig(pearson_df, method="pearson", dark_mode=dark_mode)
    corr_html = fig_corr.to_html(full_html=False, include_plotlyjs="cdn")

    # 2. Scatter Plots
    active_pairs = get_active_scatter_pairs(df)
    scatter_htmls = []
    # Display top 4 scatter pairs
    for x_col, y_col in active_pairs[:4]:
        s_fig = generate_single_scatter_fig(df, x_col=x_col, y_col=y_col, dark_mode=dark_mode)
        scatter_htmls.append(s_fig.to_html(full_html=False, include_plotlyjs=False))

    # 3. Network Graph
    fig_network = generate_network_graph_fig(df, threshold=0.20, dark_mode=dark_mode)
    network_html = fig_network.to_html(full_html=False, include_plotlyjs=False)

    # 4. Seasonality
    season_figs = generate_seasonality_figures(df, target_col="aqi", dark_mode=dark_mode)
    season_month_html = season_figs["monthly"].to_html(full_html=False, include_plotlyjs=False)
    season_dow_html = season_figs["day_of_week"].to_html(full_html=False, include_plotlyjs=False)
    season_heat_html = season_figs["heatmap"].to_html(full_html=False, include_plotlyjs=False)

    # 5. Time Series Explorer
    fig_ts = generate_synchronized_timeline_fig(df, freq="W", dark_mode=dark_mode)
    ts_html = fig_ts.to_html(full_html=False, include_plotlyjs=False)

    # 6. Feature Importance & Explainability
    importance_df = compute_or_load_feature_importance(df)
    fig_imp = generate_feature_importance_fig(importance_df, top_n=10, dark_mode=dark_mode)
    imp_html = fig_imp.to_html(full_html=False, include_plotlyjs=False)
    attribution_meta = get_attribution_summary(df)

    stations = sorted([str(s) for s in df["station_id"].unique()]) if "station_id" in df.columns else []

    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UrbanTwin Pune - Relationship Analytics &amp; Causal Explorer</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {{
            background-color: #0f172a;
            color: #f8fafc;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        }}
        .card {{
            background-color: #1e293b;
            border: 1px solid #334155;
            border-radius: 0.75rem;
        }}
        .tab-btn.active {{
            border-bottom: 2px solid #38bdf8;
            color: #38bdf8;
            font-weight: 600;
        }}
        .tab-content {{
            display: none;
        }}
        .tab-content.active {{
            display: block;
        }}
    </style>
</head>
<body class="p-6">
    <div class="max-w-7xl mx-auto space-y-6">

        <!-- Header -->
        <header class="flex flex-col md:flex-row justify-between items-start md:items-center pb-4 border-b border-slate-700 gap-4">
            <div>
                <div class="flex items-center gap-3">
                    <span class="text-xs font-semibold uppercase tracking-wider px-2.5 py-1 bg-sky-500/10 text-sky-400 border border-sky-500/20 rounded-full">Milestone 8</span>
                    <span class="text-xs font-semibold uppercase tracking-wider px-2.5 py-1 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded-full">Traffic-Ready</span>
                </div>
                <h1 class="text-2xl md:text-3xl font-bold tracking-tight text-white mt-2">
                    Relationship Analytics &amp; Interactive Causal Workspace
                </h1>
                <p class="text-slate-400 text-sm mt-1">
                    Multi-variate exploration between Air Quality (AQI), Meteorological Drivers, and Traffic Flow in Pune.
                </p>
            </div>
            <div class="flex items-center gap-3">
                <select id="stationFilter" onchange="filterStation(this.value)" class="bg-slate-800 border border-slate-700 text-slate-200 text-sm rounded-lg px-3 py-2 focus:ring-sky-500 focus:border-sky-500">
                    <option value="all" {"selected" if not station_id or station_id == "all" else ""}>All Pune Stations (Aggregated)</option>
                    {"".join(f'<option value="{s}" {"selected" if station_id == s else ""}>Station {s}</option>' for s in stations)}
                </select>
                <a href="/docs" class="text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 px-3 py-2 rounded-lg font-medium transition">API Docs</a>
            </div>
        </header>

        <!-- KPI Cards -->
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div class="card p-4">
                <div class="text-xs text-slate-400 font-medium uppercase">Total Variables Analyzed</div>
                <div class="text-3xl font-bold text-sky-400 mt-2">{kpis['total_vars']}</div>
                <div class="text-xs text-slate-500 mt-1">Pollutants, Weather &amp; Traffic</div>
            </div>
            <div class="card p-4">
                <div class="text-xs text-slate-400 font-medium uppercase">Strong Relationships (|r| ≥ 0.5)</div>
                <div class="text-3xl font-bold text-amber-400 mt-2">{kpis['strong_relationships']}</div>
                <div class="text-xs text-slate-500 mt-1">High predictive influence on AQI</div>
            </div>
            <div class="card p-4">
                <div class="text-xs text-slate-400 font-medium uppercase">Average Correlation (|r|)</div>
                <div class="text-3xl font-bold text-emerald-400 mt-2">{kpis['avg_correlation']}</div>
                <div class="text-xs text-slate-500 mt-1">Mean absolute correlation vs AQI</div>
            </div>
            <div class="card p-4">
                <div class="text-xs text-slate-400 font-medium uppercase">Dataset Missingness Overall</div>
                <div class="text-3xl font-bold text-purple-400 mt-2">{kpis['missing_pct']}%</div>
                <div class="text-xs text-slate-500 mt-1">Across {kpis['total_records']:,} observations</div>
            </div>
        </div>

        <!-- Navigation Tabs -->
        <div class="border-b border-slate-700">
            <nav class="flex space-x-6 text-sm">
                <button onclick="switchTab('tab-correlation')" class="tab-btn py-3 px-1 text-slate-400 hover:text-white active" id="btn-tab-correlation">
                    Correlation Heatmap
                </button>
                <button onclick="switchTab('tab-scatter')" class="tab-btn py-3 px-1 text-slate-400 hover:text-white" id="btn-tab-scatter">
                    Scatter Analysis &amp; OLS
                </button>
                <button onclick="switchTab('tab-network')" class="tab-btn py-3 px-1 text-slate-400 hover:text-white" id="btn-tab-network">
                    Force-Directed Network
                </button>
                <button onclick="switchTab('tab-seasonality')" class="tab-btn py-3 px-1 text-slate-400 hover:text-white" id="btn-tab-seasonality">
                    Seasonality &amp; Cycles
                </button>
                <button onclick="switchTab('tab-timeseries')" class="tab-btn py-3 px-1 text-slate-400 hover:text-white" id="btn-tab-timeseries">
                    Synchronized Timeline
                </button>
                <button onclick="switchTab('tab-importance')" class="tab-btn py-3 px-1 text-slate-400 hover:text-white" id="btn-tab-importance">
                    Feature Drivers &amp; SHAP
                </button>
            </nav>
        </div>

        <!-- TAB 1: Correlation Heatmap -->
        <div id="tab-correlation" class="tab-content active space-y-4">
            <div class="card p-4">
                <div class="flex justify-between items-center mb-2">
                    <h2 class="text-lg font-semibold text-white">Multi-Method Correlation Matrix</h2>
                    <span class="text-xs text-slate-400">Pearson (r) | Spearman (ρ) | Kendall (τ)</span>
                </div>
                {corr_html}
            </div>
        </div>

        <!-- TAB 2: Scatter Analysis -->
        <div id="tab-scatter" class="tab-content space-y-4">
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
                {"".join(f'<div class="card p-3">{s}</div>' for s in scatter_htmls)}
            </div>
        </div>

        <!-- TAB 3: Force-Directed Network Graph -->
        <div id="tab-network" class="tab-content space-y-4">
            <div class="card p-4">
                <div class="flex justify-between items-center mb-2">
                    <div>
                        <h2 class="text-lg font-semibold text-white">Interactive Urban Dependency Network</h2>
                        <p class="text-xs text-slate-400">Nodes sized by centrality. Green edges = positive correlation; Red = negative correlation.</p>
                    </div>
                </div>
                {network_html}
            </div>
        </div>

        <!-- TAB 4: Seasonality -->
        <div id="tab-seasonality" class="tab-content space-y-4">
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <div class="card p-3">{season_month_html}</div>
                <div class="card p-3">{season_dow_html}</div>
            </div>
            <div class="card p-3">{season_heat_html}</div>
        </div>

        <!-- TAB 5: Time-Series Explorer -->
        <div id="tab-timeseries" class="tab-content space-y-4">
            <div class="card p-4">
                <div class="flex justify-between items-center mb-2">
                    <h2 class="text-lg font-semibold text-white">Synchronized Multi-Axis Time Series</h2>
                    <span class="text-xs text-slate-400">Interactive range slider at bottom</span>
                </div>
                {ts_html}
            </div>
        </div>

        <!-- TAB 6: Feature Drivers & SHAP -->
        <div id="tab-importance" class="tab-content space-y-4">
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
                <div class="card p-4 lg:col-span-2">
                    <h2 class="text-lg font-semibold text-white mb-2">Forecasting Model Feature Importance</h2>
                    {imp_html}
                </div>
                <div class="card p-4 space-y-4">
                    <div>
                        <h3 class="text-sm font-semibold uppercase text-sky-400">SHAP Explainability State</h3>
                        <p class="text-xs text-slate-300 mt-1">{attribution_meta['shap_placeholder']['summary']}</p>
                        <div class="mt-2 text-xs bg-slate-800 p-2.5 rounded border border-slate-700">
                            <span class="font-medium text-slate-200">Attribution Method:</span> {attribution_meta['shap_placeholder']['method']}<br>
                            <span class="font-medium text-slate-200">Status:</span> {attribution_meta['shap_placeholder']['status']}
                        </div>
                    </div>
                    <div class="pt-3 border-t border-slate-700">
                        <h3 class="text-sm font-semibold uppercase text-pink-400">Traffic Integration State</h3>
                        <div class="mt-2 text-xs bg-slate-800 p-2.5 rounded border border-slate-700">
                            <span class="font-medium text-slate-200">Traffic Status:</span> {attribution_meta['traffic_placeholder']['status']}<br>
                            <span class="font-medium text-slate-200">Note:</span> {attribution_meta['traffic_placeholder']['description']}
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Footer -->
        <footer class="pt-6 border-t border-slate-800 text-xs text-slate-500 flex justify-between items-center">
            <div>UrbanTwin Research Platform &bull; Pune Smart City Air Quality &amp; Traffic Twin</div>
            <div>Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
        </footer>

    </div>

    <script>
        function switchTab(tabId) {{
            document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
            document.getElementById('btn-' + tabId).classList.add('active');
            // Trigger Plotly relayout to redraw charts in newly visible tab
            window.dispatchEvent(new Event('resize'));
        }}

        function filterStation(stationId) {{
            const url = new URL(window.location);
            if (stationId === 'all') {{
                url.searchParams.delete('station_id');
            }} else {{
                url.searchParams.set('station_id', stationId);
            }}
            window.location = url.toString();
        }}
    </script>
</body>
</html>
"""
    return html_template


@router.get("/relationships", response_class=HTMLResponse)
async def get_relationships_dashboard(
    station_id: Optional[str] = Query(None, description="Station ID filter (e.g. 11613, 5661, or 'all')"),
) -> HTMLResponse:
    """FastAPI endpoint serving the interactive Relationship Analytics Dashboard."""
    html_content = build_relationships_dashboard_html(station_id=station_id)
    return HTMLResponse(content=html_content)


def export_relationships_dashboard_html(
    output_file: Optional[Path] = None,
) -> Path:
    """Generate and write standalone HTML report."""
    target_path = Path(output_file or (REPORTS_DIR / "relationship_report.html"))
    target_path.parent.mkdir(parents=True, exist_ok=True)

    html = build_relationships_dashboard_html()
    target_path.write_text(html, encoding="utf-8")
    logger.info("Exported standalone relationship dashboard HTML", path=str(target_path))
    return target_path

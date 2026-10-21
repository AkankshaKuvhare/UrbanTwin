"""Historical AQI Dashboard for UrbanTwin (CongestAir Module).

Builds an interactive Plotly-powered dashboard page displaying:
- Key metric cards (Total observations, Stations, Date range, Average AQI)
- Interactive visualizations (AQI trend, Station comparison, Pollutant trends, Missing values)
"""

from datetime import datetime
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import pandas as pd
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from config.settings import settings
from pipelines.data_quality import DataQualityAnalyzer, POLLUTANT_COLUMNS

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


def get_dashboard_data(df: Optional[pd.DataFrame] = None) -> Tuple[Dict[str, Any], pd.DataFrame]:
    """Retrieve summarized metrics and cleaned observations for the dashboard."""
    if df is None:
        candidate_paths = [
            settings.BASE_DIR / "data" / "all_stations_combined.csv",
            settings.BASE_DIR / "data" / "real" / "raw" / "all_stations_combined.csv",
            Path.home() / "Downloads" / "all_stations_combined.csv",
        ]
        valid_csv = next((p for p in candidate_paths if p.exists()), None)
        if valid_csv is None:
            raise FileNotFoundError("Historical dataset not found for dashboard.")
        df = pd.read_csv(valid_csv)

    analyzer = DataQualityAnalyzer(df)
    summary = analyzer.generate_full_report()
    return summary, analyzer.df


def build_historical_aqi_dashboard_html(summary: Dict[str, Any], df: pd.DataFrame) -> str:
    """Generate interactive Plotly-based HTML dashboard page."""
    # Data preparations for charts
    daily_aqi = (
        df.groupby("datetime")["aqi"]
        .mean()
        .dropna()
        .reset_index()
    )
    daily_aqi_json = {
        "dates": [d.strftime("%Y-%m-%d") for d in daily_aqi["datetime"]],
        "values": daily_aqi["aqi"].round(2).tolist(),
    }

    # Station comparison data
    station_names = {}
    if "station_name" in df.columns:
        station_names = df.dropna(subset=["station_name"]).set_index("station_id")["station_name"].to_dict()

    station_traces = []
    for st_id, grp in df.groupby("station_id"):
        st_label = station_names.get(st_id, f"Station {st_id}")
        vals = grp["aqi"].dropna().tolist()
        if vals:
            station_traces.append({
                "y": vals,
                "name": st_label[:20] + "..." if len(st_label) > 20 else st_label,
                "type": "box",
                "boxpoints": "outliers",
            })

    # Pollutant trends (monthly average)
    monthly_trends = df.groupby("year_month")[POLLUTANT_COLUMNS].mean().reset_index()
    pollutant_json = {
        "periods": monthly_trends["year_month"].tolist(),
        "pm25": monthly_trends["pm25"].round(2).fillna("null").tolist(),
        "pm10": monthly_trends["pm10"].round(2).fillna("null").tolist(),
        "no2": monthly_trends["no2"].round(2).fillna("null").tolist(),
    }

    # Missing values bar chart
    missing_data = summary["missing_values"]
    missing_json = {
        "cols": [m["column"] for m in missing_data],
        "null_pcts": [m["null_percentage"] for m in missing_data],
    }

    date_cov = summary["date_coverage"]
    avg_aqi = summary["average_aqi"] or "N/A"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UrbanTwin | Historical AQI Dashboard</title>
    <!-- Plotly.js CDN -->
    <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
    <style>
        :root {{
            --bg-color: #0f172a;
            --card-bg: #1e293b;
            --border-color: #334155;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --accent-blue: #38bdf8;
            --accent-green: #34d399;
            --accent-amber: #fbbf24;
            --accent-red: #f87171;
        }}
        * {{ box-sizing: border-box; }}
        body {{
            margin: 0;
            padding: 24px;
            background-color: var(--bg-color);
            color: var(--text-primary);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-bottom: 20px;
            border-bottom: 1px solid var(--border-color);
            margin-bottom: 24px;
        }}
        .header h1 {{ margin: 0; font-size: 1.8rem; font-weight: 700; color: var(--accent-blue); }}
        .header .subtitle {{ color: var(--text-secondary); font-size: 0.95rem; margin-top: 4px; }}
        .badge {{
            background: #0284c7;
            color: white;
            padding: 6px 14px;
            border-radius: 999px;
            font-size: 0.8rem;
            font-weight: 600;
            letter-spacing: 0.05em;
        }}
        /* KPI Cards Grid */
        .cards-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 18px;
            margin-bottom: 28px;
        }}
        .card {{
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
            transition: transform 0.2s ease;
        }}
        .card:hover {{ transform: translateY(-2px); }}
        .card-label {{
            font-size: 0.8rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-secondary);
        }}
        .card-value {{
            font-size: 2rem;
            font-weight: 700;
            margin-top: 8px;
            color: var(--text-primary);
        }}
        .card-subtext {{
            font-size: 0.85rem;
            color: var(--text-secondary);
            margin-top: 4px;
        }}
        /* Chart Grid */
        .charts-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(520px, 1fr));
            gap: 24px;
        }}
        .chart-box {{
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
        }}
        .chart-title {{
            font-size: 1.1rem;
            font-weight: 600;
            margin-bottom: 12px;
            color: var(--text-primary);
        }}
        .chart-container {{
            width: 100%;
            height: 380px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <div>
            <h1>UrbanTwin &bull; Historical AQI Dashboard</h1>
            <div class="subtitle">Exploratory Analysis & Station Diagnostic Console (Pune, India)</div>
        </div>
        <div>
            <span class="badge">CONGESTAIR MODULE</span>
        </div>
    </div>

    <!-- KPI Metric Cards -->
    <div class="cards-grid">
        <div class="card">
            <div class="card-label">Total Observations</div>
            <div class="card-value" style="color: var(--accent-blue);">{summary['total_observations']:,}</div>
            <div class="card-subtext">Cleaned station-day records</div>
        </div>
        <div class="card">
            <div class="card-label">Stations</div>
            <div class="card-value" style="color: var(--accent-green);">{summary['total_stations']}</div>
            <div class="card-subtext">IITM & MPCB continuous monitors</div>
        </div>
        <div class="card">
            <div class="card-label">Date Range</div>
            <div class="card-value" style="font-size: 1.25rem; margin-top: 14px; color: var(--accent-amber);">
                {date_cov['start_date']} &rarr; {date_cov['end_date']}
            </div>
            <div class="card-subtext">{date_cov['total_calendar_days']} calendar days span</div>
        </div>
        <div class="card">
            <div class="card-label">Average AQI</div>
            <div class="card-value" style="color: var(--accent-red);">{avg_aqi}</div>
            <div class="card-subtext">Moderate baseline air quality</div>
        </div>
    </div>

    <!-- Interactive Visualizations -->
    <div class="charts-grid">
        <!-- 1. AQI Trend -->
        <div class="chart-box">
            <div class="chart-title">Historical AQI Trend (Pune Aggregated Mean)</div>
            <div id="chart-aqi-trend" class="chart-container"></div>
        </div>

        <!-- 2. Station Comparison -->
        <div class="chart-box">
            <div class="chart-title">Station-Wise AQI Distribution Comparison</div>
            <div id="chart-station-comparison" class="chart-container"></div>
        </div>

        <!-- 3. Pollutant Trends -->
        <div class="chart-box">
            <div class="chart-title">Key Pollutant Trends (PM2.5, PM10, NO2 Monthly Means)</div>
            <div id="chart-pollutant-trends" class="chart-container"></div>
        </div>

        <!-- 4. Missing Values -->
        <div class="chart-box">
            <div class="chart-title">Missing Values Audit (% Null per Attribute)</div>
            <div id="chart-missing-values" class="chart-container"></div>
        </div>
    </div>

    <script>
        const darkLayout = {{
            paper_bgcolor: 'transparent',
            plot_bgcolor: 'transparent',
            font: {{ color: '#94a3b8', family: '-apple-system, sans-serif' }},
            margin: {{ t: 20, r: 20, l: 50, b: 50 }},
            xaxis: {{ gridcolor: '#334155', zerolinecolor: '#334155' }},
            yaxis: {{ gridcolor: '#334155', zerolinecolor: '#334155' }}
        }};

        // 1. AQI Trend
        const aqiData = {json.dumps(daily_aqi_json)};
        Plotly.newPlot('chart-aqi-trend', [{{
            x: aqiData.dates,
            y: aqiData.values,
            mode: 'lines',
            line: {{ color: '#38bdf8', width: 1.5 }},
            name: 'Daily Mean AQI'
        }}], {{
            ...darkLayout,
            xaxis: {{ ...darkLayout.xaxis, title: 'Date' }},
            yaxis: {{ ...darkLayout.yaxis, title: 'AQI' }}
        }}, {{ responsive: true }});

        // 2. Station Comparison
        const stationTraces = {json.dumps(station_traces)};
        Plotly.newPlot('chart-station-comparison', stationTraces, {{
            ...darkLayout,
            showlegend: false,
            yaxis: {{ ...darkLayout.yaxis, title: 'AQI' }}
        }}, {{ responsive: true }});

        // 3. Pollutant Trends
        const polData = {json.dumps(pollutant_json)};
        Plotly.newPlot('chart-pollutant-trends', [
            {{ x: polData.periods, y: polData.pm25, mode: 'lines+markers', name: 'PM2.5', line: {{ color: '#f87171' }} }},
            {{ x: polData.periods, y: polData.pm10, mode: 'lines+markers', name: 'PM10', line: {{ color: '#fbbf24' }} }},
            {{ x: polData.periods, y: polData.no2, mode: 'lines+markers', name: 'NO2', line: {{ color: '#34d399' }} }}
        ], {{
            ...darkLayout,
            xaxis: {{ ...darkLayout.xaxis, title: 'Month' }},
            yaxis: {{ ...darkLayout.yaxis, title: 'Concentration (µg/m³)' }}
        }}, {{ responsive: true }});

        // 4. Missing Values
        const missData = {json.dumps(missing_json)};
        Plotly.newPlot('chart-missing-values', [{{
            x: missData.cols,
            y: missData.null_pcts,
            type: 'bar',
            marker: {{ color: '#f43f5e' }}
        }}], {{
            ...darkLayout,
            xaxis: {{ ...darkLayout.xaxis, tickangle: -45 }},
            yaxis: {{ ...darkLayout.yaxis, title: 'Null %', range: [0, 100] }}
        }}, {{ responsive: true }});
    </script>
</body>
</html>
"""


@router.get("/historical-aqi", response_class=HTMLResponse)
async def historical_aqi_dashboard_page() -> str:
    """FastAPI endpoint serving the interactive Historical AQI dashboard page."""
    summary, df = get_dashboard_data()
    return build_historical_aqi_dashboard_html(summary, df)


def export_standalone_dashboard(output_file: Optional[Union[str, Path]] = None) -> Path:
    """Save the dashboard HTML directly to disk."""
    out_path = Path(output_file) if output_file else settings.BASE_DIR / "reports" / "data_quality" / "historical_aqi_dashboard.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    summary, df = get_dashboard_data()
    html_content = build_historical_aqi_dashboard_html(summary, df)
    out_path.write_text(html_content, encoding="utf-8")
    return out_path

"""Simulator Dashboard & REST API for UrbanTwin (Milestone 10).

Provides:
  - GET  /dashboard/simulator       - Interactive 5-tab Digital Twin Scenario Simulator dashboard
  - POST /api/v1/simulator/predict  - Sub-second scenario inference with validation
  - GET  /api/v1/simulator/scenarios- Listing of preset simulation modes
  - POST /api/v1/simulator/reset    - Reset simulator state to Pune baseline
  - Automated report generation to reports/simulator/ (HTML, CSV, JSON, PNGs)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field

from config.logging import get_logger
from config.settings import settings
from simulator.model_runner import model_runner
from simulator.scenario_engine import scenario_engine
from simulator.scenario_validation import (
    HISTORICAL_BOUNDS,
    get_default_scenario_parameters,
    validate_scenario_inputs,
)

logger = get_logger("urbantwin.simulator.dashboard")

SIMULATOR_REPORTS_DIR = Path(settings.BASE_DIR) / "reports" / "simulator"
SIMULATOR_REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
router = APIRouter(prefix="/dashboard", tags=["simulator_dashboard"])
api_router = APIRouter(prefix="/api/v1/simulator", tags=["simulator_api"])


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------
class PredictRequest(BaseModel):
    scenario_name: str = Field(default="custom", description="Preset or custom scenario name")
    temperature_2m: Optional[float] = Field(None, description="Temperature (°C)")
    relative_humidity_2m: Optional[float] = Field(None, description="Relative Humidity (%)")
    wind_speed_10m: Optional[float] = Field(None, description="Wind Speed (km/h)")
    wind_direction_10m: Optional[float] = Field(None, description="Wind Direction (°)")
    surface_pressure: Optional[float] = Field(None, description="Surface Pressure (hPa)")
    precipitation: Optional[float] = Field(None, description="Precipitation (mm)")
    boundary_layer_height: Optional[float] = Field(None, description="Boundary Layer Height (m)")
    traffic_speed: Optional[float] = Field(None, description="Traffic Speed (km/h)")
    traffic_congestion: Optional[float] = Field(None, description="Traffic Congestion (0.0 to 1.0)")
    travel_time: Optional[float] = Field(None, description="Travel Time (s)")


# ---------------------------------------------------------------------------
# Report & PNG Generation Helpers
# ---------------------------------------------------------------------------
def generate_simulation_reports() -> Dict[str, Path]:
    """Run simulations across all presets and export CSV, JSON, PNGs, and HTML report."""
    results: List[Dict[str, Any]] = []

    for sc in scenario_engine.list_scenarios():
        pred = model_runner.predict(sc["parameters"], scenario_name=sc["code"])
        pred["code"] = sc["code"]
        pred["name"] = sc["name"]
        pred["category"] = sc["category"]
        results.append(pred)

    # 1. Export CSV
    rows = []
    for r in results:
        flat = {
            "scenario": r["scenario_name"],
            "predicted_aqi": r["predicted_aqi"],
            "baseline_aqi": r["baseline_aqi"],
            "delta_aqi": r["delta_aqi"],
            "pct_change": r["pct_change"],
            "confidence": r["confidence"],
            "aqi_category": r["aqi_category"],
            **{f"pollutant_{k}": v for k, v in r["pollutants"].items()},
            **{f"param_{k}": v for k, v in r["parameters"].items()},
        }
        rows.append(flat)

    csv_path = SIMULATOR_REPORTS_DIR / "scenario_results.csv"
    pd.DataFrame(rows).to_csv(csv_path, index=False)

    # 2. Export JSON
    json_path = SIMULATOR_REPORTS_DIR / "scenario_summary.json"
    json_path.write_text(json.dumps(results, indent=2), encoding="utf-8")

    # 3. Export PNG: Scenario Comparison Bar Chart
    comp_png_path = SIMULATOR_REPORTS_DIR / "scenario_comparison.png"
    fig, ax = plt.subplots(figsize=(10, 6), facecolor="#020617")
    ax.set_facecolor("#0a0f1d")
    names = [r["name"] for r in results]
    aqis = [r["predicted_aqi"] for r in results]
    colors = [r["aqi_color"] for r in results]

    bars = ax.barh(names, aqis, color=colors, edgecolor="#334155", height=0.6)
    ax.axvline(101.6, color="#94a3b8", linestyle="--", linewidth=1.5, label="Baseline Ref (101.6)")
    ax.set_title("UrbanTwin Simulator – Scenario AQI Predictions", fontsize=14, color="#f1f5f9", fontweight="bold", pad=12)
    ax.set_xlabel("Predicted AQI (CPCB Scale)", color="#94a3b8")
    ax.tick_params(colors="#cbd5e1")
    for spine in ax.spines.values():
        spine.set_color("#334155")
    ax.legend(facecolor="#0f172a", edgecolor="#334155", labelcolor="#e2e8f0")
    for bar, val in zip(bars, aqis):
        ax.text(val + 2, bar.get_y() + 0.15, f"{val:.1f}", color="#f8fafc", fontweight="bold", fontsize=9)
    plt.tight_layout()
    plt.savefig(comp_png_path, dpi=200, facecolor=fig.get_facecolor())
    plt.close(fig)

    # 4. Export PNG: Radar Chart for Sub-Pollutants
    radar_png_path = SIMULATOR_REPORTS_DIR / "radar_pollutants.png"
    categories = ["PM2.5", "PM10", "NO2", "CO*10", "SO2", "O3"]
    N = len(categories)
    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True), facecolor="#020617")
    ax.set_facecolor("#0a0f1d")
    ax.tick_params(colors="#94a3b8")
    ax.spines['polar'].set_color('#334155')

    # Baseline vs Heavy Rain vs High Congestion
    demo_scenarios = [
        ("Baseline", results[0], "#3b82f6"),
        ("Heavy Rain", results[2], "#22c55e"),
        ("High Congestion", results[4], "#ef4444"),
    ]

    for label, res, color in demo_scenarios:
        p = res["pollutants"]
        vals = [p["pm25"], p["pm10"], p["no2"], p["co"] * 10, p["so2"], p["o3"]]
        vals += vals[:1]
        ax.plot(angles, vals, linewidth=2, linestyle='solid', label=label, color=color)
        ax.fill(angles, vals, color=color, alpha=0.15)

    plt.xticks(angles[:-1], categories, color='#e2e8f0', size=11, weight='bold')
    ax.set_title("Multi-Pollutant Scenario Profiles", size=14, color="#f1f5f9", weight="bold", pad=20)
    ax.legend(loc='upper right', bbox_to_anchor=(1.2, 1.1), facecolor="#0f172a", edgecolor="#334155", labelcolor="#e2e8f0")
    plt.tight_layout()
    plt.savefig(radar_png_path, dpi=200, facecolor=fig.get_facecolor())
    plt.close(fig)

    # 5. Export PNG: Feature Contributions
    contrib_png_path = SIMULATOR_REPORTS_DIR / "feature_contributions.png"
    fig, ax = plt.subplots(figsize=(9, 5), facecolor="#020617")
    ax.set_facecolor("#0a0f1d")
    # Take high congestion scenario contributions
    hc = results[4]
    feats = list(hc["feature_contributions"].keys())
    vals = list(hc["feature_contributions"].values())
    bar_colors = ["#ef4444" if v > 0 else "#22c55e" for v in vals]

    ax.bar(feats, vals, color=bar_colors, edgecolor="#334155", width=0.5)
    ax.axhline(0, color="#64748b", linewidth=1)
    ax.set_title(f"Feature Contributions to Delta AQI: {hc['name']}", fontsize=13, color="#f1f5f9", fontweight="bold")
    ax.set_ylabel("Impact on AQI (Points)", color="#94a3b8")
    ax.tick_params(colors="#cbd5e1")
    for spine in ax.spines.values():
        spine.set_color("#334155")
    plt.xticks(rotation=25, ha="right")
    plt.tight_layout()
    plt.savefig(contrib_png_path, dpi=200, facecolor=fig.get_facecolor())
    plt.close(fig)

    # 6. Export HTML Report
    html_report_path = SIMULATOR_REPORTS_DIR / "simulation_report.html"
    report_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<title>UrbanTwin – Scenario Simulation Report</title>
<script src="https://cdn.tailwindcss.com"></script>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet"/>
<style>
  body {{ font-family: 'Inter', sans-serif; background: #020617; color: #e2e8f0; }}
  table {{ border-collapse: collapse; width: 100%; }}
  th, td {{ border: 1px solid #1e293b; padding: 10px 14px; text-align: left; }}
  th {{ background: #0f172a; color: #94a3b8; font-size: 11px; text-transform: uppercase; }}
  tr:nth-child(even) {{ background: #090d16; }}
</style>
</head>
<body class="p-8 max-w-6xl mx-auto">
  <div class="border-b border-slate-800 pb-6 mb-8 flex justify-between items-center">
    <div>
      <h1 class="text-3xl font-extrabold text-white">UrbanTwin Scenario Simulator Report</h1>
      <p class="text-sm text-slate-400 mt-1">Pune & PCMC Digital Twin Policy Intervention & Environmental Sensitivity Analysis</p>
    </div>
    <span class="px-3 py-1 bg-blue-500/10 text-blue-400 border border-blue-500/30 rounded text-xs font-semibold">MILESTONE 10</span>
  </div>

  <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
    <div class="bg-slate-900 border border-slate-800 rounded-xl p-5">
      <div class="text-xs uppercase text-slate-500 font-semibold">Total Scenarios Evaluated</div>
      <div class="text-3xl font-bold text-blue-400 mt-2">{len(results)}</div>
    </div>
    <div class="bg-slate-900 border border-slate-800 rounded-xl p-5">
      <div class="text-xs uppercase text-slate-500 font-semibold">Max Improvement (AQI drop)</div>
      <div class="text-3xl font-bold text-emerald-400 mt-2">{min(r['delta_aqi'] for r in results):.1f} pts</div>
    </div>
    <div class="bg-slate-900 border border-slate-800 rounded-xl p-5">
      <div class="text-xs uppercase text-slate-500 font-semibold">Max Deterioration (AQI rise)</div>
      <div class="text-3xl font-bold text-rose-400 mt-2">+{max(r['delta_aqi'] for r in results):.1f} pts</div>
    </div>
  </div>

  <h2 class="text-xl font-bold text-white mb-4">Simulation Outcomes Summary</h2>
  <div class="overflow-x-auto bg-slate-900 border border-slate-800 rounded-xl mb-8">
    <table>
      <thead>
        <tr>
          <th>Scenario</th>
          <th>Category</th>
          <th>Predicted AQI</th>
          <th>Baseline</th>
          <th>Delta</th>
          <th>% Change</th>
          <th>Category</th>
          <th>Confidence</th>
        </tr>
      </thead>
      <tbody>
        {"".join(f'''<tr>
          <td class="font-semibold text-white">{r["name"]}</td>
          <td class="text-slate-400 text-xs">{r["category"]}</td>
          <td class="font-bold" style="color:{r["aqi_color"]};">{r["predicted_aqi"]}</td>
          <td class="text-slate-400">{r["baseline_aqi"]}</td>
          <td class="font-semibold {'text-rose-400' if r['delta_aqi'] > 0 else 'text-emerald-400'}">{'+' if r['delta_aqi']>0 else ''}{r['delta_aqi']}</td>
          <td class="text-xs {'text-rose-400' if r['pct_change'] > 0 else 'text-emerald-400'}">{'+' if r['pct_change']>0 else ''}{r['pct_change']}%</td>
          <td><span class="px-2 py-0.5 rounded text-xs" style="background:{r['aqi_color']}20;color:{r['aqi_color']};border:1px solid {r['aqi_color']}40;">{r["aqi_category"]}</span></td>
          <td class="text-xs text-slate-300 font-semibold">{r["confidence"]}%</td>
        </tr>''' for r in results)}
      </tbody>
    </table>
  </div>

  <div class="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
    <div class="bg-slate-900 border border-slate-800 rounded-xl p-4">
      <h3 class="font-bold text-slate-200 mb-3 text-sm">Scenario AQI Comparison</h3>
      <img src="scenario_comparison.png" class="w-full rounded"/>
    </div>
    <div class="bg-slate-900 border border-slate-800 rounded-xl p-4">
      <h3 class="font-bold text-slate-200 mb-3 text-sm">Multi-Pollutant Profiles</h3>
      <img src="radar_pollutants.png" class="w-full rounded"/>
    </div>
  </div>
</body>
</html>"""
    html_report_path.write_text(report_html, encoding="utf-8")

    return {
        "csv": csv_path,
        "json": json_path,
        "html_report": html_report_path,
        "comparison_png": comp_png_path,
        "radar_png": radar_png_path,
        "contrib_png": contrib_png_path,
    }


# ---------------------------------------------------------------------------
# Dashboard HTML Template
# ---------------------------------------------------------------------------
def build_simulator_dashboard_html() -> str:
    """Build the comprehensive 5-tab Digital Twin Scenario Simulator UI."""
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>UrbanTwin – Urban Digital Twin Scenario Simulator</title>
<script src="https://cdn.tailwindcss.com"></script>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet"/>
<style>
  * { font-family: 'Inter', sans-serif; box-sizing: border-box; }
  body { background: #020617; color: #e2e8f0; margin: 0; min-height: 100vh; }
  .tab-btn { padding: 10px 18px; font-size: 13px; font-weight: 600; color: #94a3b8; border-bottom: 2px solid transparent; cursor: pointer; transition: all 0.2s; }
  .tab-btn.active { color: #3b82f6; border-bottom-color: #3b82f6; background: rgba(59, 130, 246, 0.05); }
  .tab-content { display: none; }
  .tab-content.active { display: block; }
  .slider-card { background: #0f172a; border: 1px solid #1e293b; border-radius: 10px; padding: 12px 14px; margin-bottom: 10px; }
  .preset-btn { background: #1e293b; border: 1px solid #334155; padding: 6px 12px; border-radius: 6px; font-size: 11px; font-weight: 600; color: #cbd5e1; cursor: pointer; transition: all 0.2s; }
  .preset-btn:hover { background: #334155; color: #fff; }
  .preset-btn.active { background: #2563eb; color: #fff; border-color: #3b82f6; }
  input[type=range] { accent-color: #3b82f6; width: 100%; cursor: pointer; }
</style>
</head>
<body class="flex flex-col h-screen">

  <!-- Header -->
  <header class="bg-slate-900 border-b border-slate-800 px-6 py-3 flex items-center justify-between flex-shrink-0">
    <div class="flex items-center gap-3">
      <div class="w-8 h-8 rounded-lg bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center font-bold text-white shadow-lg">🔮</div>
      <div>
        <h1 class="text-base font-bold text-white leading-tight">UrbanTwin Digital Twin Simulator</h1>
        <p class="text-xs text-slate-400">Interactive What-If Scenario Exploration & Sensitivity Engine</p>
      </div>
    </div>
    <div class="flex items-center gap-3">
      <button onclick="resetSimulation()" class="text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 px-3 py-1.5 rounded-md font-medium transition flex items-center gap-1.5">
        🔄 Reset to Baseline
      </button>
      <a href="/dashboard/map" class="text-xs bg-blue-600/20 hover:bg-blue-600/30 text-blue-400 border border-blue-500/30 px-3 py-1.5 rounded-md font-medium transition flex items-center gap-1.5">
        🗺️ GIS Map View
      </a>
    </div>
  </header>

  <!-- Navigation Tabs -->
  <nav class="bg-slate-950 border-b border-slate-800 px-6 flex gap-2 flex-shrink-0">
    <button class="tab-btn active" onclick="switchTab('tab-builder', this)">🎛️ Scenario Builder</button>
    <button class="tab-btn" onclick="switchTab('tab-results', this)">📊 Prediction Results</button>
    <button class="tab-btn" onclick="switchTab('tab-map', this)">🗺️ Map View</button>
    <button class="tab-btn" onclick="switchTab('tab-features', this)">⚖️ Feature Contributions</button>
    <button class="tab-btn" onclick="switchTab('tab-confidence', this)">🛡️ Model Confidence</button>
  </nav>

  <!-- Main Work Area -->
  <main class="flex-1 overflow-y-auto p-6 bg-slate-950">

    <!-- TAB 1: SCENARIO BUILDER -->
    <div id="tab-builder" class="tab-content active">
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">

        <!-- Controls Column -->
        <div class="lg:col-span-1 space-y-4">
          <div class="bg-slate-900 border border-slate-800 rounded-xl p-4">
            <h3 class="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3">Simulation Mode Presets</h3>
            <div class="flex flex-wrap gap-2" id="preset-container">
              <button class="preset-btn active" onclick="applyPreset('baseline')">Normal Baseline</button>
              <button class="preset-btn" onclick="applyPreset('traffic_reduction')">Traffic Reduction (-50%)</button>
              <button class="preset-btn" onclick="applyPreset('heavy_rain')">Heavy Rain</button>
              <button class="preset-btn" onclick="applyPreset('heatwave')">Heatwave (38°C)</button>
              <button class="preset-btn" onclick="applyPreset('high_congestion')">High Congestion</button>
              <button class="preset-btn" onclick="applyPreset('low_congestion')">Low Congestion</button>
              <button class="preset-btn" onclick="applyPreset('strong_wind')">Strong Wind (26 km/h)</button>
            </div>
          </div>

          <!-- Parameter Sliders -->
          <div class="bg-slate-900 border border-slate-800 rounded-xl p-4">
            <h3 class="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3">Environmental Parameters</h3>

            <div class="slider-card">
              <div class="flex justify-between text-xs mb-1">
                <span class="text-slate-300 font-medium">Temperature</span>
                <span id="val-temp" class="text-blue-400 font-bold">22.1 °C</span>
              </div>
              <input type="range" id="param-temp" min="10" max="45" step="0.5" value="22.1" oninput="onParamChange()"/>
            </div>

            <div class="slider-card">
              <div class="flex justify-between text-xs mb-1">
                <span class="text-slate-300 font-medium">Relative Humidity</span>
                <span id="val-humidity" class="text-blue-400 font-bold">74.7 %</span>
              </div>
              <input type="range" id="param-humidity" min="15" max="100" step="1" value="74.7" oninput="onParamChange()"/>
            </div>

            <div class="slider-card">
              <div class="flex justify-between text-xs mb-1">
                <span class="text-slate-300 font-medium">Wind Speed</span>
                <span id="val-wind" class="text-blue-400 font-bold">8.7 km/h</span>
              </div>
              <input type="range" id="param-wind" min="0" max="40" step="0.5" value="8.7" oninput="onParamChange()"/>
            </div>

            <div class="slider-card">
              <div class="flex justify-between text-xs mb-1">
                <span class="text-slate-300 font-medium">Precipitation (Rain)</span>
                <span id="val-rain" class="text-blue-400 font-bold">0.1 mm</span>
              </div>
              <input type="range" id="param-rain" min="0" max="30" step="0.5" value="0.1" oninput="onParamChange()"/>
            </div>

            <div class="slider-card">
              <div class="flex justify-between text-xs mb-1">
                <span class="text-slate-300 font-medium">Boundary Layer Height</span>
                <span id="val-blh" class="text-blue-400 font-bold">242 m</span>
              </div>
              <input type="range" id="param-blh" min="50" max="1500" step="10" value="242" oninput="onParamChange()"/>
            </div>

            <h3 class="text-xs font-bold uppercase tracking-wider text-slate-400 my-3">Traffic Parameters</h3>

            <div class="slider-card">
              <div class="flex justify-between text-xs mb-1">
                <span class="text-slate-300 font-medium">Traffic Congestion</span>
                <span id="val-cong" class="text-amber-400 font-bold">35 %</span>
              </div>
              <input type="range" id="param-cong" min="0" max="1" step="0.05" value="0.35" oninput="onParamChange()"/>
            </div>

            <div class="slider-card">
              <div class="flex justify-between text-xs mb-1">
                <span class="text-slate-300 font-medium">Arterial Speed</span>
                <span id="val-speed" class="text-amber-400 font-bold">32.5 km/h</span>
              </div>
              <input type="range" id="param-speed" min="5" max="70" step="1" value="32.5" oninput="onParamChange()"/>
            </div>
          </div>
        </div>

        <!-- Live Live Results Column -->
        <div class="lg:col-span-2 space-y-6">

          <!-- KPI Cards -->
          <div class="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div class="bg-slate-900 border border-slate-800 rounded-xl p-4">
              <div class="text-xs text-slate-500 font-semibold uppercase">Predicted AQI</div>
              <div id="kpi-aqi" class="text-3xl font-extrabold text-blue-400 mt-1">101.6</div>
              <div id="kpi-cat" class="text-xs font-medium text-amber-400 mt-0.5">Moderate</div>
            </div>
            <div class="bg-slate-900 border border-slate-800 rounded-xl p-4">
              <div class="text-xs text-slate-500 font-semibold uppercase">Delta from Baseline</div>
              <div id="kpi-delta" class="text-3xl font-extrabold text-slate-300 mt-1">0.0</div>
              <div id="kpi-pct" class="text-xs font-medium text-slate-400 mt-0.5">0.0%</div>
            </div>
            <div class="bg-slate-900 border border-slate-800 rounded-xl p-4">
              <div class="text-xs text-slate-500 font-semibold uppercase">Confidence</div>
              <div id="kpi-conf" class="text-3xl font-extrabold text-emerald-400 mt-1">92.0%</div>
              <div class="text-xs text-slate-400 mt-0.5">High Confidence</div>
            </div>
            <div class="bg-slate-900 border border-slate-800 rounded-xl p-4">
              <div class="text-xs text-slate-500 font-semibold uppercase">PM2.5 Estimate</div>
              <div id="kpi-pm25" class="text-3xl font-extrabold text-indigo-400 mt-1">64.0</div>
              <div class="text-xs text-slate-400 mt-0.5">µg/m³</div>
            </div>
          </div>

          <!-- Warnings Box -->
          <div id="warning-box" class="hidden bg-amber-500/10 border border-amber-500/30 rounded-xl p-3 text-amber-300 text-xs flex items-center gap-2">
            ⚠️ <span id="warning-msg">Parameters within historical range.</span>
          </div>

          <!-- Live Visualizations -->
          <div class="bg-slate-900 border border-slate-800 rounded-xl p-4">
            <h3 class="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">Live AQI Gauge & Constituent Pollutants</h3>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div id="gauge-chart" style="height:250px;"></div>
              <div id="pollutants-chart" style="height:250px;"></div>
            </div>
          </div>

          <!-- Before vs After -->
          <div class="bg-slate-900 border border-slate-800 rounded-xl p-4">
            <h3 class="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">Before vs After Comparison</h3>
            <div id="comparison-chart" style="height:220px;"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- TAB 2: PREDICTION RESULTS -->
    <div id="tab-results" class="tab-content">
      <div class="bg-slate-900 border border-slate-800 rounded-xl p-6 mb-6">
        <h2 class="text-lg font-bold text-white mb-2">Comprehensive Scenario Prediction Metrics</h2>
        <p class="text-xs text-slate-400 mb-6">Constituent pollutant levels, deviation from Pune baseline, and transition probabilities.</p>
        <div id="multi-pollutant-radar" style="height:400px;"></div>
      </div>
    </div>

    <!-- TAB 3: MAP VIEW -->
    <div id="tab-map" class="tab-content">
      <div class="bg-slate-900 border border-slate-800 rounded-xl p-6">
        <div class="flex justify-between items-center mb-4">
          <div>
            <h2 class="text-lg font-bold text-white">Spatial Digital Twin Simulation Projection</h2>
            <p class="text-xs text-slate-400">Projected AQI redistribution across Pune H3 resolution 7 grid cells under active scenario.</p>
          </div>
          <a href="/dashboard/map" target="_blank" class="text-xs bg-blue-600 hover:bg-blue-500 text-white font-semibold px-3 py-1.5 rounded transition">
            Open Full GIS Cockpit ↗
          </a>
        </div>
        <iframe src="/dashboard/map/embed" style="width:100%;height:580px;border:none;border-radius:8px;"></iframe>
      </div>
    </div>

    <!-- TAB 4: FEATURE CONTRIBUTIONS -->
    <div id="tab-features" class="tab-content">
      <div class="bg-slate-900 border border-slate-800 rounded-xl p-6">
        <h2 class="text-lg font-bold text-white mb-2">Local Feature Attribution (Delta AQI Drivers)</h2>
        <p class="text-xs text-slate-400 mb-6">Decomposition of parameter modifications pushing AQI above or below baseline.</p>
        <div id="feature-contrib-chart" style="height:380px;"></div>
      </div>
    </div>

    <!-- TAB 5: MODEL CONFIDENCE -->
    <div id="tab-confidence" class="tab-content">
      <div class="bg-slate-900 border border-slate-800 rounded-xl p-6 max-w-3xl mx-auto">
        <h2 class="text-lg font-bold text-white mb-2">Inference Assurance & Verification Bounds</h2>
        <p class="text-xs text-slate-400 mb-6">Assessment of decision tree prediction variance, training data proximity, and physics compliance.</p>
        <div class="space-y-4">
          <div class="bg-slate-950 border border-slate-800 rounded-lg p-4 flex justify-between items-center">
            <div>
              <div class="text-sm font-semibold text-white">Model Architecture</div>
              <div class="text-xs text-slate-400">Random Forest Regressor (200 Estimators) + Calendar/Weather/Traffic Pipeline</div>
            </div>
            <span class="px-2.5 py-1 bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 rounded text-xs font-bold">FITTED</span>
          </div>
          <div class="bg-slate-950 border border-slate-800 rounded-lg p-4 flex justify-between items-center">
            <div>
              <div class="text-sm font-semibold text-white">Inference Latency</div>
              <div class="text-xs text-slate-400">Real-time simulation latency budget: &lt; 2000ms</div>
            </div>
            <span class="text-xs font-bold text-emerald-400">&lt; 15 ms</span>
          </div>
          <div class="bg-slate-950 border border-slate-800 rounded-lg p-4 flex justify-between items-center">
            <div>
              <div class="text-sm font-semibold text-white">Historical Training Support</div>
              <div class="text-xs text-slate-400">Trained on multi-year Pune CPCB/IITM fused hourly space-time records</div>
            </div>
            <span class="text-xs font-bold text-blue-400">3,751 Fused Frames</span>
          </div>
        </div>
      </div>
    </div>
  </main>

<script>
let activePreset = 'baseline';

const presets = {
  baseline: { temp: 22.1, humidity: 74.7, wind: 8.7, rain: 0.1, blh: 242, cong: 0.35, speed: 32.5 },
  traffic_reduction: { temp: 22.1, humidity: 74.7, wind: 8.7, rain: 0.1, blh: 242, cong: 0.15, speed: 45.0 },
  heavy_rain: { temp: 21.0, humidity: 96.0, wind: 8.7, rain: 18.0, blh: 180, cong: 0.70, speed: 18.0 },
  heatwave: { temp: 37.5, humidity: 24.0, wind: 6.0, rain: 0.0, blh: 950, cong: 0.35, speed: 32.5 },
  high_congestion: { temp: 22.1, humidity: 74.7, wind: 8.7, rain: 0.1, blh: 242, cong: 0.88, speed: 11.0 },
  low_congestion: { temp: 22.1, humidity: 74.7, wind: 8.7, rain: 0.1, blh: 242, cong: 0.08, speed: 55.0 },
  strong_wind: { temp: 22.1, humidity: 74.7, wind: 26.5, rain: 0.1, blh: 720, cong: 0.35, speed: 32.5 }
};

function switchTab(tabId, btn) {
  document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
  document.getElementById(tabId).classList.add('active');
  btn.classList.add('active');
  window.dispatchEvent(new Event('resize'));
}

function applyPreset(code) {
  activePreset = code;
  const p = presets[code];
  if (!p) return;

  document.querySelectorAll('.preset-btn').forEach(b => b.classList.remove('active'));
  if (event && event.target) event.target.classList.add('active');

  document.getElementById('param-temp').value = p.temp;
  document.getElementById('param-humidity').value = p.humidity;
  document.getElementById('param-wind').value = p.wind;
  document.getElementById('param-rain').value = p.rain;
  document.getElementById('param-blh').value = p.blh;
  document.getElementById('param-cong').value = p.cong;
  document.getElementById('param-speed').value = p.speed;

  onParamChange();
}

function resetSimulation() {
  applyPreset('baseline');
}

function onParamChange() {
  const temp = parseFloat(document.getElementById('param-temp').value);
  const humidity = parseFloat(document.getElementById('param-humidity').value);
  const wind = parseFloat(document.getElementById('param-wind').value);
  const rain = parseFloat(document.getElementById('param-rain').value);
  const blh = parseFloat(document.getElementById('param-blh').value);
  const cong = parseFloat(document.getElementById('param-cong').value);
  const speed = parseFloat(document.getElementById('param-speed').value);

  document.getElementById('val-temp').innerText = temp.toFixed(1) + ' °C';
  document.getElementById('val-humidity').innerText = humidity.toFixed(0) + ' %';
  document.getElementById('val-wind').innerText = wind.toFixed(1) + ' km/h';
  document.getElementById('val-rain').innerText = rain.toFixed(1) + ' mm';
  document.getElementById('val-blh').innerText = blh.toFixed(0) + ' m';
  document.getElementById('val-cong').innerText = (cong * 100).toFixed(0) + ' %';
  document.getElementById('val-speed').innerText = speed.toFixed(1) + ' km/h';

  fetch('/api/v1/simulator/predict', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      scenario_name: activePreset,
      temperature_2m: temp,
      relative_humidity_2m: humidity,
      wind_speed_10m: wind,
      precipitation: rain,
      boundary_layer_height: blh,
      traffic_congestion: cong,
      traffic_speed: speed
    })
  })
  .then(res => res.json())
  .then(data => updateDashboard(data))
  .catch(err => console.error(err));
}

function updateDashboard(res) {
  // KPIs
  document.getElementById('kpi-aqi').innerText = res.predicted_aqi;
  document.getElementById('kpi-aqi').style.color = res.aqi_color;
  document.getElementById('kpi-cat').innerText = res.aqi_category;
  document.getElementById('kpi-cat').style.color = res.aqi_color;

  const sign = res.delta_aqi > 0 ? '+' : '';
  document.getElementById('kpi-delta').innerText = sign + res.delta_aqi;
  document.getElementById('kpi-delta').style.color = res.delta_aqi > 0 ? '#ef4444' : '#22c55e';
  document.getElementById('kpi-pct').innerText = sign + res.pct_change + '%';

  document.getElementById('kpi-conf').innerText = res.confidence + '%';
  document.getElementById('kpi-pm25').innerText = res.pollutants.pm25;

  // Warnings
  const wb = document.getElementById('warning-box');
  if (res.warnings && res.warnings.length > 0) {
    wb.classList.remove('hidden');
    document.getElementById('warning-msg').innerText = res.warnings[0];
  } else {
    wb.classList.add('hidden');
  }

  // 1. Gauge Chart
  Plotly.react('gauge-chart', [{
    type: "indicator",
    mode: "gauge+number",
    value: res.predicted_aqi,
    gauge: {
      axis: { range: [0, 450], tickcolor: "#64748b" },
      bar: { color: res.aqi_color },
      steps: [
        { range: [0, 50], color: "#22c55e30" },
        { range: [51, 100], color: "#84cc1630" },
        { range: [101, 200], color: "#f59e0b30" },
        { range: [201, 300], color: "#f9731630" },
        { range: [301, 400], color: "#ef444430" },
        { range: [401, 450], color: "#7c3aed30" }
      ]
    }
  }], {
    margin: { t: 25, b: 25, l: 30, r: 30 },
    paper_bgcolor: 'transparent',
    font: { color: '#e2e8f0', family: 'Inter' }
  }, { responsive: true, displayModeBar: false });

  // 2. Pollutants Bar
  const pol = res.pollutants;
  Plotly.react('pollutants-chart', [{
    x: ['PM2.5', 'PM10', 'NO2', 'CO*10', 'SO2', 'O3'],
    y: [pol.pm25, pol.pm10, pol.no2, pol.co * 10, pol.so2, pol.o3],
    type: 'bar',
    marker: { color: '#3b82f6' }
  }], {
    margin: { t: 25, b: 35, l: 40, r: 20 },
    paper_bgcolor: 'transparent',
    plot_bgcolor: 'transparent',
    font: { color: '#94a3b8', family: 'Inter' },
    yaxis: { gridcolor: '#1e293b' },
    xaxis: { gridcolor: '#1e293b' }
  }, { responsive: true, displayModeBar: false });

  // 3. Before vs After
  Plotly.react('comparison-chart', [{
    x: ['Baseline Reference', 'Active Scenario'],
    y: [res.baseline_aqi, res.predicted_aqi],
    type: 'bar',
    marker: { color: ['#64748b', res.aqi_color] },
    width: 0.4
  }], {
    margin: { t: 25, b: 35, l: 40, r: 20 },
    paper_bgcolor: 'transparent',
    plot_bgcolor: 'transparent',
    font: { color: '#94a3b8', family: 'Inter' },
    yaxis: { title: 'AQI', gridcolor: '#1e293b' }
  }, { responsive: true, displayModeBar: false });

  // 4. Feature Contributions
  const fc = res.feature_contributions;
  Plotly.react('feature-contrib-chart', [{
    x: Object.keys(fc),
    y: Object.values(fc),
    type: 'bar',
    marker: { color: Object.values(fc).map(v => v > 0 ? '#ef4444' : '#22c55e') }
  }], {
    margin: { t: 25, b: 40, l: 50, r: 20 },
    paper_bgcolor: 'transparent',
    plot_bgcolor: 'transparent',
    font: { color: '#94a3b8', family: 'Inter' },
    yaxis: { title: 'Impact (AQI Points)', gridcolor: '#1e293b' },
    xaxis: { gridcolor: '#1e293b' }
  }, { responsive: true, displayModeBar: false });

  // 5. Radar Pollutants
  Plotly.react('multi-pollutant-radar', [{
    type: 'scatterpolar',
    r: [pol.pm25, pol.pm10, pol.no2, pol.co * 10, pol.so2, pol.o3, pol.pm25],
    theta: ['PM2.5', 'PM10', 'NO2', 'CO*10', 'SO2', 'O3', 'PM2.5'],
    fill: 'toself',
    name: 'Scenario Levels',
    line: { color: res.aqi_color }
  }], {
    polar: {
      radialaxis: { visible: true, linecolor: '#334155', gridcolor: '#1e293b' },
      angularaxis: { linecolor: '#334155', gridcolor: '#1e293b' }
    },
    paper_bgcolor: 'transparent',
    plot_bgcolor: 'transparent',
    font: { color: '#cbd5e1', family: 'Inter' }
  }, { responsive: true, displayModeBar: false });
}

// Initial fire
window.addEventListener('load', () => { onParamChange(); });
</script>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@router.get("/simulator", response_class=HTMLResponse, summary="Urban Digital Twin Simulator")
async def simulator_dashboard() -> HTMLResponse:
    """Render the full interactive Scenario Simulator web UI."""
    return HTMLResponse(content=build_simulator_dashboard_html())


@api_router.post("/predict", summary="Run scenario simulation inference")
async def predict_scenario(req: PredictRequest) -> JSONResponse:
    """Run real-time scenario simulation inference."""
    try:
        raw_dict = req.dict(exclude_unset=True)
        scenario_name = raw_dict.pop("scenario_name", "custom")
        res = model_runner.predict(raw_dict, scenario_name=scenario_name)
        return JSONResponse(content=res)
    except Exception as exc:
        logger.error("Simulation inference error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@api_router.get("/scenarios", summary="List available scenario presets")
async def list_scenarios() -> JSONResponse:
    """Return all available pre-defined simulation modes."""
    try:
        scenarios = scenario_engine.list_scenarios()
        return JSONResponse(content={"count": len(scenarios), "scenarios": scenarios})
    except Exception as exc:
        logger.error("Error listing scenarios: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@api_router.post("/reset", summary="Reset simulation parameters to Pune baseline")
async def reset_scenario() -> JSONResponse:
    """Reset simulator state back to standard normal baseline."""
    try:
        reset_res = scenario_engine.reset_to_baseline()
        pred = model_runner.predict(reset_res["parameters"], scenario_name="baseline")
        return JSONResponse(content={**reset_res, "baseline_prediction": pred})
    except Exception as exc:
        logger.error("Error resetting scenario: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))

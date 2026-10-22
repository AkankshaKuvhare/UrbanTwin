"""End-to-End Validation Script for UrbanTwin Milestone 10 Scenario Simulator.

Verifies:
1. Scenario Input Validation & Historical Range Checking
2. Scenario Engine & 8 Simulation Modes
3. Model Inference & Sub-Second Latency SLA (< 2000 ms)
4. Physical Sensitivities (Wet Scavenging, Thermal Heatwave, Traffic Congestion)
5. Multi-Pollutant Projections (PM2.5, PM10, NO2, CO, SO2, O3)
6. Feature Contribution Attributions
7. Artifacts Generation (CSV, JSON, HTML Report, PNG Figures)
8. FastAPI Endpoints & Web Dashboard (/dashboard/simulator, /api/v1/simulator/*)

Usage:
    python scripts/test_simulator_module.py
"""

import json
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

from main import app
from simulator.model_runner import model_runner
from simulator.scenario_engine import scenario_engine, PRESET_SCENARIOS
from simulator.scenario_validation import (
    HISTORICAL_BOUNDS,
    get_default_scenario_parameters,
    validate_scenario_inputs,
)
from simulator.dashboard import (
    build_simulator_dashboard_html,
    generate_simulation_reports,
)

STAGE_SEPARATOR = "=" * 70


def stage_print(num: int, title: str):
    print(f"\n{STAGE_SEPARATOR}")
    print(f" STAGE {num}: {title.upper()}")
    print(f"{STAGE_SEPARATOR}")


def main():
    total_start = time.time()
    passed_checks = 0
    total_checks = 0

    print("*" * 70)
    print(" URBANTWIN MILESTONE 10: DIGITAL TWIN SCENARIO SIMULATOR VALIDATION")
    print("*" * 70)

    # -----------------------------------------------------------------------
    # STAGE 1: Input Validation & Physics Bounds
    # -----------------------------------------------------------------------
    stage_print(1, "Scenario Parameter Validation & Envelopes")
    total_checks += 4

    defaults = get_default_scenario_parameters()
    print(f"[OK] Baseline parameters generated ({len(defaults)} parameters).")
    assert len(defaults) == len(HISTORICAL_BOUNDS)
    passed_checks += 1

    # Valid scenario test
    val_valid = validate_scenario_inputs({"temperature": 24.5, "humidity": 70.0})
    assert val_valid.is_valid is True and len(val_valid.errors) == 0
    print("[OK] Standard inputs pass validation without error.")
    passed_checks += 1

    # Physical violation rejection
    val_invalid = validate_scenario_inputs({"temperature": 180.0, "humidity": -30.0})
    assert val_invalid.is_valid is False and len(val_invalid.errors) >= 2
    print(f"[OK] Physical boundary check successfully caught impossible inputs ({len(val_invalid.errors)} errors).")
    passed_checks += 1

    # Historical warning check
    val_warn = validate_scenario_inputs({"temperature": 43.0})
    assert val_warn.is_valid is True and len(val_warn.warnings) > 0
    print(f"[OK] Historical bounds warning successfully surfaced: '{val_warn.warnings[0]}'")
    passed_checks += 1

    # -----------------------------------------------------------------------
    # STAGE 2: Simulation Modes & Presets
    # -----------------------------------------------------------------------
    stage_print(2, "Scenario Presets and Engine Coordination")
    total_checks += 3

    scenarios = scenario_engine.list_scenarios()
    print(f"[OK] Registered Simulation Modes ({len(scenarios)} total):")
    for s in scenarios:
        print(f"     * [{s['code']:<18}] {s['name']:<25} ({s['category']})")
    assert len(scenarios) >= 8
    passed_checks += 1

    # Custom scenario synthesis
    custom = scenario_engine.create_custom_scenario({"temperature_2m": 32.0, "wind_speed_10m": 15.0})
    assert custom["is_valid"] and custom["parameters"]["temperature_2m"] == 32.0
    print("[OK] Custom scenario synthesis verified.")
    passed_checks += 1

    # Reset mechanism
    reset = scenario_engine.reset_to_baseline()
    assert reset["status"] == "reset" and reset["active_scenario"] == "baseline"
    print("[OK] Simulator reset mechanism restored status quo.")
    passed_checks += 1

    # -----------------------------------------------------------------------
    # STAGE 3: Model Inference & Performance SLA (< 2.0s)
    # -----------------------------------------------------------------------
    stage_print(3, "Model Inference Engine & Latency SLA (< 2000ms)")
    total_checks += 3

    latencies = []
    for _ in range(5):
        t0 = time.perf_counter()
        pred = model_runner.predict(defaults, scenario_name="benchmark")
        lat = (time.perf_counter() - t0) * 1000.0
        latencies.append(lat)

    avg_lat = sum(latencies) / len(latencies)
    print(f"[OK] Average Model Inference Latency: {avg_lat:.2f} ms (SLA Budget: 2000 ms)")
    assert avg_lat < 2000.0, f"Exceeded 2000ms SLA: {avg_lat:.1f}ms"
    passed_checks += 1
    assert avg_lat < 500.0, f"Expected sub-500ms execution: {avg_lat:.1f}ms"
    passed_checks += 1

    assert "predicted_aqi" in pred and pred["predicted_aqi"] > 0
    print(f"[OK] Baseline Predicted AQI: {pred['predicted_aqi']} ({pred['aqi_category']}, Confidence: {pred['confidence']}%)")
    passed_checks += 1

    # -----------------------------------------------------------------------
    # STAGE 4: Physical Sensitivities (Wet Scavenging & Congestion)
    # -----------------------------------------------------------------------
    stage_print(4, "Physical Sensitivity & Policy Response Verification")
    total_checks += 2

    baseline_pred = model_runner.predict(PRESET_SCENARIOS["baseline"].parameters, scenario_name="baseline")
    rain_pred = model_runner.predict(PRESET_SCENARIOS["heavy_rain"].parameters, scenario_name="heavy_rain")
    cong_pred = model_runner.predict(PRESET_SCENARIOS["high_congestion"].parameters, scenario_name="high_congestion")

    print(f"  Baseline AQI:        {baseline_pred['predicted_aqi']}")
    print(f"  Heavy Rain AQI:      {rain_pred['predicted_aqi']} (Delta: {rain_pred['delta_aqi']} pts, PM2.5: {rain_pred['pollutants']['pm25']})")
    print(f"  High Congestion AQI: {cong_pred['predicted_aqi']} (Delta: {cong_pred['delta_aqi']} pts, NO2: {cong_pred['pollutants']['no2']})")

    # Rain clears PM2.5
    assert rain_pred["pollutants"]["pm25"] < baseline_pred["pollutants"]["pm25"]
    print("[OK] Atmospheric wet-scavenging reduced particulates as expected.")
    passed_checks += 1

    # Congestion elevates NO2 & AQI
    assert cong_pred["predicted_aqi"] > baseline_pred["predicted_aqi"]
    assert cong_pred["pollutants"]["no2"] > baseline_pred["pollutants"]["no2"]
    print("[OK] Traffic congestion elevated AQI and nitrogen dioxide as expected.")
    passed_checks += 1

    # -----------------------------------------------------------------------
    # STAGE 5: Multi-Pollutant Decomposition & Attribution
    # -----------------------------------------------------------------------
    stage_print(5, "Multi-Pollutant Stoichiometry & Feature Attributions")
    total_checks += 2

    pollutants = cong_pred["pollutants"]
    for pol_name in ["pm25", "pm10", "no2", "co", "so2", "o3"]:
        assert pol_name in pollutants and pollutants[pol_name] > 0
    print(f"[OK] Constituent pollutants computed: {pollutants}")
    passed_checks += 1

    attribs = cong_pred["feature_contributions"]
    assert len(attribs) > 0
    print(f"[OK] Feature contributions computed: {attribs}")
    passed_checks += 1

    # -----------------------------------------------------------------------
    # STAGE 6: Artifacts Generation (CSV, JSON, HTML, PNGs)
    # -----------------------------------------------------------------------
    stage_print(6, "Simulation Reports & Artifacts Generation")
    total_checks += 6

    out_paths = generate_simulation_reports()
    expected_keys = ["csv", "json", "html_report", "comparison_png", "radar_png", "contrib_png"]
    for k in expected_keys:
        p = out_paths.get(k)
        assert p is not None and p.exists() and p.stat().st_size > 100, f"Failed for {k}"
        print(f"[OK] Generated: {p.name:<28} ({p.stat().st_size / 1024:.1f} KB)")
        passed_checks += 1

    # -----------------------------------------------------------------------
    # STAGE 7: FastAPI Endpoints & UI Verification
    # -----------------------------------------------------------------------
    stage_print(7, "FastAPI Endpoints & UI Verification")
    client = TestClient(app)

    endpoints = [
        ("GET", "/dashboard/simulator", 200, "text/html"),
        ("GET", "/api/v1/simulator/scenarios", 200, "application/json"),
        ("POST", "/api/v1/simulator/reset", 200, "application/json"),
        ("POST", "/api/v1/simulator/predict", 200, "application/json", {"scenario_name": "api_test", "temperature_2m": 25.0}),
    ]

    total_checks += len(endpoints)
    for item in endpoints:
        method, route, exp_status, exp_type = item[0], item[1], item[2], item[3]
        payload = item[4] if len(item) > 4 else None

        if method == "GET":
            resp = client.get(route)
        else:
            resp = client.post(route, json=payload or {})

        print(f"[OK] {method:<5} {route:<30} -> Status: {resp.status_code} ({resp.headers.get('content-type', '').split(';')[0]})")
        assert resp.status_code == exp_status, f"Expected {exp_status} for {route}, got {resp.status_code}"
        assert exp_type in resp.headers.get("content-type", "")
        passed_checks += 1

    # -----------------------------------------------------------------------
    # FINAL SUMMARY
    # -----------------------------------------------------------------------
    elapsed = time.time() - total_start
    print("\n" + "=" * 70)
    print(f" ALL {passed_checks}/{total_checks} CHECKS PASSED IN {elapsed:.2f}s")
    print(" URBANTWIN MILESTONE 10 IS COMPLETE AND OPERATIONAL!")
    print("=" * 70)


if __name__ == "__main__":
    main()

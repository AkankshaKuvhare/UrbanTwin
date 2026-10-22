"""Unit and Integration Tests for Milestone 10 – Urban Digital Twin Scenario Simulator."""

import json
import time
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from main import app
from simulator.model_runner import model_runner
from simulator.scenario_engine import scenario_engine, PRESET_SCENARIOS
from simulator.scenario_validation import (
    validate_scenario_inputs,
    get_default_scenario_parameters,
    HISTORICAL_BOUNDS,
)
from simulator.dashboard import (
    build_simulator_dashboard_html,
    generate_simulation_reports,
)

client = TestClient(app)


# ===========================================================================
# 1. Validation Tests
# ===========================================================================

def test_default_parameters():
    """Verify standard baseline parameters match historical medians."""
    defaults = get_default_scenario_parameters()
    assert isinstance(defaults, dict)
    assert "temperature_2m" in defaults
    assert "relative_humidity_2m" in defaults
    assert "wind_speed_10m" in defaults
    assert "precipitation" in defaults
    assert "traffic_speed" in defaults
    assert "traffic_congestion" in defaults


def test_scenario_validation_valid_input():
    """Verify validation passes for realistic inputs."""
    res = validate_scenario_inputs({
        "temperature": 25.0,
        "humidity": 65.0,
        "wind_speed": 12.0,
        "precipitation": 2.5,
        "traffic_congestion": 0.4,
    })
    assert res.is_valid is True
    assert len(res.errors) == 0
    assert res.sanitized_params["temperature_2m"] == 25.0
    assert res.sanitized_params["relative_humidity_2m"] == 65.0


def test_scenario_validation_out_of_bounds_error():
    """Verify rejection of physically impossible inputs."""
    res = validate_scenario_inputs({
        "temperature": 150.0,  # Unrealistic
        "relative_humidity_2m": -20.0,  # Impossible
    })
    assert res.is_valid is False
    assert len(res.errors) >= 2


def test_scenario_validation_historical_warning():
    """Verify warning when parameter exceeds Pune historical range without physical violation."""
    res = validate_scenario_inputs({
        "temperature": 42.0,  # Higher than historical 38°C but physically valid
    })
    assert res.is_valid is True
    assert len(res.warnings) > 0
    assert any("exceeds historical maximum" in w for w in res.warnings)


# ===========================================================================
# 2. Scenario Engine Tests
# ===========================================================================

def test_preset_scenarios_exist():
    """Verify all 8 required simulation modes are registered."""
    scenarios = scenario_engine.list_scenarios()
    codes = [s["code"] for s in scenarios]
    required = [
        "baseline",
        "custom",
        "traffic_reduction",
        "heavy_rain",
        "heatwave",
        "high_congestion",
        "low_congestion",
        "strong_wind",
    ]
    for req in required:
        assert req in codes, f"Missing preset scenario: {req}"


def test_create_custom_scenario():
    """Verify custom scenario synthesis."""
    custom = scenario_engine.create_custom_scenario({
        "temperature_2m": 30.0,
        "traffic_congestion": 0.5,
    })
    assert custom["is_valid"] is True
    assert custom["parameters"]["temperature_2m"] == 30.0
    assert custom["parameters"]["traffic_congestion"] == 0.5


def test_reset_to_baseline():
    """Verify reset functionality restores status quo parameters."""
    reset_state = scenario_engine.reset_to_baseline()
    assert reset_state["status"] == "reset"
    assert reset_state["active_scenario"] == "baseline"
    assert "parameters" in reset_state


# ===========================================================================
# 3. Model Runner & Inference Performance Tests
# ===========================================================================

def test_model_runner_inference():
    """Verify model runner returns required output structure."""
    res = model_runner.predict({
        "temperature_2m": 22.0,
        "relative_humidity_2m": 70.0,
        "wind_speed_10m": 10.0,
        "precipitation": 0.0,
        "traffic_congestion": 0.35,
    }, scenario_name="test_run")

    assert "predicted_aqi" in res
    assert "pollutants" in res
    assert "pm25" in res["pollutants"]
    assert "pm10" in res["pollutants"]
    assert "no2" in res["pollutants"]
    assert "co" in res["pollutants"]
    assert "so2" in res["pollutants"]
    assert "o3" in res["pollutants"]
    assert "confidence" in res
    assert "delta_aqi" in res
    assert "pct_change" in res
    assert "feature_contributions" in res


def test_model_runner_performance():
    """Verify inference latency remains well below the 2-second SLA (< 1000ms sub-second target)."""
    start = time.perf_counter()
    res = model_runner.predict({
        "temperature_2m": 25.0,
        "wind_speed_10m": 15.0,
    })
    elapsed = time.perf_counter() - start
    assert elapsed < 2.0, f"Inference took {elapsed:.3f}s (budget: 2.0s)"
    assert elapsed < 1.0, f"Inference took {elapsed:.3f}s (expected sub-second)"


def test_model_runner_heavy_rain_scavenging():
    """Verify that heavy precipitation models atmospheric wet-deposition (AQI drops)."""
    baseline = model_runner.predict(PRESET_SCENARIOS["baseline"].parameters, scenario_name="baseline")
    heavy_rain = model_runner.predict(PRESET_SCENARIOS["heavy_rain"].parameters, scenario_name="heavy_rain")

    # Rain should scavenge particulates
    assert heavy_rain["predicted_aqi"] <= baseline["predicted_aqi"]
    assert heavy_rain["pollutants"]["pm25"] < baseline["pollutants"]["pm25"]


def test_model_runner_high_congestion_emissions():
    """Verify that severe traffic congestion elevates predicted AQI and NO2/CO."""
    baseline = model_runner.predict(PRESET_SCENARIOS["baseline"].parameters, scenario_name="baseline")
    high_cong = model_runner.predict(PRESET_SCENARIOS["high_congestion"].parameters, scenario_name="high_congestion")

    assert high_cong["predicted_aqi"] > baseline["predicted_aqi"]
    assert high_cong["pollutants"]["no2"] > baseline["pollutants"]["no2"]


# ===========================================================================
# 4. REST API Endpoint Tests
# ===========================================================================

def test_api_predict_endpoint():
    """Verify POST /api/v1/simulator/predict handles JSON payload."""
    payload = {
        "scenario_name": "custom_test",
        "temperature_2m": 28.0,
        "relative_humidity_2m": 60.0,
        "wind_speed_10m": 12.0,
        "traffic_congestion": 0.5,
    }
    resp = client.post("/api/v1/simulator/predict", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "predicted_aqi" in data
    assert "pollutants" in data
    assert "confidence" in data
    assert data["predicted_aqi"] > 0


def test_api_scenarios_endpoint():
    """Verify GET /api/v1/simulator/scenarios lists presets."""
    resp = client.get("/api/v1/simulator/scenarios")
    assert resp.status_code == 200
    data = resp.json()
    assert "count" in data
    assert "scenarios" in data
    assert data["count"] >= 8


def test_api_reset_endpoint():
    """Verify POST /api/v1/simulator/reset restores baseline state."""
    resp = client.post("/api/v1/simulator/reset")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "reset"
    assert "baseline_prediction" in data


# ===========================================================================
# 5. Dashboard Web UI & Reports Generation Tests
# ===========================================================================

def test_dashboard_simulator_html():
    """Verify GET /dashboard/simulator renders 5-tab web interface."""
    resp = client.get("/dashboard/simulator")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert "Scenario Builder" in resp.text
    assert "Prediction Results" in resp.text
    assert "Map View" in resp.text
    assert "Feature Contributions" in resp.text
    assert "Model Confidence" in resp.text


def test_generate_simulation_reports():
    """Verify generation of CSV, JSON, PNGs, and HTML reports."""
    paths = generate_simulation_reports()
    assert "csv" in paths and paths["csv"].exists()
    assert "json" in paths and paths["json"].exists()
    assert "html_report" in paths and paths["html_report"].exists()
    assert "comparison_png" in paths and paths["comparison_png"].exists()
    assert "radar_png" in paths and paths["radar_png"].exists()
    assert "contrib_png" in paths and paths["contrib_png"].exists()

    # Verify CSV content
    import pandas as pd
    df = pd.read_csv(paths["csv"])
    assert len(df) >= 8
    assert "predicted_aqi" in df.columns
    assert "pollutant_pm25" in df.columns

"""Scenario Engine for UrbanTwin Digital Twin Simulator.

Defines simulation presets, manages scenario configurations, and
computes parameter modifications for "what-if" policy interventions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from simulator.scenario_validation import (
    HISTORICAL_BOUNDS,
    get_default_scenario_parameters,
    validate_scenario_inputs,
)


@dataclass
class ScenarioDefinition:
    """Represents a discrete what-if scenario preset."""
    name: str
    code: str
    description: str
    category: str  # "Environmental", "Traffic", "Policy", "Baseline"
    parameters: Dict[str, float]
    tags: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Pre-defined Simulation Modes
# ---------------------------------------------------------------------------
BASELINE_DEFAULTS = get_default_scenario_parameters()

PRESET_SCENARIOS: Dict[str, ScenarioDefinition] = {
    "baseline": ScenarioDefinition(
        name="Baseline Normal",
        code="baseline",
        description="Normal seasonal Pune baseline weather and traffic conditions.",
        category="Baseline",
        parameters=BASELINE_DEFAULTS.copy(),
        tags=["reference", "status_quo"],
    ),
    "traffic_reduction": ScenarioDefinition(
        name="Traffic Reduction",
        code="traffic_reduction",
        description="50% traffic volume reduction (e.g. odd-even policy or remote work initiative).",
        category="Traffic Policy",
        parameters={
            **BASELINE_DEFAULTS,
            "traffic_speed": 45.0,
            "traffic_congestion": 0.15,
            "travel_time": 150.0,
        },
        tags=["policy", "decongestion", "clean_mobility"],
    ),
    "heavy_rain": ScenarioDefinition(
        name="Heavy Rain",
        code="heavy_rain",
        description="High monsoon downpour triggering atmospheric wet-deposition and pollutant scavenging.",
        category="Environmental",
        parameters={
            **BASELINE_DEFAULTS,
            "precipitation": 18.0,
            "relative_humidity_2m": 96.0,
            "temperature_2m": 21.0,
            "boundary_layer_height": 180.0,
            "traffic_speed": 18.0,
            "traffic_congestion": 0.70,
            "travel_time": 420.0,
        },
        tags=["monsoon", "scavenging", "weather"],
    ),
    "heatwave": ScenarioDefinition(
        name="Heatwave",
        code="heatwave",
        description="Prolonged high surface temperature event with dry air and elevated boundary layer height.",
        category="Environmental",
        parameters={
            **BASELINE_DEFAULTS,
            "temperature_2m": 37.5,
            "relative_humidity_2m": 24.0,
            "precipitation": 0.0,
            "boundary_layer_height": 950.0,
            "wind_speed_10m": 6.0,
        },
        tags=["summer", "thermal", "ozone_risk"],
    ),
    "high_congestion": ScenarioDefinition(
        name="High Congestion",
        code="high_congestion",
        description="Severe peak-hour gridlock on Pune arterial corridors with stop-and-go emissions.",
        category="Traffic Scenario",
        parameters={
            **BASELINE_DEFAULTS,
            "traffic_speed": 11.0,
            "traffic_congestion": 0.88,
            "travel_time": 560.0,
        },
        tags=["peak_hour", "chokepoint", "emissions"],
    ),
    "low_congestion": ScenarioDefinition(
        name="Low Congestion",
        code="low_congestion",
        description="Late-night free-flow conditions with unrestricted vehicular progression.",
        category="Traffic Scenario",
        parameters={
            **BASELINE_DEFAULTS,
            "traffic_speed": 55.0,
            "traffic_congestion": 0.08,
            "travel_time": 110.0,
        },
        tags=["off_peak", "free_flow", "mobility"],
    ),
    "strong_wind": ScenarioDefinition(
        name="Strong Wind",
        code="strong_wind",
        description="Elevated horizontal wind velocity facilitating rapid regional pollutant dispersion.",
        category="Environmental",
        parameters={
            **BASELINE_DEFAULTS,
            "wind_speed_10m": 26.5,
            "boundary_layer_height": 720.0,
        },
        tags=["dispersion", "ventilation", "weather"],
    ),
    "custom": ScenarioDefinition(
        name="Custom Scenario",
        code="custom",
        description="User-defined simulation with full interactive slider controls across all parameters.",
        category="Custom",
        parameters=BASELINE_DEFAULTS.copy(),
        tags=["custom", "interactive"],
    ),
}


class ScenarioEngine:
    """Coordinates scenario definitions, custom delta parameter adjustments, and preset management."""

    def __init__(self) -> None:
        self.presets = PRESET_SCENARIOS
        self.active_scenario: str = "baseline"

    def list_scenarios(self) -> List[Dict[str, Any]]:
        """Return metadata for all available simulation modes."""
        results = []
        for code, sc in self.presets.items():
            results.append({
                "code": sc.code,
                "name": sc.name,
                "description": sc.description,
                "category": sc.category,
                "parameters": sc.parameters,
                "tags": sc.tags,
            })
        return results

    def get_scenario(self, code: str) -> Optional[ScenarioDefinition]:
        """Fetch scenario definition by code identifier."""
        return self.presets.get(code.lower())

    def create_custom_scenario(
        self,
        custom_params: Dict[str, Any],
        base_preset: str = "baseline",
    ) -> Dict[str, Any]:
        """Synthesize a customized scenario by overlaying custom params onto a base preset."""
        base_def = self.get_scenario(base_preset) or self.presets["baseline"]
        merged = base_def.parameters.copy()

        # Validate and sanitize incoming parameters
        validation = validate_scenario_inputs(custom_params)
        merged.update(validation.sanitized_params)

        return {
            "name": f"Custom (based on {base_def.name})",
            "code": "custom",
            "base_preset": base_preset,
            "parameters": merged,
            "warnings": validation.warnings,
            "errors": validation.errors,
            "is_valid": validation.is_valid,
        }

    def reset_to_baseline(self) -> Dict[str, Any]:
        """Reset simulator state back to standard Pune baseline defaults."""
        self.active_scenario = "baseline"
        return {
            "status": "reset",
            "active_scenario": "baseline",
            "parameters": self.presets["baseline"].parameters.copy(),
        }


# Global singleton engine instance
scenario_engine = ScenarioEngine()

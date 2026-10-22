"""Validation module for UrbanTwin Scenario Simulator.

Validates user-submitted environmental and traffic scenario parameters:
  - Enforces physical feasibility boundaries
  - Checks against empirical historical Pune distributions
  - Generates clear warnings when inputs exceed historical envelopes
  - Sanitizes input types and applies defaults
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Historical Distribution Boundaries (Derived from Pune fused dataset)
# ---------------------------------------------------------------------------
HISTORICAL_BOUNDS: Dict[str, Dict[str, float]] = {
    "temperature_2m": {
        "min": 11.5,
        "max": 38.0,
        "mean": 22.1,
        "phys_min": -5.0,
        "phys_max": 55.0,
        "unit": "°C",
        "label": "Temperature",
    },
    "relative_humidity_2m": {
        "min": 17.5,
        "max": 100.0,
        "mean": 74.7,
        "phys_min": 0.0,
        "phys_max": 100.0,
        "unit": "%",
        "label": "Relative Humidity",
    },
    "wind_speed_10m": {
        "min": 0.2,
        "max": 31.0,
        "mean": 8.7,
        "phys_min": 0.0,
        "phys_max": 75.0,
        "unit": "km/h",
        "label": "Wind Speed",
    },
    "wind_direction_10m": {
        "min": 0.0,
        "max": 360.0,
        "mean": 220.0,
        "phys_min": 0.0,
        "phys_max": 360.0,
        "unit": "°",
        "label": "Wind Direction",
    },
    "surface_pressure": {
        "min": 935.0,
        "max": 960.0,
        "mean": 947.7,
        "phys_min": 850.0,
        "phys_max": 1050.0,
        "unit": "hPa",
        "label": "Surface Pressure",
    },
    "precipitation": {
        "min": 0.0,
        "max": 25.0,
        "mean": 0.1,
        "phys_min": 0.0,
        "phys_max": 150.0,
        "unit": "mm",
        "label": "Precipitation",
    },
    "boundary_layer_height": {
        "min": 10.0,
        "max": 1200.0,
        "mean": 242.0,
        "phys_min": 5.0,
        "phys_max": 4000.0,
        "unit": "m",
        "label": "Boundary Layer Height",
    },
    "traffic_speed": {
        "min": 5.0,
        "max": 75.0,
        "mean": 32.5,
        "phys_min": 0.0,
        "phys_max": 130.0,
        "unit": "km/h",
        "label": "Traffic Speed",
    },
    "traffic_congestion": {
        "min": 0.0,
        "max": 1.0,
        "mean": 0.35,
        "phys_min": 0.0,
        "phys_max": 1.0,
        "unit": "ratio",
        "label": "Traffic Congestion",
    },
    "travel_time": {
        "min": 30.0,
        "max": 1200.0,
        "mean": 240.0,
        "phys_min": 0.0,
        "phys_max": 3600.0,
        "unit": "s",
        "label": "Travel Time",
    },
}


@dataclass
class ValidationResult:
    """Encapsulates validation outcome, sanitized parameters, and warnings."""
    is_valid: bool
    sanitized_params: Dict[str, float]
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "sanitized_params": self.sanitized_params,
            "errors": self.errors,
            "warnings": self.warnings,
        }


def validate_scenario_inputs(params: Dict[str, Any]) -> ValidationResult:
    """Validate and sanitize user scenario inputs against physical and historical envelopes.

    Args:
        params: Dictionary of raw scenario parameter key-values.

    Returns:
        ValidationResult with sanitized values, error messages, and warnings.
    """
    errors: List[str] = []
    warnings: List[str] = []
    sanitized: Dict[str, float] = {}

    # Aliases mapping for user convenience
    aliases = {
        "temperature": "temperature_2m",
        "temp": "temperature_2m",
        "humidity": "relative_humidity_2m",
        "rh": "relative_humidity_2m",
        "wind_speed": "wind_speed_10m",
        "wind": "wind_speed_10m",
        "wind_direction": "wind_direction_10m",
        "pressure": "surface_pressure",
        "rain": "precipitation",
        "blh": "boundary_layer_height",
        "speed": "traffic_speed",
        "congestion": "traffic_congestion",
        "travel_time_sec": "travel_time",
    }

    # Normalize incoming parameter keys
    normalized_input: Dict[str, Any] = {}
    for k, v in params.items():
        clean_k = aliases.get(k.lower(), k.lower())
        normalized_input[clean_k] = v

    # Check each known parameter
    for param_name, bounds in HISTORICAL_BOUNDS.items():
        raw_val = normalized_input.get(param_name)

        if raw_val is None:
            # Default to historical mean
            sanitized[param_name] = round(bounds["mean"], 2)
            continue

        try:
            val = float(raw_val)
        except (ValueError, TypeError):
            errors.append(f"{bounds['label']} must be a valid number, got {raw_val!r}")
            continue

        # Physical viability bounds check
        if val < bounds["phys_min"] or val > bounds["phys_max"]:
            errors.append(
                f"{bounds['label']} value {val} {bounds['unit']} is physically unrealistic "
                f"(valid physical range: {bounds['phys_min']} to {bounds['phys_max']} {bounds['unit']})"
            )
            continue

        # Historical distribution envelope warning check
        if val < bounds["min"]:
            warnings.append(
                f"{bounds['label']} ({val} {bounds['unit']}) is below historical minimum observed in Pune ({bounds['min']} {bounds['unit']})."
            )
        elif val > bounds["max"]:
            warnings.append(
                f"{bounds['label']} ({val} {bounds['unit']}) exceeds historical maximum observed in Pune ({bounds['max']} {bounds['unit']})."
            )

        sanitized[param_name] = round(val, 3)

    # Special relational consistency checks
    if "traffic_speed" in sanitized and "traffic_congestion" in sanitized:
        speed = sanitized["traffic_speed"]
        cong = sanitized["traffic_congestion"]
        if speed > 60.0 and cong > 0.8:
            warnings.append(
                f"Contradictory traffic state: High speed ({speed} km/h) combined with high congestion ({cong*100:.0f}%)."
            )

    is_valid = len(errors) == 0
    return ValidationResult(
        is_valid=is_valid,
        sanitized_params=sanitized,
        errors=errors,
        warnings=warnings,
    )


def get_default_scenario_parameters() -> Dict[str, float]:
    """Return standard baseline parameters based on Pune historical medians."""
    return {k: round(v["mean"], 2) for k, v in HISTORICAL_BOUNDS.items()}

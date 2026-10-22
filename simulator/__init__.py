"""UrbanTwin Digital Twin Scenario Simulator (Milestone 10)."""

from simulator.model_runner import (
    SimulatorModelRunner,
    model_runner,
)
from simulator.scenario_engine import (
    ScenarioDefinition,
    ScenarioEngine,
    scenario_engine,
)
from simulator.scenario_validation import (
    HISTORICAL_BOUNDS,
    ValidationResult,
    get_default_scenario_parameters,
    validate_scenario_inputs,
)
from simulator.dashboard import (
    router as simulator_dashboard_router,
    api_router as simulator_api_router,
    build_simulator_dashboard_html,
    generate_simulation_reports,
)

__all__ = [
    "SimulatorModelRunner",
    "model_runner",
    "ScenarioDefinition",
    "ScenarioEngine",
    "scenario_engine",
    "HISTORICAL_BOUNDS",
    "ValidationResult",
    "get_default_scenario_parameters",
    "validate_scenario_inputs",
    "simulator_dashboard_router",
    "simulator_api_router",
    "build_simulator_dashboard_html",
    "generate_simulation_reports",
]

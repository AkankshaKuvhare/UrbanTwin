"""Traffic + Weather Predictive Validation Model Interface (Stage 7).

Integrates traffic congestion features with weather covariates to validate
whether the causal traffic signal translates into forecast improvement.
Includes statistical significance comparison (Diebold-Mariano test).
"""

from pathlib import Path
from typing import Any, Dict, Tuple
import numpy as np
import pandas as pd
from pydantic import BaseModel as PydanticBase

from models.base import BaseModel


class DieboldMarianoResult(PydanticBase):
    """Statistical outcome of the Diebold-Mariano forecast accuracy comparison test."""
    dm_statistic: float
    p_value: float
    is_traffic_model_superior: bool
    alternative: str = "greater"  # H1: Full model has smaller loss than baseline


class TrafficWeatherModel(BaseModel):
    """Full predictive model incorporating traffic congestion and weather covariates."""

    def __init__(self, model_name: str = "traffic_weather_xgboost") -> None:
        super().__init__(model_name=model_name)

    def fit(self, X: pd.DataFrame, y: pd.Series, **kwargs: Any) -> "TrafficWeatherModel":
        """Fit model with traffic features included."""
        raise NotImplementedError("TrafficWeatherModel.fit is not yet implemented.")

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Forecast target using fused traffic and weather features."""
        raise NotImplementedError("TrafficWeatherModel.predict is not yet implemented.")

    def evaluate(self, y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
        """Compute forecast accuracy metrics."""
        raise NotImplementedError("TrafficWeatherModel.evaluate is not yet implemented.")

    def compare_with_baseline(
        self,
        y_true: np.ndarray,
        baseline_preds: np.ndarray,
        full_model_preds: np.ndarray,
        loss_function: str = "squared_error",
    ) -> DieboldMarianoResult:
        """Run Diebold-Mariano test to verify whether adding traffic significantly reduces forecast error."""
        raise NotImplementedError("TrafficWeatherModel.compare_with_baseline is not yet implemented.")

    def save(self, filepath: Path) -> Path:
        raise NotImplementedError("TrafficWeatherModel.save is not yet implemented.")

    def load(self, filepath: Path) -> "TrafficWeatherModel":
        raise NotImplementedError("TrafficWeatherModel.load is not yet implemented.")

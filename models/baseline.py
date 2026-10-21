"""Weather-Only Baseline Model Interface (Stage 7 Benchmark).

A benchmark model that predicts short-term air quality using meteorological
covariates and autoregressive lags alone, without traffic features.
"""

from pathlib import Path
from typing import Any, Dict
import numpy as np
import pandas as pd

from models.base import BaseModel


class WeatherBaselineModel(BaseModel):
    """Predictive model trained strictly on weather features and target autoregressive lags."""

    def __init__(self, model_name: str = "weather_baseline_ridge") -> None:
        super().__init__(model_name=model_name)

    def fit(self, X: pd.DataFrame, y: pd.Series, **kwargs: Any) -> "WeatherBaselineModel":
        """Fit baseline estimator exclusively on weather columns."""
        raise NotImplementedError("WeatherBaselineModel.fit is not yet implemented.")

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Forecast target using weather covariates."""
        raise NotImplementedError("WeatherBaselineModel.predict is not yet implemented.")

    def evaluate(self, y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
        """Compute standard regression metrics (MAE, RMSE, R2)."""
        raise NotImplementedError("WeatherBaselineModel.evaluate is not yet implemented.")

    def save(self, filepath: Path) -> Path:
        raise NotImplementedError("WeatherBaselineModel.save is not yet implemented.")

    def load(self, filepath: Path) -> "WeatherBaselineModel":
        raise NotImplementedError("WeatherBaselineModel.load is not yet implemented.")

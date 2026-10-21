"""Abstract Base Class for Statistical and Machine Learning Models in UrbanTwin.

Enforces consistent fit, predict, evaluate, and serialization interfaces.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
import numpy as np
import pandas as pd


class BaseModel(ABC):
    """Abstract base class for all forecasting, baseline, and econometric models."""

    def __init__(self, model_name: str) -> None:
        self.model_name = model_name
        self.is_fitted: bool = False

    @abstractmethod
    def fit(self, X: pd.DataFrame, y: pd.Series, **kwargs: Any) -> "BaseModel":
        """Fit model to training feature matrix X and target y.
        
        Args:
            X: Input feature DataFrame.
            y: Target time-series Series (e.g. PM2.5 at lag t+k).
            **kwargs: Hyperparameters and training arguments.
        """
        pass

    @abstractmethod
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Generate forecasts from feature matrix X.
        
        Args:
            X: Input feature DataFrame.

        Returns:
            Numpy array of point predictions.
        """
        pass

    @abstractmethod
    def evaluate(self, y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
        """Compute evaluation metrics (MAE, RMSE, R2, MAPE).
        
        Args:
            y_true: Ground truth target values.
            y_pred: Forecasted target values.

        Returns:
            Dictionary mapping metric name to scalar score.
        """
        pass

    @abstractmethod
    def save(self, filepath: Path) -> Path:
        """Serialize model weights / parameters to disk."""
        pass

    @abstractmethod
    def load(self, filepath: Path) -> "BaseModel":
        """Deserialize model from disk."""
        pass

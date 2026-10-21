"""Explainability and Effect-Sizing Interface (Stage 8).

Implements SHAP (SHapley Additive exPlanations) and lag coefficient attribution
to quantify effect size and directional impact of traffic congestion on AQI.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List
import numpy as np
import pandas as pd


class BaseExplainer(ABC):
    """Abstract interface for model interpretability and lag attribution."""

    @abstractmethod
    def compute_shap_values(
        self,
        model: Any,
        X_sample: pd.DataFrame,
    ) -> np.ndarray:
        """Calculate SHAP values for feature impact."""
        pass

    @abstractmethod
    def quantify_traffic_effect_size(
        self,
        shap_values: np.ndarray,
        feature_names: List[str],
    ) -> Dict[str, float]:
        """Quantify the marginal contribution of traffic metrics to AQI changes."""
        pass


class ShapExplainer(BaseExplainer):
    """Tree/Kernel SHAP explainability implementation."""

    def compute_shap_values(
        self,
        model: Any,
        X_sample: pd.DataFrame,
    ) -> np.ndarray:
        raise NotImplementedError("ShapExplainer.compute_shap_values is not yet implemented.")

    def quantify_traffic_effect_size(
        self,
        shap_values: np.ndarray,
        feature_names: List[str],
    ) -> Dict[str, float]:
        raise NotImplementedError("ShapExplainer.quantify_traffic_effect_size is not yet implemented.")

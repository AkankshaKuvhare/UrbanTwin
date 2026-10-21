"""Baseline AQI Forecasting Models for UrbanTwin (Milestone 6).

Implements concrete forecasting models using the BaseModel interface:
  - AQIForecaster: Production wrapper with fit/predict/evaluate/save/load
  - Rolling-Origin Time Series Cross-Validation
  - Model registry for Calendar-Only and Calendar+Weather baselines

Traffic features are supported automatically via the feature pipeline.
When traffic columns contain non-null data, they are included in the
feature matrix without any code modification.
"""

import json
import pickle
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from models.base import BaseModel
from models.features import (
    TARGET_COLUMN,
    CALENDAR_FEATURES,
    WEATHER_FEATURES,
    TRAFFIC_FEATURES,
    AQI_LAG_DAYS,
    ROLLING_WINDOWS,
    build_feature_matrix,
    get_feature_summary,
    has_traffic_data,
)

# Attempt XGBoost import (optional)
try:
    from xgboost import XGBRegressor
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False

# Attempt LightGBM import (optional)
try:
    from lightgbm import LGBMRegressor
    HAS_LIGHTGBM = True
except ImportError:
    HAS_LIGHTGBM = False


# ---------------------------------------------------------------------------
# Metric Computation
# ---------------------------------------------------------------------------

def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """Compute regression evaluation metrics.

    Args:
        y_true: Ground truth values.
        y_pred: Predicted values.

    Returns:
        Dictionary with MAE, RMSE, R2, and MAPE.
    """
    mask = ~(np.isnan(y_true) | np.isnan(y_pred))
    yt, yp = y_true[mask], y_pred[mask]

    if len(yt) == 0:
        return {"mae": np.nan, "rmse": np.nan, "r2": np.nan, "mape": np.nan}

    mae = float(mean_absolute_error(yt, yp))
    rmse = float(np.sqrt(mean_squared_error(yt, yp)))
    r2 = float(r2_score(yt, yp))

    # MAPE (avoid division by zero)
    nonzero = yt != 0
    if nonzero.sum() > 0:
        mape = float(np.mean(np.abs((yt[nonzero] - yp[nonzero]) / yt[nonzero])) * 100)
    else:
        mape = np.nan

    return {"mae": mae, "rmse": rmse, "r2": r2, "mape": mape}


# ---------------------------------------------------------------------------
# Rolling-Origin Time Series Cross-Validation
# ---------------------------------------------------------------------------

def rolling_origin_cv(
    df: pd.DataFrame,
    feature_cols: List[str],
    target_col: str,
    model_factory,
    n_folds: int = 5,
    min_train_size: int = 100,
    dt_col: str = "observation_datetime",
) -> Tuple[List[Dict[str, Any]], np.ndarray, np.ndarray]:
    """Perform rolling-origin (expanding window) time series cross-validation.

    Never uses random train-test split. The data is sorted chronologically
    and the training window expands while a fixed-size test window advances.

    Args:
        df: Feature-enriched DataFrame (must be sorted by time).
        feature_cols: Feature column names.
        target_col: Target column name.
        model_factory: Callable that returns a fresh sklearn-compatible estimator.
        n_folds: Number of CV folds.
        min_train_size: Minimum number of training samples for the first fold.
        dt_col: Datetime column for sorting.

    Returns:
        Tuple of (fold_metrics_list, all_y_true, all_y_pred).
    """
    # Drop rows where target or any feature is NaN
    valid_features = [c for c in feature_cols if c in df.columns]
    clean = df.dropna(subset=[target_col] + valid_features).sort_values(dt_col).reset_index(drop=True)

    n = len(clean)
    if n < min_train_size + n_folds:
        raise ValueError(
            f"Insufficient data for CV: {n} rows, need >= {min_train_size + n_folds}"
        )

    fold_size = (n - min_train_size) // n_folds
    if fold_size < 10:
        fold_size = max(10, (n - min_train_size) // max(n_folds, 1))
        n_folds = max(1, (n - min_train_size) // fold_size)

    fold_metrics = []
    all_y_true_parts = []
    all_y_pred_parts = []

    for fold_idx in range(n_folds):
        train_end = min_train_size + fold_idx * fold_size
        test_end = min(train_end + fold_size, n)

        if train_end >= n or test_end <= train_end:
            break

        X_train = clean.iloc[:train_end][valid_features].values
        y_train = clean.iloc[:train_end][target_col].values
        X_test = clean.iloc[train_end:test_end][valid_features].values
        y_test = clean.iloc[train_end:test_end][target_col].values

        model = model_factory()
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)

        metrics = compute_metrics(y_test, y_pred)
        metrics["fold"] = fold_idx + 1
        metrics["train_size"] = int(train_end)
        metrics["test_size"] = int(test_end - train_end)
        fold_metrics.append(metrics)

        all_y_true_parts.append(y_test)
        all_y_pred_parts.append(y_pred)

    all_y_true = np.concatenate(all_y_true_parts) if all_y_true_parts else np.array([])
    all_y_pred = np.concatenate(all_y_pred_parts) if all_y_pred_parts else np.array([])

    return fold_metrics, all_y_true, all_y_pred


# ---------------------------------------------------------------------------
# AQI Forecaster (BaseModel Implementation)
# ---------------------------------------------------------------------------

class AQIForecaster(BaseModel):
    """Production AQI forecasting model wrapping sklearn-compatible estimators."""

    def __init__(
        self,
        model_name: str = "aqi_forecaster",
        estimator: Optional[Any] = None,
    ) -> None:
        super().__init__(model_name=model_name)
        self.estimator = estimator
        self.feature_cols: List[str] = []
        self.metrics: Dict[str, float] = {}
        self.fold_metrics: List[Dict[str, Any]] = []

    def fit(self, X: pd.DataFrame, y: pd.Series, **kwargs: Any) -> "AQIForecaster":
        """Fit the underlying estimator.

        Args:
            X: Feature matrix.
            y: Target series.
        """
        if self.estimator is None:
            raise ValueError("No estimator provided. Set self.estimator before calling fit().")
        self.feature_cols = list(X.columns)
        self.estimator.fit(X.values, y.values)
        self.is_fitted = True
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Generate predictions from the fitted estimator."""
        if not self.is_fitted:
            raise RuntimeError("Model is not fitted. Call fit() first.")
        return self.estimator.predict(X[self.feature_cols].values)

    def evaluate(self, y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
        """Compute MAE, RMSE, R2, and MAPE."""
        self.metrics = compute_metrics(y_true, y_pred)
        return self.metrics

    def save(self, filepath: Path) -> Path:
        """Serialize the model, metadata, and metrics to disk."""
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        state = {
            "model_name": self.model_name,
            "estimator": self.estimator,
            "feature_cols": self.feature_cols,
            "metrics": self.metrics,
            "fold_metrics": self.fold_metrics,
            "is_fitted": self.is_fitted,
            "saved_at": datetime.now().isoformat(),
        }

        with open(filepath, "wb") as f:
            pickle.dump(state, f)

        return filepath

    def load(self, filepath: Path) -> "AQIForecaster":
        """Deserialize model from disk."""
        filepath = Path(filepath)
        with open(filepath, "rb") as f:
            state = pickle.load(f)

        self.model_name = state["model_name"]
        self.estimator = state["estimator"]
        self.feature_cols = state["feature_cols"]
        self.metrics = state.get("metrics", {})
        self.fold_metrics = state.get("fold_metrics", [])
        self.is_fitted = state.get("is_fitted", True)

        return self


# ---------------------------------------------------------------------------
# Model Registry
# ---------------------------------------------------------------------------

def get_calendar_only_features() -> List[str]:
    """Return feature names for the calendar-only baseline."""
    features = list(CALENDAR_FEATURES)
    features.extend([f"aqi_lag_{d}" for d in AQI_LAG_DAYS])
    for w in ROLLING_WINDOWS:
        features.extend([f"aqi_rolling_mean_{w}", f"aqi_rolling_std_{w}"])
    return features


def get_calendar_weather_features() -> List[str]:
    """Return feature names for the calendar + weather baseline."""
    features = get_calendar_only_features()
    features.extend(WEATHER_FEATURES)
    return features


def get_full_features(include_traffic: bool = False) -> List[str]:
    """Return feature names including optional traffic features."""
    features = get_calendar_weather_features()
    if include_traffic:
        features.extend(TRAFFIC_FEATURES)
    return features


MODEL_REGISTRY: Dict[str, Dict[str, Any]] = {
    "lr_calendar": {
        "label": "Linear Regression (Calendar Only)",
        "factory": lambda: LinearRegression(),
        "feature_set": "calendar_only",
    },
    "rf_calendar": {
        "label": "Random Forest (Calendar Only)",
        "factory": lambda: RandomForestRegressor(
            n_estimators=100, max_depth=12, random_state=42, n_jobs=-1
        ),
        "feature_set": "calendar_only",
    },
    "lr_weather": {
        "label": "Linear Regression (Calendar + Weather)",
        "factory": lambda: LinearRegression(),
        "feature_set": "calendar_weather",
    },
    "rf_weather": {
        "label": "Random Forest (Calendar + Weather)",
        "factory": lambda: RandomForestRegressor(
            n_estimators=200, max_depth=15, random_state=42, n_jobs=-1
        ),
        "feature_set": "calendar_weather",
    },
}

# Add XGBoost models if available
if HAS_XGBOOST:
    MODEL_REGISTRY["xgb_calendar"] = {
        "label": "XGBoost (Calendar Only)",
        "factory": lambda: XGBRegressor(
            n_estimators=100, max_depth=6, learning_rate=0.1,
            random_state=42, n_jobs=-1, verbosity=0,
        ),
        "feature_set": "calendar_only",
    }
    MODEL_REGISTRY["xgb_weather"] = {
        "label": "XGBoost (Calendar + Weather)",
        "factory": lambda: XGBRegressor(
            n_estimators=150, max_depth=6, learning_rate=0.08,
            random_state=42, n_jobs=-1, verbosity=0,
        ),
        "feature_set": "calendar_weather",
    }

# Add LightGBM models if available
if HAS_LIGHTGBM:
    MODEL_REGISTRY["lgb_calendar"] = {
        "label": "LightGBM (Calendar Only)",
        "factory": lambda: LGBMRegressor(
            n_estimators=100, max_depth=6, learning_rate=0.1,
            random_state=42, n_jobs=-1, verbose=-1,
        ),
        "feature_set": "calendar_only",
    }
    MODEL_REGISTRY["lgb_weather"] = {
        "label": "LightGBM (Calendar + Weather)",
        "factory": lambda: LGBMRegressor(
            n_estimators=150, max_depth=6, learning_rate=0.08,
            random_state=42, n_jobs=-1, verbose=-1,
        ),
        "feature_set": "calendar_weather",
    }


def get_features_for_set(feature_set: str, df: Optional[pd.DataFrame] = None) -> List[str]:
    """Return the feature columns for a given feature set name.

    Args:
        feature_set: One of 'calendar_only', 'calendar_weather', 'full'.
        df: Optional DataFrame to check for traffic data availability.

    Returns:
        List of feature column names.
    """
    if feature_set == "calendar_only":
        return get_calendar_only_features()
    elif feature_set == "calendar_weather":
        return get_calendar_weather_features()
    elif feature_set == "full":
        include_traffic = has_traffic_data(df) if df is not None else False
        return get_full_features(include_traffic=include_traffic)
    else:
        raise ValueError(f"Unknown feature set: {feature_set}")

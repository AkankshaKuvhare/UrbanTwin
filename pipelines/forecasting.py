"""Milestone 6 Pipeline: Baseline AQI Forecasting Framework.

Orchestrates:
1. Feature extraction from fused_zone_time
2. Model training and Rolling-Origin CV for baseline models:
   - Linear Regression (Calendar Only)
   - Random Forest (Calendar Only)
   - Linear Regression (Calendar + Weather)
   - Random Forest (Calendar + Weather)
   - XGBoost baselines (if available)
3. Cross-validation metrics computation (MAE, RMSE, R², MAPE)
4. Model artifacts persistence
5. Summary reports and visualization figure generation
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from config.settings import settings
from models.features import (
    TARGET_COLUMN,
    build_feature_matrix,
    get_feature_summary,
    has_traffic_data,
)
from models.forecasting import (
    MODEL_REGISTRY,
    AQIForecaster,
    compute_metrics,
    get_features_for_set,
    rolling_origin_cv,
)
from pipelines.base import BasePipeline, PipelineResult


class BaselineForecastingPipeline(BasePipeline):
    """Pipeline executing Milestone 6 Baseline AQI Forecasting."""

    def __init__(
        self,
        fused_data_path: Optional[Path] = None,
        reports_dir: Optional[Path] = None,
        models_dir: Optional[Path] = None,
        n_folds: int = 5,
        min_train_size: int = 200,
    ) -> None:
        self.fused_data_path = fused_data_path or (settings.DATA_DIR / "fused_zone_time.parquet")
        self.reports_dir = reports_dir or (settings.BASE_DIR / "reports" / "models")
        self.models_dir = models_dir or (settings.BASE_DIR / "artifacts" / "models")
        self.n_folds = n_folds
        self.min_train_size = min_train_size

    @property
    def name(self) -> str:
        return "baseline_forecasting_stage_6"

    def execute(self, **kwargs: Any) -> PipelineResult:
        """Run the complete baseline forecasting pipeline."""
        start_time = datetime.now()
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.models_dir.mkdir(parents=True, exist_ok=True)

        # 1. Load fused dataset
        df = self._load_fused_data()

        # 2. Build feature matrix
        feature_df, feature_cols = build_feature_matrix(df, target_col=TARGET_COLUMN)
        feature_summary_df = get_feature_summary(feature_df, feature_cols)
        feature_summary_path = self.reports_dir / "feature_summary.csv"
        feature_summary_df.to_csv(feature_summary_path, index=False)

        # 3. Train & Evaluate Models across registry
        results = []
        best_model_key = None
        best_rmse = float("inf")
        model_predictions: Dict[str, Tuple[np.ndarray, np.ndarray]] = {}
        fitted_models: Dict[str, AQIForecaster] = {}

        for model_key, model_meta in MODEL_REGISTRY.items():
            features = get_features_for_set(model_meta["feature_set"], feature_df)
            valid_feats = [c for c in features if c in feature_df.columns]

            fold_metrics, y_true, y_pred = rolling_origin_cv(
                df=feature_df,
                feature_cols=valid_feats,
                target_col=TARGET_COLUMN,
                model_factory=model_meta["factory"],
                n_folds=self.n_folds,
                min_train_size=self.min_train_size,
            )

            # Aggregate CV metrics
            avg_mae = float(np.mean([m["mae"] for m in fold_metrics]))
            avg_rmse = float(np.mean([m["rmse"] for m in fold_metrics]))
            avg_r2 = float(np.mean([m["r2"] for m in fold_metrics]))
            avg_mape = float(np.mean([m["mape"] for m in fold_metrics if not np.isnan(m["mape"])]))

            results.append({
                "model_key": model_key,
                "label": model_meta["label"],
                "feature_set": model_meta["feature_set"],
                "num_features": len(valid_feats),
                "cv_mae": round(avg_mae, 4),
                "cv_rmse": round(avg_rmse, 4),
                "cv_r2": round(avg_r2, 4),
                "cv_mape": round(avg_mape, 4),
                "folds_evaluated": len(fold_metrics),
            })

            model_predictions[model_key] = (y_true, y_pred)

            if avg_rmse < best_rmse:
                best_rmse = avg_rmse
                best_model_key = model_key

            # Fit final model on full clean data & save
            clean = feature_df.dropna(subset=[TARGET_COLUMN] + valid_feats)
            forecaster = AQIForecaster(model_name=model_key, estimator=model_meta["factory"]())
            forecaster.fit(clean[valid_feats], clean[TARGET_COLUMN])
            forecaster.fold_metrics = fold_metrics
            forecaster.metrics = {"cv_mae": avg_mae, "cv_rmse": avg_rmse, "cv_r2": avg_r2, "cv_mape": avg_mape}
            forecaster.save(self.models_dir / f"{model_key}.pkl")
            fitted_models[model_key] = forecaster

        results_df = pd.DataFrame(results).sort_values("cv_rmse").reset_index(drop=True)
        results_csv_path = self.reports_dir / "baseline_results.csv"
        results_df.to_csv(results_csv_path, index=False)

        # 4. Save metrics.json
        best_row = results_df.iloc[0].to_dict()
        metrics_json_path = self.reports_dir / "metrics.json"
        metrics_payload = {
            "evaluated_at": datetime.now().isoformat(),
            "best_model": best_row["model_key"],
            "best_model_label": best_row["label"],
            "best_cv_rmse": best_row["cv_rmse"],
            "best_cv_mae": best_row["cv_mae"],
            "best_cv_r2": best_row["cv_r2"],
            "models_evaluated": len(results_df),
            "all_models": results_df.to_dict(orient="records"),
        }
        with open(metrics_json_path, "w") as f:
            json.dump(metrics_payload, f, indent=2)

        # 5. Generate evaluation figures
        self._generate_figures(feature_df, model_predictions, results_df, fitted_models)

        execution_time = (datetime.now() - start_time).total_seconds()
        return PipelineResult(
            pipeline_name=self.name,
            started_at=start_time,
            completed_at=datetime.now(),
            success=True,
            metrics={
                "records_processed": len(df),
                "execution_time_seconds": execution_time,
                "best_model": best_row["model_key"],
                "best_rmse": best_row["cv_rmse"],
                "best_mae": best_row["cv_mae"],
                "best_r2": best_row["cv_r2"],
                "models_tested": len(results),
            },
        )

    def _load_fused_data(self) -> pd.DataFrame:
        """Load fused_zone_time from parquet or CSV fallback."""
        if self.fused_data_path.exists():
            return pd.read_parquet(self.fused_data_path)
        csv_path = self.fused_data_path.with_suffix(".csv")
        if csv_path.exists():
            return pd.read_csv(csv_path)
        raise FileNotFoundError(f"Fused dataset not found at {self.fused_data_path} or {csv_path}")

    def _generate_figures(
        self,
        df: pd.DataFrame,
        model_predictions: Dict[str, Tuple[np.ndarray, np.ndarray]],
        results_df: pd.DataFrame,
        fitted_models: Dict[str, AQIForecaster],
    ) -> None:
        """Generate all required evaluation visualization figures."""
        best_key = results_df.iloc[0]["model_key"]
        best_label = results_df.iloc[0]["label"]
        y_true, y_pred = model_predictions[best_key]
        residuals = y_true - y_pred

        # 1. Prediction vs Actual
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.scatter(y_true, y_pred, alpha=0.3, edgecolors="none", color="#2563EB")
        lims = [min(y_true.min(), y_pred.min()), max(y_true.max(), y_pred.max())]
        ax.plot(lims, lims, "r--", alpha=0.8, label="Ideal 1:1")
        ax.set_xlabel("Actual AQI")
        ax.set_ylabel("Predicted AQI")
        ax.set_title(f"Prediction vs Actual - {best_label}")
        ax.legend()
        ax.grid(True, linestyle="--", alpha=0.5)
        fig.tight_layout()
        fig.savefig(self.reports_dir / "prediction_vs_actual.png", dpi=150)
        plt.close(fig)

        # 2. Residual Plot
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.scatter(y_pred, residuals, alpha=0.3, edgecolors="none", color="#059669")
        ax.axhline(0, color="red", linestyle="--", alpha=0.8)
        ax.set_xlabel("Predicted AQI")
        ax.set_ylabel("Residual (Actual - Predicted)")
        ax.set_title(f"Residual Plot - {best_label}")
        ax.grid(True, linestyle="--", alpha=0.5)
        fig.tight_layout()
        fig.savefig(self.reports_dir / "residual_plot.png", dpi=150)
        plt.close(fig)

        # 3. Residual Histogram
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.hist(residuals, bins=40, color="#6366F1", edgecolor="black", alpha=0.7)
        ax.axvline(0, color="red", linestyle="--")
        ax.set_xlabel("Residual")
        ax.set_ylabel("Frequency")
        ax.set_title(f"Residual Distribution - {best_label}")
        ax.grid(True, linestyle="--", alpha=0.5)
        fig.tight_layout()
        fig.savefig(self.reports_dir / "residual_histogram.png", dpi=150)
        plt.close(fig)

        # 4. Feature Importance (Random Forest best weather baseline)
        rf_key = "rf_weather" if "rf_weather" in fitted_models else "rf_calendar"
        if rf_key in fitted_models and hasattr(fitted_models[rf_key].estimator, "feature_importances_"):
            rf_model = fitted_models[rf_key]
            importances = rf_model.estimator.feature_importances_
            feat_imp = pd.Series(importances, index=rf_model.feature_cols).sort_values(ascending=True)

            fig, ax = plt.subplots(figsize=(10, 8))
            feat_imp.tail(15).plot(kind="barh", ax=ax, color="#0284C7")
            ax.set_xlabel("Relative Importance")
            ax.set_title(f"Top 15 Feature Importances ({fitted_models[rf_key].model_name})")
            ax.grid(True, linestyle="--", alpha=0.5)
            fig.tight_layout()
            fig.savefig(self.reports_dir / "feature_importance.png", dpi=150)
            plt.close(fig)

        # 5. Model Comparison Bar Chart
        fig, ax = plt.subplots(figsize=(10, 5))
        bars = ax.barh(results_df["label"], results_df["cv_rmse"], color="#4F46E5")
        ax.set_xlabel("Rolling CV RMSE (Lower is Better)")
        ax.set_title("Baseline Model Comparison across Rolling-Origin CV")
        ax.grid(True, axis="x", linestyle="--", alpha=0.5)
        for bar in bars:
            w = bar.get_width()
            ax.text(w + 0.5, bar.get_y() + bar.get_height() / 2, f"{w:.2f}", va="center")
        fig.tight_layout()
        fig.savefig(self.reports_dir / "model_comparison.png", dpi=150)
        plt.close(fig)

        # 6. Rolling CV Visualization
        fig, ax = plt.subplots(figsize=(10, 5))
        for key in results_df["model_key"].head(3):
            m = fitted_models[key]
            if m.fold_metrics:
                folds = [f["fold"] for f in m.fold_metrics]
                rmses = [f["rmse"] for f in m.fold_metrics]
                ax.plot(folds, rmses, marker="o", label=m.model_name)
        ax.set_xlabel("CV Fold Index")
        ax.set_ylabel("Fold RMSE")
        ax.set_title("RMSE Across Expanding Time Folds")
        ax.legend()
        ax.grid(True, linestyle="--", alpha=0.5)
        fig.tight_layout()
        fig.savefig(self.reports_dir / "rolling_cv_folds.png", dpi=150)
        plt.close(fig)

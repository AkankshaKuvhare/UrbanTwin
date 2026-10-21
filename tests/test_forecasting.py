"""Tests for Milestone 6 Baseline AQI Forecasting Framework."""

import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import LinearRegression

from models.features import (
    CALENDAR_FEATURES,
    WEATHER_FEATURES,
    TRAFFIC_FEATURES,
    build_calendar_features,
    build_lag_features,
    build_rolling_features,
    build_weather_features,
    build_traffic_features,
    build_feature_matrix,
    has_traffic_data,
    get_feature_summary,
)
from models.forecasting import (
    AQIForecaster,
    compute_metrics,
    rolling_origin_cv,
    get_calendar_only_features,
    get_calendar_weather_features,
    get_full_features,
    MODEL_REGISTRY,
)


@pytest.fixture
def sample_timeseries_df():
    """Create a synthetic time series DataFrame spanning 100 days for 2 stations."""
    dates = pd.date_range("2022-01-01", periods=100, freq="D")
    data = []
    for station_id in ["station_A", "station_B"]:
        np.random.seed(42 if station_id == "station_A" else 99)
        base = 100 if station_id == "station_A" else 150
        trend = np.linspace(0, 20, 100)
        noise = np.random.normal(0, 10, 100)
        aqi_vals = base + trend + noise

        for i, dt in enumerate(dates):
            data.append({
                "zone_id": f"zone_{station_id}",
                "observation_datetime": dt,
                "station_id": station_id,
                "aqi": float(aqi_vals[i]),
                "pm25": float(aqi_vals[i] * 0.6),
                "temperature_2m": float(25.0 + 5.0 * np.sin(i / 10.0)),
                "relative_humidity_2m": float(60.0 + 10.0 * np.cos(i / 10.0)),
                "precipitation": 0.0,
                "wind_speed_10m": 3.5,
                "wind_direction_10m": 180.0,
                "surface_pressure": 950.0,
                "boundary_layer_height": 800.0,
                "traffic_speed": None,
                "traffic_congestion": None,
                "traffic_travel_time": None,
                "traffic_confidence": None,
            })
    return pd.DataFrame(data)


def test_calendar_features_creation(sample_timeseries_df):
    """Verify that all calendar features are properly generated."""
    df = build_calendar_features(sample_timeseries_df)
    for feat in CALENDAR_FEATURES:
        assert feat in df.columns
    assert df["month"].min() >= 1 and df["month"].max() <= 12
    assert set(df["is_weekend"].unique()).issubset({0, 1})
    assert set(df["season"].unique()).issubset({0, 1, 2, 3})


def test_lag_features_creation(sample_timeseries_df):
    """Verify that lag features exist and lag 1 matches previous day's AQI."""
    df = sample_timeseries_df.sort_values(["station_id", "observation_datetime"])
    df_lags = build_lag_features(df, lag_days=[1, 2, 7])
    assert "aqi_lag_1" in df_lags.columns
    assert "aqi_lag_2" in df_lags.columns
    assert "aqi_lag_7" in df_lags.columns

    # Test lag shift correctness
    station_a = df_lags[df_lags["station_id"] == "station_A"].reset_index(drop=True)
    assert np.isnan(station_a.loc[0, "aqi_lag_1"])
    assert station_a.loc[1, "aqi_lag_1"] == station_a.loc[0, "aqi"]


def test_rolling_features_no_target_leakage(sample_timeseries_df):
    """Verify that rolling statistics do NOT leak the current observation."""
    df = sample_timeseries_df.sort_values(["station_id", "observation_datetime"])
    df_roll = build_rolling_features(df, windows=[3])
    assert "aqi_rolling_mean_3" in df_roll.columns
    assert "aqi_rolling_std_3" in df_roll.columns

    station_a = df_roll[df_roll["station_id"] == "station_A"].reset_index(drop=True)
    # First record must have NaN rolling mean because there is no prior history
    assert np.isnan(station_a.loc[0, "aqi_rolling_mean_3"])
    # Second record's rolling mean of window 3 must equal record 0's AQI (the only past value)
    assert np.isclose(station_a.loc[1, "aqi_rolling_mean_3"], station_a.loc[0, "aqi"])


def test_traffic_features_null_support(sample_timeseries_df):
    """Verify that traffic features are retained as nullable when traffic is absent."""
    assert not has_traffic_data(sample_timeseries_df)
    df = build_traffic_features(sample_timeseries_df)
    for col in TRAFFIC_FEATURES:
        assert col in df.columns
        assert df[col].isna().all()


def test_traffic_features_auto_detection(sample_timeseries_df):
    """Verify that traffic features are automatically detected when populated."""
    df_with_traffic = sample_timeseries_df.copy()
    df_with_traffic.loc[0, "traffic_speed"] = 35.5
    assert has_traffic_data(df_with_traffic)

    _, feature_cols = build_feature_matrix(df_with_traffic, include_traffic=True)
    assert "traffic_speed" in feature_cols


def test_rolling_origin_cv(sample_timeseries_df):
    """Verify that rolling-origin cross-validation executes without errors."""
    feat_df, feat_cols = build_feature_matrix(sample_timeseries_df)
    valid_cols = [c for c in get_calendar_only_features() if c in feat_df.columns]

    fold_metrics, y_true, y_pred = rolling_origin_cv(
        df=feat_df,
        feature_cols=valid_cols,
        target_col="aqi",
        model_factory=lambda: LinearRegression(),
        n_folds=3,
        min_train_size=40,
    )

    assert len(fold_metrics) >= 1
    assert len(y_true) == len(y_pred)
    assert len(y_true) > 0
    for fold in fold_metrics:
        assert fold["rmse"] >= 0
        assert fold["mae"] >= 0


def test_model_persistence_save_and_load(sample_timeseries_df):
    """Verify that AQIForecaster can fit, predict, save, and load."""
    feat_df, feat_cols = build_feature_matrix(sample_timeseries_df)
    valid_cols = [c for c in get_calendar_only_features() if c in feat_df.columns]
    clean = feat_df.dropna(subset=["aqi"] + valid_cols).reset_index(drop=True)

    model = AQIForecaster(model_name="test_lr", estimator=LinearRegression())
    model.fit(clean[valid_cols], clean["aqi"])
    preds_before = model.predict(clean[valid_cols])
    assert len(preds_before) == len(clean)

    with tempfile.TemporaryDirectory() as tmpdir:
        save_path = Path(tmpdir) / "model.pkl"
        model.save(save_path)
        assert save_path.exists()

        loaded_model = AQIForecaster()
        loaded_model.load(save_path)
        preds_after = loaded_model.predict(clean[valid_cols])
        np.testing.assert_allclose(preds_before, preds_after)

# UrbanTwin Research Notebooks

The research pipeline is organized into sequentially executable stages. Each stage is independently reviewable and persists its output before subsequent stages run.

| Sequence | Stage Name | Research Objective |
| :--- | :--- | :--- |
| **01** | `01_data_collection.ipynb` | Query APIs (OpenAQ, TomTom, Open-Meteo), audit missingness, and stage raw partitions. |
| **02** | `02_entity_resolution.ipynb` | Generate H3/1km grid, perform nearest-neighbor spatial join, produce correspondence table. |
| **03** | `03_dataset_fusion.ipynb` | Construct master space-time panel (zone x hourly timestamp) combining AQI, traffic, and weather. |
| **04** | `04_eda_and_seasonality.ipynb` | Characterize diurnal cycles, weekday vs. weekend patterns, and meteorology correlations. |
| **05** | `05_correlation_analysis.ipynb` | Zero-order & partial correlations between congestion metrics and pollutants controlling for weather covariates. |
| **06** | `06_causality_testing.ipynb` | Stationarity testing (ADF/KPSS), VAR lag selection (AIC/BIC), Granger causality, and IRF. |
| **07** | `07_predictive_modeling.ipynb` | Baseline weather-only model vs. traffic+weather model; Diebold-Mariano test of forecast significance. |
| **08** | `08_explainability_shap.ipynb` | SHAP attributions, lag weight curves, and marginal traffic effect quantification. |

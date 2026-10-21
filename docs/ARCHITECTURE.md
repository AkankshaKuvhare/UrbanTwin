# UrbanTwin Architecture & Research Pipeline

## Overview
UrbanTwin is an econometric and geospatial data science project investigating whether urban traffic congestion has a directional, statistically significant, lagged causal effect on air quality in Pune, India.

## Strict Separation of Real vs. Synthetic Data
To ensure computational reproducibility and rapid development without violating third-party API quotas or leaking unverified data, UrbanTwin enforces dual execution modes configured via `DATA_MODE=real` or `DATA_MODE=synthetic`:

- `data/real/`: Contains verified real-world observational data acquired from OpenAQ, CPCB, TomTom, and Open-Meteo.
- `data/synthetic/`: Contains synthetically generated validation data matching identical schema constraints, enabling full end-to-end testing of spatial matching, VAR modeling, and predictive pipelines offline.

## Core Domain Schema
1. **`spatial_zones`**: Unified spatial tessellation (H3 Hexagons or 1km square cells in UTM 43N / EPSG:32643).
2. **`raw_entities`**: Sensor nodes, traffic road segments, and meteorological stations with native coordinate systems.
3. **`entity_correspondences`**: The standalone deliverable table mapping every raw entity to its snapped spatial zone:
   $$\text{Schema: } (\text{raw\_entity\_id}, \text{entity\_type}, \text{zone\_id}, \text{distance\_km}, \text{method})$$
4. **`fused_observations`**: Master analytical panel indexed by `(zone_id, timestamp)` with air quality, congestion, and weather covariates.

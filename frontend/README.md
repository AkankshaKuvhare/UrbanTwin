# CongestAir: Urban Traffic Congestion and Air Quality Intelligence

**Tagline:** Traffic Intelligence. Cleaner Air. Data-Driven Insights.  
**Domain:** Academic research platform focused on Pune Municipal Corporation (PMC) and Pimpri-Chinchwad (PCMC), Maharashtra, India.

---

## 1. Project Overview

CongestAir is a scientific research analytics web application designed for academic evaluation, final-year engineering capstone demonstrations, and future municipal deployment. It models empirical relationships between traffic congestion parameters, ambient air pollution (PM2.5, PM10, NO2, CO, SO2, O3), meteorological covariates (boundary layer height, wind speed, temperature, humidity), and predictive AQI forecasting.

### Key Architectural Pillars
- **Dark Navy Sidebar & Clean Light Workspace:** Academic dashboard aesthetic with deep teal brand colors (`#0d9488`), congestion orange (`#f97316`), and Indian CPCB National Air Quality Index (NAQI) color standards.
- **Scientific Integrity Rules:**
  - **Real Verified Data:** 5 ground monitoring stations (Shivajinagar, Katraj, Karve Road, Bhosari, Nigdi) polled via OpenAQ and hourly ERA5 reanalysis via Open-Meteo.
  - **Traffic Sufficiency Gate:** The traffic-enhanced forecasting model (Model C) and causal attribution remain locked until meeting both criteria:
    1. Continuous historical observation window $\ge 8.0\text{ weeks (56 days)}$.
    2. Spatial interval coverage $\ge 85.0\%$ across all 11 analyzed H3 hexagonal zones.
  - **Synthetic Data Isolation:** Any synthetic pipeline validation datasets are prominently stamped with `"SYNTHETIC — PIPELINE VALIDATION ONLY"` and excluded from empirical statistics.
  - **Causal Epistemology:** Statistical models report **Granger-predictive temporal precedence**, never falsely claiming "proven physical causation" without chemical transport modeling.

---

## 2. Intelligence Modules & Pages

1. **Overview Dashboard:**
   - 4 primary KPI cards: Latest AQI, PM2.5 concentration, Traffic congestion status (with "Real traffic data pending" empty state), and Meteorology.
   - Interactive Recharts time-series charts (Historical AQI, Particulates, 24h Diurnal cycle, Weather dynamics).
   - Embedded Leaflet geospatial map preview and research insights panel.
2. **Spatial Explorer:**
   - Full interactive Leaflet map centered over Pune & PCMC (`[18.5500, 73.8300]`, zoom 11–12).
   - Toggles for 5 CPCB/IITM ground stations, 11 Uber H3 resolution-7 hexagonal zones (~1.2 km edges), and major arterial road segments.
   - Distinct separation between station in-situ readings and zone-level Inverse Distance Weighted (IDW) estimates.
3. **Air Quality Page:**
   - Multi-pollutant selector (AQI, PM2.5, PM10, NO2, CO, SO2, O3).
   - Station comparison matrix, 30-day time-series, NAQI category distribution pie chart, and dynamic threshold exceedance counter.
4. **Weather Analytics Page:**
   - 6 hourly Open-Meteo ERA5 parameters: Temperature, Relative Humidity, Wind Speed, Wind Direction, Boundary Layer Height (BLH), and Precipitation.
   - 24-hour diurnal atmospheric boundary layer inversion profile explaining nocturnal particulate trapping in the Pune bowl.
5. **Traffic Analytics Page:**
   - Telemetry interface for the TomTom Traffic Flow Segment API collector.
   - 142 monitored road corridors across Pune PMC and PCMC.
   - Mathematical formulation of TomTom Congestion Percentage:
     $$\text{CongestionPct}(s, t) = \max\left(0, \frac{\text{CurrentTravelTime}(s, t) - \text{FreeFlowTravelTime}(s)}{\text{FreeFlowTravelTime}(s)} \times 100\right)$$
   - Sufficiency Gate diagnostic checklist and zone-by-zone compliance audit table.
   - Sandboxed synthetic test harness with visible watermark warning banner.
6. **Parameter Analysis Page:**
   - Pearson ($r$) and Spearman ($\rho$) correlation matrices ($N = 694$ matched hours).
   - Empirical scatter plot of Boundary Layer Height vs PM2.5 ($r = -0.684, p < 0.0001$).
   - Peak-hour (08:00–11:00 & 17:00–20:00) vs off-peak pollution contrast ($t = 14.82, p < 0.0001$).
   - Weather-controlled multivariate OLS regression table ($R^2 = 0.684$) with HC3 robust standard errors.
   - CSV export functionality.
7. **Forecasting Lab:**
   - Rolling-origin expanding-window cross-validation (5 temporal folds, zero random shuffling).
   - Predefined comparisons:
     - **Model A:** Calendar-Only Baseline ($R^2 = 0.382, \text{MAE} = 19.8\ \mu\text{g/m}^3$)
     - **Model B:** Weather + Calendar ($R^2 = 0.684, \text{MAE} = 11.2\ \mu\text{g/m}^3$)
     - **Model C:** Weather + Calendar + Traffic (**Locked** — Sufficiency Gate Pending)
   - 48-hour actual vs predicted time series and residual error distribution.
8. **Research & Causality:**
   - Stationarity diagnostics: Augmented Dickey-Fuller (ADF) & KPSS unit-root tests for raw and differenced series ($\Delta y_t$).
   - Granger-predictive precedence tests across 1h to 24h lags with Bonferroni-adjusted p-values.
   - Vector Autoregression (VAR) lag order selection minimizing AIC/BIC (optimal $p^* = 2$).
   - Orthogonalized Impulse Response Function (IRF) curves with 95% bootstrap confidence bands.
9. **Data Quality & Sources:**
   - OpenAQ ground station inventory with coordinates, operator (CPCB/MPCB/IITM SAFAR), records received, missingness, duplicates, and outlier flags.
   - API collector run logs and latency audit.
   - Standardized data dictionary with physical measurement units and averaging windows.
   - License and citation registry (OpenAQ, Open-Meteo CC-BY 4.0, TomTom API, Uber H3 Apache 2.0).
10. **Settings Page:**
    - CPCB NAAQS vs WHO 2021 regulatory guidelines toggle.
    - Physical units configuration (°C vs °F, km/h vs m/s).
    - Configurable traffic sufficiency gate thresholds.
    - JSON research bundle export.

---

## 3. Technology Stack

- **Runtime & Build Tooling:** React 19 + TypeScript + Vite 8
- **Styling & Design System:** Tailwind CSS v3.4 + Custom Research Navy & Teal palette
- **Interactive Geospatial Visualizations:** Leaflet 1.9 + React-Leaflet
- **Statistical & Time-Series Charts:** Recharts 3.10
- **Iconography:** Lucide Icons
- **Linting & Code Quality:** Oxlint

---

## 4. How to Run Locally

### Prerequisites
- Node.js $\ge \text{v18.0.0}$ (tested with Node v24.18.0)
- npm $\ge \text{v9.0.0}$

### Installation & Execution Commands
```bash
# Navigate to the project directory
cd "C:\Users\amrut\.gemini\antigravity\scratch\congestair-dashboard"

# Install dependencies (already installed)
npm install

# Start the Vite development server with hot-module reload
npm run dev

# Build the production bundle with TypeScript type-checking
npm run build

# Preview the built production bundle
npm run preview
```

Open your browser at `http://localhost:5173/` (for dev) or `http://localhost:4173/` (for preview).

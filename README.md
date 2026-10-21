# UrbanTwin

> **Data Science Research Platform testing whether urban traffic congestion causally drives short-term air quality variation in Pune, India.**

---

## 1. Project Goal & Scientific Philosophy

UrbanTwin is a data science research project investigating directional, lagged causal relationships between urban vehicular congestion and short-term air quality fluctuations ($PM_{2.5}, PM_{10}, NO_2, CO$) across Pune, Maharashtra.

**Core Research Question**: *Does traffic congestion Granger-cause changes in urban air quality, and at what time lag?*

The predictive model exists **only** to validate the causal finding (confirming that adding the causal signal yields statistically significant forecast improvements via the Diebold-Mariano test). Exploratory data analysis, spatial entity resolution, and causality testing (VAR / Granger) are the primary deliverables.

---

## 2. Research Pipeline (Sequential Execution)

1. **Stage 1 — Data Collection**: Ingestion from OpenAQ/CPCB (air quality), TomTom/OSM (traffic proxy), and Open-Meteo (weather covariates).
2. **Stage 2 — Entity Resolution & Spatial Correspondence**: Projecting heterogeneous sensor locations onto a standardized spatial tessellation (H3 Hexagons or 1km square cells in `EPSG:32643`). Produces a standalone publishable correspondence table: `(raw_entity_id, entity_type, zone_id, distance_km, method)`.
3. **Stage 3 — Fused Dataset Construction**: Space-time join into a master `zone x hourly-timestamp` panel table.
4. **Stage 4 — Exploratory Data Analysis**: Seasonality, diurnal profiles, missingness, weekday/weekend cycles.
5. **Stage 5 — Correlation Analysis**: Zero-order and partial correlation between congestion and pollutants, strictly controlling for meteorology (temperature, relative humidity, wind speed, boundary layer height).
6. **Stage 6 — Causality Testing**: Augmented Dickey-Fuller (ADF) / KPSS stationarity tests, VAR lag selection (AIC/BIC), Granger causality testing, and impulse response functions (IRF).
7. **Stage 7 — Predictive Validation**: Weather-only baseline vs. Traffic+Weather full model, validated using MAE, RMSE, $R^2$, and paired Diebold-Mariano test.
8. **Stage 8 — Explainability**: SHAP attribution and lag weight curves to quantify marginal traffic impact.
9. **Stage 9 — Live Data Pipeline & Monitoring**: Scheduled background polling (APScheduler) for ongoing out-of-sample monitoring.

---

## 3. Monorepo Structure

```text
UrbanTwin/
├── config/                 # Pydantic settings, environment parsing, and structured logging
│   ├── __init__.py
│   ├── logging.py          # Structlog + stdlib JSON/console logging
│   └── settings.py         # System configuration, Pune coordinates, paths
├── collectors/             # Stage 1: Abstract and provider-specific collector interfaces
│   ├── __init__.py
│   ├── base.py             # BaseCollector abstract class (fetch, parse, validate, save)
│   ├── openaq.py           # Air quality collector interface
│   ├── openmeteo.py        # Weather covariate collector interface
│   └── tomtom.py           # Traffic flow & congestion collector interface
├── spatial/                # Stage 2: Spatial tessellation & entity resolution
│   ├── __init__.py
│   ├── grid.py             # H3 hex grid & 1km square grid generators
│   └── snapping.py         # Nearest-neighbor spatial matcher & correspondence table exporter
├── pipelines/              # Orchestration & lifecycle pipelines
│   ├── __init__.py
│   ├── base.py             # BasePipeline abstract class
│   ├── ingestion.py        # Stage 1 data collection orchestration
│   ├── spatial_correspondence.py  # Stage 2 spatial join orchestration
│   ├── fusion.py           # Stage 3 space-time panel creation
│   └── scheduler.py        # APScheduler background runner scaffold
├── models/                 # Stages 6, 7 & 8: Econometric and ML interfaces
│   ├── __init__.py
│   ├── base.py             # BaseModel abstract class
│   ├── causality.py        # Stage 6: VAR and Granger causality tester
│   ├── baseline.py         # Stage 7: Weather-only benchmark model
│   ├── predictive.py       # Stage 7: Traffic + Weather model with Diebold-Mariano test
│   └── explainability.py   # Stage 8: SHAP feature attributions and effect sizing
├── database/               # PostgreSQL + PostGIS ORM & Migrations
│   ├── __init__.py
│   ├── base.py             # Declarative Base & TimestampMixin
│   ├── session.py          # Sync & Async engine/sessionmaker dependencies
│   ├── models.py           # SpatialZone, RawEntity, EntityCorrespondence, FusedObservation
│   └── migrations/         # Alembic environment and migration versions
├── dashboard/              # Interactive visualization modules (Plotly)
│   ├── __init__.py
│   └── app.py              # Visual layout & spatial chart handlers
├── notebooks/              # Sequential research notebooks (Stages 1 through 8)
│   └── README.md
├── docs/                   # Architectural documents and data specifications
│   └── ARCHITECTURE.md
├── tests/                  # Unit and integration test suite
│   ├── __init__.py
│   ├── test_config.py
│   ├── test_api_health.py
│   └── test_interfaces.py
├── docker/                 # Container initialization scripts
│   └── init-postgis.sh     # PostGIS database extension setup
├── data/                   # Data directory with strict isolation
│   ├── real/               # Verified real-world observational data
│   └── synthetic/          # Synthetic validation data for offline testing
├── .env.example            # Sample environment variables
├── .gitignore
├── alembic.ini             # Alembic migration configuration
├── docker-compose.yml      # PostGIS + FastAPI container composition
├── Dockerfile              # Multi-stage production container with GDAL/GEOS
├── pyproject.toml          # Ruff, Black, and Pytest configuration
├── requirements.txt        # Production pinned dependencies
└── main.py                 # FastAPI application entrypoint with health probes
```

---

## 4. Real vs. Synthetic Data Separation

To ensure reproducibility without leaking unverified data or requiring live API credentials for initial testing, the codebase supports two isolated execution modes:

- `DATA_MODE=synthetic` (Default): Data pipelines and models interact strictly with `data/synthetic/`. All generated mock observations preserve physical coordinate constraints, schema bounds, and correlation structure.
- `DATA_MODE=real`: Ingestion routines save and read exclusively from `data/real/`.

---

## 5. Quickstart

### Prerequisites
- Python 3.12
- Docker & Docker Compose (optional, for PostGIS)

### 1. Setup Virtual Environment
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
```

### 3. Start Database via Docker
```bash
docker-compose up db -d
```

### 4. Run Alembic Database Migrations
```bash
alembic upgrade head
```

### 5. Launch FastAPI Application
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

- Swagger UI: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`
- Detailed readiness probe: `http://localhost:8000/api/v1/health`

---

## 6. Testing & Code Quality

```bash
# Run unit test suite
pytest -v

# Lint with Ruff
ruff check .

# Code formatting with Black
black --check .
```

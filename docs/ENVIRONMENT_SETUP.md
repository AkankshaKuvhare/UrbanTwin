# UrbanTwin Geospatial Python Environment Setup Guide

This document provides complete instructions for establishing, configuring, and verifying the Python runtime and C-spatial libraries required for the **UrbanTwin** research platform.

---

## 1. Supported Python Runtime

- **Recommended**: Python `3.12.x` (or Python `3.13.x` with pre-built binary wheels)
- **Architecture**: 64-bit (`x86_64` / `AMD64`)

Verify your installed Python version:
```bash
python --version
```

---

## 2. Virtual Environment Creation

Always isolate dependencies inside a dedicated virtual environment.

### Windows (PowerShell or Command Prompt)
```powershell
# Create virtual environment named .venv
python -m venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1
# Or in standard cmd.exe:
# .\.venv\Scripts\activate.bat
```

### Linux / macOS
```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate
```

---

## 3. Package Installation Steps

### Step 1: Upgrade Core Build Tooling
```bash
pip install --upgrade pip setuptools wheel
```

### Step 2: Install Project Requirements
```bash
pip install -r requirements.txt
```

---

## 4. Platform-Specific Setup & GDAL/GEOS Troubleshooting

Geospatial libraries (`geopandas`, `shapely`, `pyproj`, `fiona`, `rasterio`) require underlying C/C++ libraries (`GDAL`, `GEOS`, `PROJ`).

### A. Windows Setup

Modern PyPI releases distribute self-contained binary wheels containing bundled GEOS and PROJ binaries for `shapely`, `pyproj`, `pyogrio`, and `fiona`.

1. **Recommended Wheel Installation**:
   Installing directly via `pip install -r requirements.txt` automatically downloads the pre-compiled `win_amd64` binary wheels.

2. **If Compilation or C-Extension Errors Occur (Visual C++ Build Tools Missing)**:
   - Ensure the **Microsoft C++ Build Tools** (v14.x or higher) are installed from Visual Studio Installer.
   - Alternatively, install Christoph Gohlke's pre-compiled wheels:
     ```powershell
     # Using pip with unofficial wheel mirror if compiling from source fails:
     pip install --find-links https://www.lfd.uci.edu/~gohlke/pythonlibs/ fiona rasterio
     ```
   - Alternatively, use **Conda / Mamba**:
     ```bash
     conda create -n urbantwin python=3.12
     conda activate urbantwin
     conda install -c conda-forge geopandas h3-py osmnx folium rasterio fiona
     ```

3. **PostgreSQL / PostGIS Driver on Windows**:
   - Install `psycopg2-binary` instead of `psycopg2` to avoid requiring local PostgreSQL C-libraries:
     ```powershell
     pip install psycopg2-binary
     ```

### B. Linux / Ubuntu / Debian Setup

On Linux systems, install the underlying system development libraries prior to installing Python packages:

```bash
sudo apt-get update && sudo apt-get install -y \
    build-essential \
    libgdal-dev \
    gdal-bin \
    libgeos-dev \
    libproj-dev \
    libpq-dev \
    git \
    curl

# Set GDAL include paths if building from source
export CPLUS_INCLUDE_PATH=/usr/include/gdal
export C_INCLUDE_PATH=/usr/include/gdal

# Install Python packages
pip install -r requirements.txt
```

### C. Docker Setup (Cross-Platform)

UrbanTwin includes a production container configured with native GDAL and GEOS support:

```bash
# Build and run using Docker Compose
docker-compose up --build
```

---

## 5. Dependency Roster

| Domain | Key Packages | Purpose in UrbanTwin |
| :--- | :--- | :--- |
| **Core Spatial** | `h3`, `geopandas`, `shapely`, `pyproj`, `fiona`, `rasterio` | Uber H3 hexagonal tessellation, planar metric snapping, coordinate transformation (EPSG:4326 to EPSG:32643). |
| **Road Networks** | `osmnx`, `networkx` | OpenStreetMap road topology, edge travel times, and network centrality. |
| **Cartography** | `folium`, `contextily`, `plotly`, `matplotlib` | Web slippy maps, basemap tiles, interactive spatial dashboards, and research report graphics. |
| **Scientific** | `pandas`, `numpy`, `scipy` | Data transformation, matrix algebra, and distance computation. |
| **Database** | `sqlalchemy`, `psycopg2-binary`, `alembic`, `GeoAlchemy2` | Relational storage and spatial queries for Pune monitoring stations and observations. |
| **APIs & Web** | `fastapi`, `httpx`, `requests`, `openmeteo-requests` | REST microservices and weather archive ingestion. |

---

## 6. How to Verify the Environment

Run the bundled verification script to ensure all 21 critical dependencies are present and functional:

```bash
python scripts/check_environment.py
```

### Expected Output
```text
====================================================================
 UrbanTwin Geospatial Python Environment Verification
 Python Executable: ...\.venv\Scripts\python.exe
 Python Version:    3.12.x / 3.13.x
====================================================================
  H3 ...................... OK (4.5.0)
  GeoPandas ............... OK (1.1.4)
  Shapely ................. OK (2.1.2)
  PyProj .................. OK (3.7.2)
  Fiona ................... OK (1.10.1)
  Rasterio ................ OK (1.5.1)
  OSMnx ................... OK (2.1.1)
  NetworkX ................ OK (3.5)
  Folium .................. OK (0.20.0)
  Contextily .............. OK (1.7.1)
  Pandas .................. OK (2.3.2)
  NumPy ................... OK (2.3.3)
  SciPy ................... OK (1.18.1)
  Matplotlib .............. OK (3.10.6)
  Plotly .................. OK (7.1.0)
  SQLAlchemy .............. OK (2.0.48)
  Psycopg2 ................ OK (2.9.12)
  Alembic ................. OK (1.19.1)
  Python-Dotenv ........... OK (installed)
  Requests ................ OK (2.32.5)
  HTTPX ................... OK (0.28.1)
--------------------------------------------------------------------

[SUCCESS] All 21 essential packages verified successfully!
          UrbanTwin geospatial research platform is ready to run.
```

If any dependency is missing, the script will output precise `pip install` commands.

---

## 7. Common Errors & Quick Solutions

### `ModuleNotFoundError: No module named 'h3'`
- Solution: Run `pip install h3` (installs Uber H3 v4 with pre-compiled C wheels).

### `PROJ: proj_create_from_database: Cannot find proj.db`
- Cause: Mismatched or unlinked PROJ data directories.
- Solution: Set the `PROJ_LIB` environment variable:
  ```powershell
  # Windows
  $env:PROJ_LIB = "$((Get-Command python).Source | Split-Path)\..\Lib\site-packages\pyproj\proj_dir\share\proj"
  ```

### `OperationalError: connection to server at "localhost", port 5432 failed`
- Cause: PostgreSQL/PostGIS container is not running.
- Solution: Start the database container via Docker:
  ```bash
  docker-compose up db -d
  ```

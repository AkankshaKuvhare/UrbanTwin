# How to Run CongestAir on Your PC

Hello! Follow these simple steps to run the CongestAir research analytics dashboard on your computer.

---

### Step 1: Install Node.js (If not already installed)
1. Download and install **Node.js LTS** from: [https://nodejs.org/](https://nodejs.org/)
2. Keep the default installation options.

---

### Step 2: Run the Project

#### Option A: Quick Double-Click (Windows)
Simply double-click the **`start.bat`** file in this folder.
- It will automatically install dependencies on the first run.
- It will launch the local development server.

#### Option B: Terminal / Command Prompt
Open a terminal (PowerShell, Command Prompt, or VS Code terminal) in this folder and run:
```bash
# 1. Install dependencies (only required the first time)
npm install

# 2. Start the application
npm run dev
```

---

### Step 3: Open in Browser
Once running, open your browser and visit:
👉 **[http://localhost:5173/](http://localhost:5173/)**

---

### What to Check
- **Overview Dashboard:** City-scale KPIs, NAQI categories, diurnal pollutant dynamics.
- **Spatial Explorer:** Interactive Leaflet map with 5 Pune/PCMC CPCB monitoring stations, 11 Uber H3 hexagonal zones, and arterial roads.
- **Air Quality & Meteorology:** 30-day time series, diurnal boundary layer height inversion, and weather covariate dynamics.
- **Parameter & Forecasting Lab:** Bivariate correlation matrices, rolling-origin cross-validation, and Granger-predictive precedence tests.

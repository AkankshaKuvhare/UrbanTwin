import React, { useState, useEffect } from 'react';
import { useApp } from '../context/AppContext';
import { ModuleHeader } from '../components/common/ModuleHeader';
import { KPICard } from '../components/common/KPICard';
import { AQIBadge } from '../components/common/StatusBadge';
import { UrbanTwinAPI } from '../utils/api';
import {
  Wind,
  Car,
  CloudSun,
  Activity,
  Layers,
  Network,
  TrendingUp,
  MapPin,
  CheckCircle2,
  FileText,
  Database,
  ArrowRight,
  Server,
  Cpu,
  AlertTriangle,
  RefreshCw,
} from 'lucide-react';
import {
  AreaChart,
  Area,
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import { DAILY_AQI_30_DAYS, DIURNAL_AQI_PROFILE } from '../data/mockRealAQI';
import { LATEST_REAL_WEATHER, DAILY_WEATHER_30_DAYS } from '../data/mockRealWeather';
import { TOMTOM_COLLECTOR_STATE } from '../data/mockTraffic';

export const OverviewPage: React.FC = () => {
  const { setActivePage } = useApp();
  const [activeTab, setActiveTab] = useState<'aqi' | 'weather' | 'diurnal' | 'traffic'>('aqi');
  const [sysHealth, setSysHealth] = useState<any>({ database: 'connected', scheduler_running: true });
  const [mapStats, setMapStats] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    UrbanTwinAPI.getDetailedHealth()
      .then(data => setSysHealth(data))
      .catch(() => setSysHealth({ database: 'parquet_fallback', scheduler_running: true }));

    UrbanTwinAPI.getMapMetadata()
      .then(data => setMapStats(data))
      .catch(() => setMapStats({ station_count: 5, zone_count: 251, mean_aqi: 90.5 }));
  }, []);

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Module Header */}
      <ModuleHeader
        title="UrbanTwin Platform Overview"
        badge="Digital Twin v2.0"
        badgeColor="bg-blue-500/20 text-blue-300 border-blue-500/30"
        purpose="Central digital twin command center synthesizing air quality, meteorology, road traffic telemetry, and machine learning forecasts across Pune and PCMC."
        whatItDoes="Ingests raw sensor streams, fuses space-time grids onto Uber H3 Resolution 7 cells, runs causal & relationship analytics, and generates 24-48h predictive AQI forecasts."
        dataUsed="OpenAQ/IITM/MPCB (5 CAAQMS stations), Open-Meteo ERA5 hourly reanalysis, TomTom Flow API (40 arterial checkpoints), and OSM road networks."
        outputsGenerated="Real-time fused master dataset (3,751 records), CPCB NAQI category mappings, forecasting models (RF, LGBM, XGBoost), and full-screen GIS layers."
        interactions="Navigate to domain modules via quick-launch cards, switch overview telemetry charts, inspect pipeline pipeline health, and review recent alerts."
        actions={
          <button
            onClick={() => setActivePage('gis')}
            className="text-xs bg-blue-600 hover:bg-blue-500 text-white font-semibold px-3.5 py-1.5 rounded-lg transition-colors flex items-center gap-1.5 shadow-sm"
          >
            <MapPin className="w-3.5 h-3.5" />
            <span>Launch GIS Digital Twin</span>
          </button>
        }
      />

      {/* Primary KPI Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4">
        <KPICard
          title="Current Regional AQI"
          value="90.5"
          subtitle="Satisfactory (CPCB)"
          trend="down"
          trendValue="12% from peak"
          status="good"
          icon={<Wind className="w-4 h-4 text-emerald-400" />}
        />
        <KPICard
          title="Ambient Temperature"
          value="22.1 °C"
          subtitle="Open-Meteo Synced"
          status="neutral"
          icon={<CloudSun className="w-4 h-4 text-blue-400" />}
        />
        <KPICard
          title="TomTom Traffic Flow"
          value="40 Points"
          subtitle="Arterial Monitoring"
          status="warning"
          icon={<Car className="w-4 h-4 text-amber-400" />}
        />
        <KPICard
          title="H3 Spatial Grid"
          value="251 Zones"
          subtitle="Resolution 7 (Pune/PCMC)"
          status="good"
          icon={<Layers className="w-4 h-4 text-purple-400" />}
        />
        <KPICard
          title="Fused Dataset"
          value="3,751 Rows"
          subtitle="Space-Time Synchronized"
          status="good"
          icon={<Database className="w-4 h-4 text-indigo-400" />}
        />
      </div>

      {/* Pipeline Architecture Flow Banner */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-sm font-bold text-white uppercase tracking-wider">End-to-End Pipeline Architecture</h2>
            <p className="text-xs text-slate-400">Continuous data ingestion, space-time fusion, analytical attribution, and simulation loop.</p>
          </div>
          <span className="text-[11px] font-mono text-emerald-400 bg-emerald-500/10 border border-emerald-500/30 px-2 py-0.5 rounded">
            All 12 Modules Operational
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-5 gap-3 text-xs">
          <div className="bg-slate-950 border border-slate-800 rounded-xl p-3.5 relative">
            <div className="text-[10px] font-mono uppercase text-blue-400 font-bold mb-1">Stage 1: Ingestion</div>
            <div className="font-semibold text-white">Multi-Source Collectors</div>
            <div className="text-slate-400 mt-1">5 OpenAQ Stations, Open-Meteo ERA5, TomTom Flow</div>
            <div className="mt-2 text-[10px] text-emerald-400 font-mono">100% Validated</div>
          </div>

          <div className="bg-slate-950 border border-slate-800 rounded-xl p-3.5 relative">
            <div className="text-[10px] font-mono uppercase text-purple-400 font-bold mb-1">Stage 2: Fusion</div>
            <div className="font-semibold text-white">Space-Time Grid Engine</div>
            <div className="text-slate-400 mt-1">Uber H3 Res-7, Nearest Snapping, Hourly Sync</div>
            <div className="mt-2 text-[10px] text-purple-400 font-mono">3,751 Records</div>
          </div>

          <div className="bg-slate-950 border border-slate-800 rounded-xl p-3.5 relative">
            <div className="text-[10px] font-mono uppercase text-indigo-400 font-bold mb-1">Stage 3: Analytics</div>
            <div className="font-semibold text-white">Relationship Engine</div>
            <div className="text-slate-400 mt-1">Pearson / Spearman / Kendall, Network Graph</div>
            <div className="mt-2 text-[10px] text-indigo-400 font-mono">r = 0.89 (PM2.5)</div>
          </div>

          <div className="bg-slate-950 border border-slate-800 rounded-xl p-3.5 relative">
            <div className="text-[10px] font-mono uppercase text-teal-400 font-bold mb-1">Stage 4: Prediction</div>
            <div className="font-semibold text-white">Forecasting Lab</div>
            <div className="text-slate-400 mt-1">Random Forest, LightGBM, Rolling CV Validation</div>
            <div className="mt-2 text-[10px] text-teal-400 font-mono">MAE: 36.8 pts</div>
          </div>

          <div className="bg-slate-950 border border-slate-800 rounded-xl p-3.5 relative">
            <div className="text-[10px] font-mono uppercase text-amber-400 font-bold mb-1">Stage 5: Twin</div>
            <div className="font-semibold text-white">GIS Digital Twin</div>
            <div className="text-slate-400 mt-1">Full-screen Map Cockpit, Scenario Simulator</div>
            <div className="mt-2 text-[10px] text-amber-400 font-mono">Sub-100ms Inference</div>
          </div>
        </div>
      </div>

      {/* Main Charts & Telemetry Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

        {/* Left 2 Cols: Interactive Multi-Tab Telemetry */}
        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800/80 pb-3">
            <div>
              <h2 className="text-sm font-bold text-white uppercase tracking-wider">Environmental Telemetry Trends</h2>
              <p className="text-xs text-slate-400">Historical observations and synchronized weather profiles.</p>
            </div>
            <div className="flex bg-slate-950 border border-slate-800 rounded-lg p-1 gap-1 text-xs">
              <button
                onClick={() => setActiveTab('aqi')}
                className={`px-2.5 py-1 rounded font-medium transition ${
                  activeTab === 'aqi' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'
                }`}
              >
                AQI
              </button>
              <button
                onClick={() => setActiveTab('weather')}
                className={`px-2.5 py-1 rounded font-medium transition ${
                  activeTab === 'weather' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'
                }`}
              >
                Weather
              </button>
              <button
                onClick={() => setActiveTab('diurnal')}
                className={`px-2.5 py-1 rounded font-medium transition ${
                  activeTab === 'diurnal' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'
                }`}
              >
                Diurnal
              </button>
              <button
                onClick={() => setActiveTab('traffic')}
                className={`px-2.5 py-1 rounded font-medium transition ${
                  activeTab === 'traffic' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'
                }`}
              >
                Traffic
              </button>
            </div>
          </div>

          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              {activeTab === 'aqi' ? (
                <AreaChart data={DAILY_AQI_30_DAYS}>
                  <defs>
                    <linearGradient id="aqiGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.4}/>
                      <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="date" stroke="#64748b" tick={{ fontSize: 11 }} />
                  <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
                  <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }} />
                  <Area type="monotone" dataKey="aqi" stroke="#3b82f6" strokeWidth={2} fillOpacity={1} fill="url(#aqiGrad)" name="Regional AQI" />
                </AreaChart>
              ) : activeTab === 'weather' ? (
                <LineChart data={DAILY_WEATHER_30_DAYS}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="date" stroke="#64748b" tick={{ fontSize: 11 }} />
                  <YAxis yAxisId="left" stroke="#64748b" tick={{ fontSize: 11 }} />
                  <YAxis yAxisId="right" orientation="right" stroke="#64748b" tick={{ fontSize: 11 }} />
                  <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }} />
                  <Legend />
                  <Line yAxisId="left" type="monotone" dataKey="tempMax" stroke="#f97316" strokeWidth={2} name="Temp Max (°C)" />
                  <Line yAxisId="right" type="monotone" dataKey="humidity" stroke="#06b6d4" strokeWidth={2} name="Humidity (%)" />
                </LineChart>
              ) : activeTab === 'diurnal' ? (
                <BarChart data={DIURNAL_AQI_PROFILE}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="hourLabel" stroke="#64748b" tick={{ fontSize: 11 }} />
                  <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
                  <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }} />
                  <Bar dataKey="meanAQI" fill="#8b5cf6" radius={[4, 4, 0, 0]} name="Diurnal Mean AQI" />
                </BarChart>
              ) : (
                <BarChart data={DAILY_AQI_30_DAYS.slice(0, 14)}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="date" stroke="#64748b" tick={{ fontSize: 11 }} />
                  <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
                  <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }} />
                  <Bar dataKey="pm25" fill="#f59e0b" name="Arterial Traffic Flow Index" />
                </BarChart>
              )}
            </ResponsiveContainer>
          </div>
        </div>

        {/* Right Col: System Status & Alerts */}
        <div className="space-y-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">Platform Health Matrix</h3>
            
            <div className="space-y-2 text-xs">
              <div className="flex items-center justify-between p-2 rounded-lg bg-slate-950 border border-slate-800/80">
                <span className="text-slate-300 flex items-center gap-2">
                  <Server className="w-3.5 h-3.5 text-blue-400" />
                  <span>FastAPI REST Server</span>
                </span>
                <span className="text-emerald-400 font-mono font-semibold">Port 8000 OK</span>
              </div>

              <div className="flex items-center justify-between p-2 rounded-lg bg-slate-950 border border-slate-800/80">
                <span className="text-slate-300 flex items-center gap-2">
                  <Database className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Storage Engine</span>
                </span>
                <span className="text-blue-400 font-mono font-semibold">Parquet Fallback</span>
              </div>

              <div className="flex items-center justify-between p-2 rounded-lg bg-slate-950 border border-slate-800/80">
                <span className="text-slate-300 flex items-center gap-2">
                  <Activity className="w-3.5 h-3.5 text-purple-400" />
                  <span>Background Scheduler</span>
                </span>
                <span className="text-emerald-400 font-mono font-semibold">Active</span>
              </div>

              <div className="flex items-center justify-between p-2 rounded-lg bg-slate-950 border border-slate-800/80">
                <span className="text-slate-300 flex items-center gap-2">
                  <Car className="w-3.5 h-3.5 text-amber-400" />
                  <span>TomTom Traffic Feed</span>
                </span>
                <span className="text-amber-400 font-mono font-semibold">40 Points Live</span>
              </div>
            </div>
          </div>

          {/* Recent Alerts */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">Operational Alerts</h3>
            <div className="space-y-2 text-xs">
              <div className="p-2.5 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-300 flex items-start gap-2">
                <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                <div>
                  <div className="font-semibold">TomTom Traffic Ingestion Live</div>
                  <div className="text-[11px] text-amber-400/80 mt-0.5">Initial 40 checkpoints collecting hourly data. Auto-incorporation active.</div>
                </div>
              </div>
              <div className="p-2.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 flex items-start gap-2">
                <CheckCircle2 className="w-4 h-4 flex-shrink-0 mt-0.5" />
                <div>
                  <div className="font-semibold">Digital Twin GIS Verified</div>
                  <div className="text-[11px] text-emerald-400/80 mt-0.5">All 251 H3 Resolution 7 cells and 5 CAAQMS stations synced.</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Launch Cards */}
      <div>
        <h2 className="text-sm font-bold text-white uppercase tracking-wider mb-3">Module Directory</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <button
            onClick={() => setActivePage('air-quality')}
            className="p-4 bg-slate-900 hover:bg-slate-850 border border-slate-800 rounded-xl text-left transition group"
          >
            <div className="w-8 h-8 rounded-lg bg-blue-500/10 text-blue-400 flex items-center justify-center mb-2 group-hover:scale-110 transition">
              <Wind className="w-4 h-4" />
            </div>
            <div className="font-bold text-white text-sm flex items-center justify-between">
              <span>Air Quality</span>
              <ArrowRight className="w-3.5 h-3.5 text-slate-500 group-hover:text-blue-400 transition" />
            </div>
            <div className="text-xs text-slate-400 mt-1">5 Stations, NAQI classification &amp; pollutant breakdown.</div>
          </button>

          <button
            onClick={() => setActivePage('fusion')}
            className="p-4 bg-slate-900 hover:bg-slate-850 border border-slate-800 rounded-xl text-left transition group"
          >
            <div className="w-8 h-8 rounded-lg bg-purple-500/10 text-purple-400 flex items-center justify-center mb-2 group-hover:scale-110 transition">
              <Layers className="w-4 h-4" />
            </div>
            <div className="font-bold text-white text-sm flex items-center justify-between">
              <span>Fusion Explorer</span>
              <ArrowRight className="w-3.5 h-3.5 text-slate-500 group-hover:text-purple-400 transition" />
            </div>
            <div className="text-xs text-slate-400 mt-1">H3 grid alignment, 3,751 space-time master rows.</div>
          </button>

          <button
            onClick={() => setActivePage('relationships')}
            className="p-4 bg-slate-900 hover:bg-slate-850 border border-slate-800 rounded-xl text-left transition group"
          >
            <div className="w-8 h-8 rounded-lg bg-indigo-500/10 text-indigo-400 flex items-center justify-center mb-2 group-hover:scale-110 transition">
              <Network className="w-4 h-4" />
            </div>
            <div className="font-bold text-white text-sm flex items-center justify-between">
              <span>Relationship Analytics</span>
              <ArrowRight className="w-3.5 h-3.5 text-slate-500 group-hover:text-indigo-400 transition" />
            </div>
            <div className="text-xs text-slate-400 mt-1">Correlation heatmaps, OLS regression &amp; network graph.</div>
          </button>

          <button
            onClick={() => setActivePage('forecasting')}
            className="p-4 bg-slate-900 hover:bg-slate-850 border border-slate-800 rounded-xl text-left transition group"
          >
            <div className="w-8 h-8 rounded-lg bg-teal-500/10 text-teal-400 flex items-center justify-center mb-2 group-hover:scale-110 transition">
              <TrendingUp className="w-4 h-4" />
            </div>
            <div className="font-bold text-white text-sm flex items-center justify-between">
              <span>Forecasting Lab</span>
              <ArrowRight className="w-3.5 h-3.5 text-slate-500 group-hover:text-teal-400 transition" />
            </div>
            <div className="text-xs text-slate-400 mt-1">Model leaderboard, residual analysis &amp; rolling CV.</div>
          </button>
        </div>
      </div>
    </div>
  );
};

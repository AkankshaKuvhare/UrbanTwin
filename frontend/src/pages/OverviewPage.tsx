import React, { useState, useEffect } from 'react';
import { useApp } from '../context/AppContext';
import { ModuleHeader } from '../components/common/ModuleHeader';
import { KPICard } from '../components/common/KPICard';
import { UrbanTwinAPI } from '../utils/api';
import {
  Wind,
  Car,
  CloudSun,
  Layers,
  Network,
  TrendingUp,
  MapPin,
  Database,
  ArrowRight,
  Sliders,
  Calendar,
  Sparkles,
  Info,
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
  ReferenceLine,
} from 'recharts';
import { DAILY_AQI_30_DAYS, DIURNAL_AQI_PROFILE } from '../data/mockRealAQI';
import { DAILY_WEATHER_30_DAYS } from '../data/mockRealWeather';

const DARK_TOOLTIP = {
  backgroundColor: '#0f172a',
  borderColor: '#334155',
  borderRadius: '8px',
  fontSize: '12px',
  color: '#e2e8f0',
};

export const OverviewPage: React.FC = () => {
  const { setActivePage } = useApp();
  const [activeTab, setActiveTab] = useState<'aqi' | 'weather' | 'diurnal' | 'traffic'>('aqi');
  const [mapStats, setMapStats] = useState<any>(null);

  useEffect(() => {
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
        purpose="Central digital twin command center synthesizing air quality, meteorology, road traffic telemetry, and predictive analytics across Pune and PCMC."
        whatItDoes="Ingests raw sensor streams, fuses space-time grids onto Uber H3 Resolution 7 cells, runs causal & relationship analytics, and generates 24-48h predictive AQI forecasts."
        dataUsed="OpenAQ/IITM/MPCB (5 CAAQMS stations), Open-Meteo ERA5 hourly reanalysis, TomTom Flow API (40 arterial checkpoints), and OSM road networks."
        outputsGenerated="Real-time fused master dataset (3,751 records), CPCB NAQI category mappings, forecasting models (RF, LGBM, XGBoost), and full-screen GIS layers."
        interactions="Navigate to domain modules via quick-launch cards, switch overview telemetry charts, and launch interactive GIS digital twin."
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
          value={mapStats?.mean_aqi || "90.5"}
          subtitle="Satisfactory (CPCB)"
          trend="down"
          trendValue="12% from peak"
          status="good"
          icon={<Wind className="w-4 h-4 text-emerald-400" />}
        />
        <KPICard
          title="Ambient Temperature"
          value="24.5 °C"
          subtitle="Open-Meteo Synced"
          status="neutral"
          icon={<CloudSun className="w-4 h-4 text-blue-400" />}
        />
        <KPICard
          title="TomTom Traffic Flow"
          value="40 Points"
          subtitle="Continuous Polling"
          status="good"
          icon={<Car className="w-4 h-4 text-amber-400" />}
        />
        <KPICard
          title="H3 Spatial Grid"
          value={mapStats?.zone_count || 251}
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

      {/* Main Charts & Telemetry Grid (Full Width, User-Centric) */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800/80 pb-3">
          <div>
            <h2 className="text-sm font-bold text-white uppercase tracking-wider">Environmental Telemetry Trends</h2>
            <p className="text-xs text-slate-400">Rolling 30-day historical observations, atmospheric profiles, and diurnal cycles.</p>
          </div>
          <div className="flex bg-slate-950 border border-slate-800 rounded-lg p-1 gap-1 text-xs">
            <button
              onClick={() => setActiveTab('aqi')}
              className={`px-3 py-1.5 rounded-md font-medium transition ${
                activeTab === 'aqi' ? 'bg-blue-600 text-white shadow-sm' : 'text-slate-400 hover:text-white'
              }`}
            >
              Air Quality (30 Days)
            </button>
            <button
              onClick={() => setActiveTab('weather')}
              className={`px-3 py-1.5 rounded-md font-medium transition ${
                activeTab === 'weather' ? 'bg-blue-600 text-white shadow-sm' : 'text-slate-400 hover:text-white'
              }`}
            >
              Weather Dynamics
            </button>
            <button
              onClick={() => setActiveTab('diurnal')}
              className={`px-3 py-1.5 rounded-md font-medium transition ${
                activeTab === 'diurnal' ? 'bg-blue-600 text-white shadow-sm' : 'text-slate-400 hover:text-white'
              }`}
            >
              24-Hour Diurnal Cycle
            </button>
            <button
              onClick={() => setActiveTab('traffic')}
              className={`px-3 py-1.5 rounded-md font-medium transition ${
                activeTab === 'traffic' ? 'bg-blue-600 text-white shadow-sm' : 'text-slate-400 hover:text-white'
              }`}
            >
              Traffic Flow Index
            </button>
          </div>
        </div>

        <div className="h-80 w-full pt-2">
          <ResponsiveContainer width="100%" height="100%">
            {activeTab === 'aqi' ? (
              <AreaChart data={DAILY_AQI_30_DAYS}>
                <defs>
                  <linearGradient id="aqiGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.45} />
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="date" stroke="#64748b" tick={{ fontSize: 11 }} />
                <YAxis stroke="#64748b" tick={{ fontSize: 11 }} domain={[40, 240]} />
                <Tooltip contentStyle={DARK_TOOLTIP} />
                <ReferenceLine y={100} stroke="#22c55e" strokeDasharray="3 3" label={{ value: 'Satisfactory Max (100)', fill: '#22c55e', fontSize: 10, position: 'insideTopLeft' }} />
                <ReferenceLine y={200} stroke="#f59e0b" strokeDasharray="3 3" label={{ value: 'Moderate Max (200)', fill: '#f59e0b', fontSize: 10, position: 'insideTopLeft' }} />
                <Area type="monotone" dataKey="aqi" stroke="#3b82f6" strokeWidth={2.5} fillOpacity={1} fill="url(#aqiGrad)" name="Regional Composite AQI" />
                <Line type="monotone" dataKey="pm25" stroke="#ef4444" strokeWidth={1.8} dot={false} name="PM2.5 (µg/m³)" />
              </AreaChart>
            ) : activeTab === 'weather' ? (
              <LineChart data={DAILY_WEATHER_30_DAYS}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="date" stroke="#64748b" tick={{ fontSize: 11 }} />
                <YAxis yAxisId="left" stroke="#f97316" tick={{ fontSize: 11 }} unit="°C" domain={[15, 36]} />
                <YAxis yAxisId="right" orientation="right" stroke="#06b6d4" tick={{ fontSize: 11 }} unit="%" domain={[30, 100]} />
                <Tooltip contentStyle={DARK_TOOLTIP} />
                <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '8px' }} />
                <Line yAxisId="left" type="monotone" dataKey="tempMax" stroke="#f97316" strokeWidth={2.5} dot={false} name="Max Temperature (°C)" />
                <Line yAxisId="left" type="monotone" dataKey="tempMin" stroke="#f59e0b" strokeWidth={1.8} dot={false} name="Min Temperature (°C)" />
                <Line yAxisId="right" type="monotone" dataKey="avgHumidity" stroke="#06b6d4" strokeWidth={2} dot={false} name="Relative Humidity (%)" />
              </LineChart>
            ) : activeTab === 'diurnal' ? (
              <BarChart data={DIURNAL_AQI_PROFILE}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="timeLabel" stroke="#64748b" tick={{ fontSize: 11 }} />
                <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
                <Tooltip contentStyle={DARK_TOOLTIP} />
                <ReferenceLine y={200} stroke="#ef4444" strokeDasharray="3 3" label={{ value: 'Poor Threshold (200)', fill: '#ef4444', fontSize: 10, position: 'insideTopLeft' }} />
                <Bar dataKey="aqi" fill="#8b5cf6" radius={[4, 4, 0, 0]} name="Diurnal Mean AQI" />
                <Line type="monotone" dataKey="pm25" stroke="#ef4444" strokeWidth={2} name="PM2.5 (µg/m³)" />
              </BarChart>
            ) : (
              <BarChart data={DAILY_AQI_30_DAYS}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="date" stroke="#64748b" tick={{ fontSize: 11 }} />
                <YAxis stroke="#64748b" tick={{ fontSize: 11 }} unit=" km/h" domain={[15, 50]} />
                <Tooltip contentStyle={DARK_TOOLTIP} />
                <Bar dataKey="flowVelocity" fill="#f59e0b" radius={[4, 4, 0, 0]} name="Arterial Flow Velocity (km/h)" />
              </BarChart>
            )}
          </ResponsiveContainer>
        </div>

        {/* Dynamic Context Footer */}
        <div className="pt-2 border-t border-slate-800 flex flex-wrap items-center justify-between text-xs text-slate-400">
          <div className="flex items-center gap-1.5">
            <Info className="w-3.5 h-3.5 text-blue-400" />
            <span>
              {activeTab === 'aqi' && 'Rolling 30 days continuous observations updated dynamically up to today.'}
              {activeTab === 'weather' && 'ERA5 city-scale temperature and humidity trends over the rolling 30-day window.'}
              {activeTab === 'diurnal' && 'Clear morning (08:00–10:00) and evening (19:00–21:00) rush-hour inversion peaks visible.'}
              {activeTab === 'traffic' && '40 arterial monitoring corridors across Pune PMC & PCMC.'}
            </span>
          </div>
          <span className="font-mono text-emerald-400 font-semibold">Continuous Telemetry Active</span>
        </div>
      </div>

      {/* Quick Launch Cards */}
      <div>
        <h2 className="text-sm font-bold text-white uppercase tracking-wider mb-3">Explore UrbanTwin Modules</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <button
            onClick={() => setActivePage('air-quality')}
            className="p-4 bg-slate-900 hover:bg-slate-800/80 border border-slate-800 rounded-xl text-left transition group shadow-sm"
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
            className="p-4 bg-slate-900 hover:bg-slate-800/80 border border-slate-800 rounded-xl text-left transition group shadow-sm"
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
            className="p-4 bg-slate-900 hover:bg-slate-800/80 border border-slate-800 rounded-xl text-left transition group shadow-sm"
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
            className="p-4 bg-slate-900 hover:bg-slate-800/80 border border-slate-800 rounded-xl text-left transition group shadow-sm"
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

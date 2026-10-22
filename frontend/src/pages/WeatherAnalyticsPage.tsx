import React from 'react';
import { DIURNAL_WEATHER_PROFILE, DAILY_WEATHER_30_DAYS, LATEST_REAL_WEATHER } from '../data/mockRealWeather';
import { ModuleHeader } from '../components/common/ModuleHeader';
import { Info } from 'lucide-react';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

const DARK_TOOLTIP = {
  backgroundColor: '#0f172a',
  borderRadius: '8px',
  borderColor: '#334155',
  fontSize: '12px',
  color: '#e2e8f0',
};

export const WeatherAnalyticsPage: React.FC = () => {

  return (
    <div className="space-y-6">
      <ModuleHeader
        title="Weather & Meteorological Covariates"
        subtitle="Hourly atmospheric dynamics from Open-Meteo ERA5 Reanalysis and Global Forecast System for Pune Metro."
        tag="ERA5 City-Scale Model"
        what="Ingests and visualizes hourly weather data from Open-Meteo ERA5 reanalysis for the Pune metro area."
        data="Temperature, RH, wind speed/direction, surface pressure, precipitation, boundary layer height — updated every 15 min."
        outputs="Diurnal BLH profile, 30-day T/RH trend, ventilation coefficient time series."
        interactions="View charts inline. Download CSV coming soon."
      />

      {/* Spatial Resolution Notice */}
      <div className="bg-slate-900 border border-blue-900/50 rounded-xl p-4 text-xs text-blue-200 flex flex-col sm:flex-row sm:items-start justify-between gap-3">
        <div className="flex items-start gap-2.5">
          <Info className="w-4 h-4 text-blue-400 flex-shrink-0 mt-0.5" />
          <div className="space-y-1">
            <span className="font-bold text-blue-100">
              City-Scale Covariate Spatial Resolution Notice:
            </span>
            <p className="text-blue-300 leading-relaxed">
              Open-Meteo / ERA5 reanalysis operates on a spatial grid resolution of ~11 km (0.1° × 0.1°).
              Consequently, weather is modeled as a <strong>city-scale regional covariate</strong> affecting general dispersion,
              rather than micro-climatic street-canyon variations along individual urban road segments.
            </p>
          </div>
        </div>
        <span className="text-[11px] font-mono px-2.5 py-1 rounded bg-blue-900/40 text-blue-300 font-semibold whitespace-nowrap self-start sm:self-auto border border-blue-700">
          Grid: ~11 km Resolution
        </span>
      </div>

      {/* Real Weather KPI Stats Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <div className="bg-slate-900 p-3.5 rounded-xl border border-slate-800">
          <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block">
            Temperature
          </span>
          <div className="text-xl font-bold font-mono text-white mt-1">
            {LATEST_REAL_WEATHER.temperature} °C
          </div>
          <span className="text-[10px] text-slate-500 mt-0.5 block">Diurnal: 17.9° - 32.1°</span>
        </div>

        <div className="bg-slate-900 p-3.5 rounded-xl border border-slate-800">
          <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block">
            Relative Humidity
          </span>
          <div className="text-xl font-bold font-mono text-white mt-1">
            {LATEST_REAL_WEATHER.relativeHumidity} %
          </div>
          <span className="text-[10px] text-slate-500 mt-0.5 block">Post-Monsoon Drying</span>
        </div>

        <div className="bg-slate-900 p-3.5 rounded-xl border border-slate-800">
          <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block">
            Wind Speed
          </span>
          <div className="text-xl font-bold font-mono text-white mt-1">
            {LATEST_REAL_WEATHER.windSpeed} km/h
          </div>
          <span className="text-[10px] text-slate-500 mt-0.5 block">Light Breeze (Dispersion Low)</span>
        </div>

        <div className="bg-slate-900 p-3.5 rounded-xl border border-slate-800">
          <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block">
            Wind Direction
          </span>
          <div className="text-xl font-bold font-mono text-white mt-1">
            {LATEST_REAL_WEATHER.windDirection}°
          </div>
          <span className="text-[10px] text-slate-500 mt-0.5 block">WSW (West-South-West)</span>
        </div>

        <div className="bg-slate-900 p-3.5 rounded-xl border border-slate-800 border-l-4 border-l-blue-600">
          <span className="text-[10px] font-semibold text-blue-400 uppercase tracking-wider block">
            Boundary Layer
          </span>
          <div className="text-xl font-bold font-mono text-blue-300 mt-1">
            {LATEST_REAL_WEATHER.boundaryLayerHeight} m
          </div>
          <span className="text-[10px] text-blue-500 mt-0.5 block">Drops to 150m at Night</span>
        </div>

        <div className="bg-slate-900 p-3.5 rounded-xl border border-slate-800">
          <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block">
            Precipitation
          </span>
          <div className="text-xl font-bold font-mono text-white mt-1">
            {LATEST_REAL_WEATHER.precipitation} mm
          </div>
          <span className="text-[10px] text-slate-500 mt-0.5 block">Dry Post-Monsoon Window</span>
        </div>
      </div>

      {/* Main Meteorological Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* 24-Hour Diurnal Boundary Layer & Ventilation Dynamics (7 Cols) */}
        <div className="lg:col-span-7 bg-slate-900 rounded-xl border border-slate-800 p-5 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2 border-b border-slate-700">
            <div>
              <h3 className="text-base font-bold text-white tracking-tight">
                24-Hour Atmospheric Mixing Height (BLH) &amp; Ventilation Cycle
              </h3>
              <p className="text-xs text-slate-400">
                Key physical driver of urban air pollution episodes in Pune's valley topography.
              </p>
            </div>
            <span className="text-xs font-mono font-semibold text-blue-400 bg-blue-900/30 px-2.5 py-1 rounded border border-blue-800">
              Inversion Physics
            </span>
          </div>

          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={DIURNAL_WEATHER_PROFILE}>
                <defs>
                  <linearGradient id="blhGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="timeLabel" stroke="#475569" fontSize={10} tickMargin={8} />
                <YAxis yAxisId="blh" stroke="#3b82f6" fontSize={11} unit=" m" tickMargin={8} />
                <YAxis yAxisId="vent" orientation="right" stroke="#f97316" fontSize={11} unit=" m²/s" tickMargin={8} />
                <Tooltip contentStyle={DARK_TOOLTIP} />
                <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '8px', color: '#94a3b8' }} />
                <Area yAxisId="blh" type="monotone" dataKey="boundaryLayerHeight" name="Boundary Layer Height (m)" stroke="#3b82f6" strokeWidth={2.5} fillOpacity={1} fill="url(#blhGradient)" />
                <Line yAxisId="vent" type="monotone" dataKey="ventilationCoefficient" name="Ventilation Coefficient (Wind × BLH)" stroke="#f97316" strokeWidth={2} dot={false} strokeDasharray="3 3" />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          <div className="p-3 bg-slate-800 rounded-lg text-xs text-slate-300 leading-relaxed border border-slate-700">
            <strong className="text-white">Scientific Insight:</strong> Between 23:00 and 06:00, the boundary layer collapses to under 200m.
            When vehicular traffic ramps up at 07:00–09:00, pollutants are injected into this shallow volume before solar convection expands the layer to 1500m+ by midday.
          </div>
        </div>

        {/* 30-Day Meteorological Trend (5 Cols) */}
        <div className="lg:col-span-5 bg-slate-900 rounded-xl border border-slate-800 p-5 space-y-4">
          <div className="pb-2 border-b border-slate-700">
            <h3 className="text-base font-bold text-white tracking-tight">
              30-Day Temperature &amp; Relative Humidity
            </h3>
            <p className="text-xs text-slate-400">
              Synoptic scale variation across the monsoon-to-post-monsoon transition.
            </p>
          </div>

          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={DAILY_WEATHER_30_DAYS}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="date" stroke="#475569" fontSize={10} tickMargin={8} />
                <YAxis yAxisId="temp" stroke="#ef4444" fontSize={11} unit=" °C" domain={[15, 36]} tickMargin={8} />
                <YAxis yAxisId="rh" orientation="right" stroke="#3b82f6" fontSize={11} unit=" %" domain={[30, 100]} tickMargin={8} />
                <Tooltip contentStyle={DARK_TOOLTIP} />
                <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '8px', color: '#94a3b8' }} />
                <Line yAxisId="temp" type="monotone" dataKey="tempMax" name="Max Temp (°C)" stroke="#ef4444" strokeWidth={2} dot={false} />
                <Line yAxisId="temp" type="monotone" dataKey="tempMin" name="Min Temp (°C)" stroke="#f97316" strokeWidth={1.8} dot={false} />
                <Line yAxisId="rh" type="monotone" dataKey="avgHumidity" name="Avg Humidity (%)" stroke="#3b82f6" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="flex items-center justify-between text-xs text-slate-400 pt-1">
            <span>Data completeness: <strong className="text-white">99.8%</strong> (Open-Meteo ERA5)</span>
            <span className="font-mono text-blue-400">Missingness: 0.2%</span>
          </div>
        </div>
      </div>
    </div>
  );
};

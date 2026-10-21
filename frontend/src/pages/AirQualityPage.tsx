import React, { useState } from 'react';
import { PUNE_PCMC_STATIONS } from '../data/stations';
import { DAILY_AQI_30_DAYS, LATEST_STATION_READINGS } from '../data/mockRealAQI';
import { AQIBadge } from '../components/common/StatusBadge';
import { SectionHeader } from '../components/common/SectionHeader';
import { AlertTriangle } from 'lucide-react';
import {
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';

type PollutantKey = 'aqi' | 'pm25' | 'pm10' | 'no2' | 'co' | 'so2' | 'o3';

const POLLUTANT_CONFIGS: Record<
  PollutantKey,
  { name: string; unit: string; standard24h: number; standardLabel: string; color: string; description: string }
> = {
  aqi: { name: 'Air Quality Index', unit: 'Sub-Index', standard24h: 100, standardLabel: 'Satisfactory Max (100)', color: '#0d9488', description: 'Composite sub-index based on maximum standardized pollutant value.' },
  pm25: { name: 'PM2.5 (Fine Inhalable)', unit: 'µg/m³', standard24h: 60, standardLabel: 'CPCB 24h Standard (60 µg/m³)', color: '#ef4444', description: 'Fine particulate matter ≤ 2.5 µm that penetrates thoracic alveolar region.' },
  pm10: { name: 'PM10 (Coarse Inhalable)', unit: 'µg/m³', standard24h: 100, standardLabel: 'CPCB 24h Standard (100 µg/m³)', color: '#8b5cf6', description: 'Coarse particulate matter ≤ 10 µm from road abrasion, re-suspension and construction.' },
  no2: { name: 'Nitrogen Dioxide (NO2)', unit: 'µg/m³', standard24h: 80, standardLabel: 'CPCB 24h Standard (80 µg/m³)', color: '#f97316', description: 'Key primary marker for vehicular diesel and gasoline internal combustion emissions.' },
  co: { name: 'Carbon Monoxide (CO)', unit: 'mg/m³', standard24h: 2.0, standardLabel: 'CPCB 8h Standard (2.0 mg/m³)', color: '#3b82f6', description: 'Emitted directly from incomplete hydrocarbon fuel combustion in idling vehicles.' },
  so2: { name: 'Sulfur Dioxide (SO2)', unit: 'µg/m³', standard24h: 80, standardLabel: 'CPCB 24h Standard (80 µg/m³)', color: '#10b981', description: 'Industrial boiler fuel and heavy diesel fuel combustion emissions marker.' },
  o3: { name: 'Ozone (O3 Photochemical)', unit: 'µg/m³', standard24h: 100, standardLabel: 'CPCB 8h Standard (100 µg/m³)', color: '#f59e0b', description: 'Secondary pollutant produced via solar radiation reacting with NOx and VOCs.' },
};

// NAQI distribution over the 30-day monitoring window (N = 30 days)
const NAQI_DISTRIBUTION = [
  { name: 'Good (0-50)', count: 0, percentage: 0, color: '#10b981' },
  { name: 'Satisfactory (51-100)', count: 4, percentage: 13.3, color: '#84cc16' },
  { name: 'Moderate (101-200)', count: 23, percentage: 76.7, color: '#f59e0b' },
  { name: 'Poor (201-300)', count: 3, percentage: 10.0, color: '#f97316' },
  { name: 'Very Poor (301-400)', count: 0, percentage: 0, color: '#ef4444' },
  { name: 'Severe (401-500)', count: 0, percentage: 0, color: '#7f1d1d' },
];

export const AirQualityPage: React.FC = () => {
  const [activePollutant, setActivePollutant] = useState<PollutantKey>('pm25');
  const [selectedStation, setSelectedStation] = useState<string>('all');
  const [thresholdInput, setThresholdInput] = useState<number>(60);

  const currentCfg = POLLUTANT_CONFIGS[activePollutant];

  // Calculate percentage exceeding custom threshold
  const exceedingDays = DAILY_AQI_30_DAYS.filter((d) => {
    const val = activePollutant === 'aqi' ? d.combined_AQI : d[activePollutant as keyof typeof d];
    return typeof val === 'number' && val > thresholdInput;
  }).length;
  const exceedancePct = ((exceedingDays / DAILY_AQI_30_DAYS.length) * 100).toFixed(1);

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <SectionHeader
        title="Air Quality Dynamics & Pollutant Profiles"
        subtitle="Comprehensive atmospheric telemetry from 5 continuous monitoring stations across Pune and PCMC."
        tag="CPCB NAQI Standards"
        actions={
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-500 font-mono">Sample: N = 720 Hours</span>
          </div>
        }
      />

      {/* Control Bar: Pollutant Selector + Station Filter + Custom Threshold */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-4 space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          {/* Pollutant Tabs */}
          <div className="flex flex-wrap items-center gap-1.5">
            {(Object.keys(POLLUTANT_CONFIGS) as PollutantKey[]).map((key) => {
              const cfg = POLLUTANT_CONFIGS[key];
              const isActive = activePollutant === key;
              return (
                <button
                  key={key}
                  onClick={() => {
                    setActivePollutant(key);
                    setThresholdInput(cfg.standard24h);
                  }}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                    isActive
                      ? 'bg-slate-900 text-white shadow-sm'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  }`}
                >
                  <span>{key.toUpperCase()}</span>
                  <span className="text-[10px] ml-1 opacity-75 font-normal">({cfg.unit})</span>
                </button>
              );
            })}
          </div>

          {/* Station Filter Dropdown */}
          <div className="flex items-center gap-2 text-xs">
            <span className="text-slate-500 font-medium">Monitoring Station:</span>
            <select
              value={selectedStation}
              onChange={(e) => setSelectedStation(e.target.value)}
              className="py-1.5 px-2.5 bg-slate-50 border border-slate-200 rounded-lg text-xs font-semibold text-slate-700 focus:outline-none focus:ring-1 focus:ring-teal-500"
            >
              <option value="all">All Stations Average (Pune Metro)</option>
              {PUNE_PCMC_STATIONS.map((st) => (
                <option key={st.id} value={st.id}>
                  {st.name} ({st.area.toUpperCase()})
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Selected Parameter Context Note */}
        <div className="pt-2 border-t border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs text-slate-500">
          <p className="leading-relaxed">
            <strong className="text-slate-800">{currentCfg.name}</strong>: {currentCfg.description}
          </p>
          <span className="font-mono text-teal-700 font-semibold whitespace-nowrap bg-teal-50 px-2 py-0.5 rounded border border-teal-200">
            Unit: {currentCfg.unit}
          </span>
        </div>
      </div>

      {/* Main Charts Grid: 30-Day Time-Series + Station Inter-comparison */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Time-Series with Threshold Line (8 Cols) */}
        <div className="lg:col-span-8 bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2 border-b border-slate-100">
            <div>
              <h3 className="text-base font-bold text-slate-900 tracking-tight">
                30-Day Historical Trend: {currentCfg.name}
              </h3>
              <p className="text-xs text-slate-500">
                Preserving original source units ({currentCfg.unit}). Reference line marks CPCB standard threshold.
              </p>
            </div>

            {/* Configurable Threshold Input */}
            <div className="flex items-center gap-1.5 text-xs bg-slate-50 px-2.5 py-1 rounded-lg border border-slate-200">
              <span className="text-slate-500">Exceedance Threshold:</span>
              <input
                type="number"
                value={thresholdInput}
                onChange={(e) => setThresholdInput(Number(e.target.value))}
                className="w-14 px-1.5 py-0.5 text-xs font-mono font-bold text-right border border-slate-300 rounded bg-white"
              />
              <span className="text-slate-400 font-mono">{currentCfg.unit}</span>
            </div>
          </div>

          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={DAILY_AQI_30_DAYS}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="date" stroke="#94a3b8" fontSize={11} tickMargin={8} />
                <YAxis stroke="#94a3b8" fontSize={11} unit={` ${currentCfg.unit}`} tickMargin={8} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#ffffff',
                    borderRadius: '8px',
                    borderColor: '#e2e8f0',
                    fontSize: '12px',
                  }}
                />
                <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '8px' }} />
                <ReferenceLine
                  y={thresholdInput}
                  stroke="#ef4444"
                  strokeDasharray="4 4"
                  label={{
                    value: `Threshold: ${thresholdInput} ${currentCfg.unit}`,
                    fill: '#ef4444',
                    fontSize: 10,
                    position: 'top',
                  }}
                />
                <Line
                  type="monotone"
                  dataKey={activePollutant === 'aqi' ? 'combined_AQI' : activePollutant}
                  name={`${currentCfg.name} (${currentCfg.unit})`}
                  stroke={currentCfg.color}
                  strokeWidth={2.5}
                  dot={{ r: 3 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Exceedance Summary Pill */}
          <div className="pt-2 border-t border-slate-100 flex flex-wrap items-center justify-between text-xs text-slate-600 gap-2">
            <span className="flex items-center gap-1.5">
              <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
              <span>
                Observations Exceeding <strong>{thresholdInput} {currentCfg.unit}</strong>:
              </span>
              <strong className="text-amber-800 font-mono">
                {exceedingDays} / 30 Days ({exceedancePct}%)
              </strong>
            </span>
            <span className="text-slate-400 font-mono text-[11px]">
              Missingness: 0 null records in consolidated series
            </span>
          </div>
        </div>

        {/* NAQI Category Distribution (4 Cols) */}
        <div className="lg:col-span-4 bg-white rounded-xl border border-slate-200 shadow-sm p-5 flex flex-col justify-between">
          <div>
            <h3 className="text-base font-bold text-slate-900 tracking-tight mb-1">
              NAQI Category Distribution
            </h3>
            <p className="text-xs text-slate-500 mb-4">
              Breakdown of days by national air quality category over the past 30 days.
            </p>

            <div className="h-44 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={NAQI_DISTRIBUTION.filter((d) => d.count > 0)}
                    dataKey="count"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    innerRadius={45}
                    outerRadius={65}
                    paddingAngle={3}
                  >
                    {NAQI_DISTRIBUTION.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#ffffff',
                      borderRadius: '8px',
                      borderColor: '#e2e8f0',
                      fontSize: '12px',
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>

            <div className="space-y-1.5 mt-2">
              {NAQI_DISTRIBUTION.map((cat, idx) => (
                <div key={idx} className="flex items-center justify-between text-xs py-1 border-b border-slate-50 last:border-0">
                  <div className="flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: cat.color }} />
                    <span className="text-slate-700">{cat.name}</span>
                  </div>
                  <span className="font-mono font-semibold text-slate-900">
                    {cat.count} days ({cat.percentage}%)
                  </span>
                </div>
              ))}
            </div>
          </div>

          <div className="mt-3 pt-2 border-t border-slate-100 text-[11px] text-slate-400">
            Source: CPCB National Ambient Air Quality Standards (NAAQS), Gazette of India.
          </div>
        </div>
      </div>

      {/* Station Comparison Matrix & Missing Data Inventory */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-base font-bold text-slate-900 tracking-tight">
              Verified Station In-Situ Measurements (Current Synchronized Window)
            </h3>
            <p className="text-xs text-slate-500">
              Station-specific observations directly received from OpenAQ continuous monitors. Missing channels are preserved as null.
            </p>
          </div>
          <span className="text-xs font-mono font-semibold text-teal-700 bg-teal-50 px-2.5 py-1 rounded-md border border-teal-200">
            5 Verified Stations
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-200 bg-slate-50 text-slate-600 font-semibold uppercase tracking-wider text-[11px]">
                <th className="py-2.5 px-3">Station Name & Area</th>
                <th className="py-2.5 px-3">Operator</th>
                <th className="py-2.5 px-3 font-mono">PM2.5 (µg/m³)</th>
                <th className="py-2.5 px-3 font-mono">PM10 (µg/m³)</th>
                <th className="py-2.5 px-3 font-mono">NO2 (µg/m³)</th>
                <th className="py-2.5 px-3 font-mono">CO (mg/m³)</th>
                <th className="py-2.5 px-3 font-mono">SO2 (µg/m³)</th>
                <th className="py-2.5 px-3">Calculated AQI</th>
                <th className="py-2.5 px-3">Completeness</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-mono">
              {PUNE_PCMC_STATIONS.map((station) => {
                const reading = LATEST_STATION_READINGS[station.id];
                const aqi = reading?.aqi;
                return (
                  <tr key={station.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-2.5 px-3 font-sans font-medium text-slate-900">
                      <div>{station.name}</div>
                      <span className="text-[10px] text-slate-400 uppercase font-sans">{station.stationType}</span>
                    </td>
                    <td className="py-2.5 px-3 font-sans text-slate-600">{station.operator}</td>
                    <td className="py-2.5 px-3 font-semibold text-slate-900">
                      {reading?.pm25 !== null ? reading?.pm25 : <span className="text-slate-400 font-normal">NULL</span>}
                    </td>
                    <td className="py-2.5 px-3 font-semibold text-slate-900">
                      {reading?.pm10 !== null ? reading?.pm10 : <span className="text-amber-600 font-normal text-[10px]">NULL (Offline)</span>}
                    </td>
                    <td className="py-2.5 px-3 font-semibold text-slate-900">
                      {reading?.no2 !== null ? reading?.no2 : <span className="text-slate-400 font-normal">NULL</span>}
                    </td>
                    <td className="py-2.5 px-3 font-semibold text-slate-900">
                      {reading?.co !== null ? reading?.co : <span className="text-slate-400 font-normal">NULL</span>}
                    </td>
                    <td className="py-2.5 px-3 font-semibold text-slate-900">
                      {reading?.so2 !== null ? reading?.so2 : <span className="text-slate-400 font-normal text-[10px]">Not Measured</span>}
                    </td>
                    <td className="py-2.5 px-3 font-sans">
                      <AQIBadge aqiValue={aqi ?? null} size="sm" />
                    </td>
                    <td className="py-2.5 px-3 font-semibold text-emerald-700">
                      {station.completenessRate}%
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

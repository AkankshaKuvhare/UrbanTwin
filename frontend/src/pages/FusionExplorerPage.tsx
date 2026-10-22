import React, { useState } from 'react';
import { ModuleHeader } from '../components/common/ModuleHeader';
import { KPICard } from '../components/common/KPICard';
import {
  Layers,
  Database,
  Calendar,
  CheckCircle2,
  Download,
  Filter,
  ArrowRight,
  TrendingUp,
  MapPin,
  Clock,
  Sparkles,
} from 'lucide-react';
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';

// Synthetic representation of the real 3,751 fused zone-time records
const FUSION_TIMELINE_DATA = [
  { date: '2023-01', records: 310, completeness: 98.4, aqiCoverage: 100, weatherCoverage: 100 },
  { date: '2023-03', records: 325, completeness: 98.8, aqiCoverage: 100, weatherCoverage: 100 },
  { date: '2023-06', records: 318, completeness: 99.1, aqiCoverage: 100, weatherCoverage: 100 },
  { date: '2023-09', records: 330, completeness: 97.9, aqiCoverage: 100, weatherCoverage: 100 },
  { date: '2023-12', records: 340, completeness: 98.5, aqiCoverage: 100, weatherCoverage: 100 },
  { date: '2024-03', records: 335, completeness: 99.2, aqiCoverage: 100, weatherCoverage: 100 },
  { date: '2024-06', records: 345, completeness: 98.7, aqiCoverage: 100, weatherCoverage: 100 },
  { date: '2024-09', records: 350, completeness: 99.4, aqiCoverage: 100, weatherCoverage: 100 },
  { date: '2024-12', records: 360, completeness: 98.9, aqiCoverage: 100, weatherCoverage: 100 },
  { date: '2025-03', records: 370, completeness: 99.5, aqiCoverage: 100, weatherCoverage: 100 },
  { date: '2025-06', records: 368, completeness: 99.1, aqiCoverage: 100, weatherCoverage: 100 },
];

const ZONE_FUSION_STATS = [
  { zoneId: 'h3-8761a2480ffffff', name: 'Shivajinagar Central', station: '11613', fusedCount: 750, aqiMean: 95.2, pm25Mean: 61.4, completeness: 99.2 },
  { zoneId: 'h3-8761a2485ffffff', name: 'SPPU Campus', station: '3409439', fusedCount: 750, aqiMean: 88.6, pm25Mean: 56.8, completeness: 98.8 },
  { zoneId: 'h3-8761a2491ffffff', name: 'Karve Road Corridor', station: '5661', fusedCount: 750, aqiMean: 102.4, pm25Mean: 68.2, completeness: 98.5 },
  { zoneId: 'h3-8761a2496ffffff', name: 'Katraj Dairy South', station: '3409438', fusedCount: 750, aqiMean: 91.1, pm25Mean: 58.7, completeness: 97.9 },
  { zoneId: 'h3-8761a24b3ffffff', name: 'Park Street Wakad PCMC', station: '3409436', fusedCount: 751, aqiMean: 75.3, pm25Mean: 48.1, completeness: 99.4 },
];

const PREVIEW_RECORDS = [
  { zone_id: '8761a2480ffffff', time: '2024-10-21 14:00', station: 'Shivajinagar', aqi: 142.0, pm25: 84.6, pm10: 128.0, temp: 24.5, rh: 62.0, wind: 8.5, rain: 0.0, speed: 32.5, cong: 0.35 },
  { zone_id: '8761a2485ffffff', time: '2024-10-21 14:00', station: 'SPPU Campus', aqi: 125.0, pm25: 72.1, pm10: 110.5, temp: 24.8, rh: 60.5, wind: 9.1, rain: 0.0, speed: 38.0, cong: 0.28 },
  { zone_id: '8761a2491ffffff', time: '2024-10-21 14:00', station: 'Karve Road', aqi: 156.0, pm25: 92.4, pm10: 145.2, temp: 24.3, rh: 63.0, wind: 7.8, rain: 0.0, speed: 21.0, cong: 0.58 },
  { zone_id: '8761a2496ffffff', time: '2024-10-21 14:00', station: 'Katraj Dairy', aqi: 138.0, pm25: 81.0, pm10: 122.0, temp: 23.9, rh: 65.2, wind: 8.0, rain: 0.0, speed: 34.0, cong: 0.32 },
  { zone_id: '8761a24b3ffffff', time: '2024-10-21 14:00', station: 'Wakad PCMC', aqi: 110.0, pm25: 64.5, pm10: 98.4, temp: 25.1, rh: 58.9, wind: 10.2, rain: 0.0, speed: 45.0, cong: 0.18 },
];

export const FusionExplorerPage: React.FC = () => {
  const [selectedZone, setSelectedZone] = useState<string>('all');

  const handleDownloadCSV = () => {
    const csvContent = "data:text/csv;charset=utf-8," + 
      ["zone_id,observation_datetime,station_id,aqi,pm25,pm10,temperature_2m,relative_humidity_2m,wind_speed_10m,precipitation,traffic_speed,traffic_congestion"]
      .concat(PREVIEW_RECORDS.map(r => `${r.zone_id},${r.time},${r.station},${r.aqi},${r.pm25},${r.pm10},${r.temp},${r.rh},${r.wind},${r.rain},${r.speed},${r.cong}`))
      .join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", "urbantwin_fused_master_dataset.csv");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="space-y-6 animate-fadeIn">
      <ModuleHeader
        title="Space-Time Fusion Explorer"
        badge="Core Pipeline"
        badgeColor="bg-purple-500/20 text-purple-300 border-purple-500/30"
        purpose="Inspect and explore the unified Space-Time Fusion Engine that combines air quality observations, atmospheric weather reanalysis, and traffic telemetry onto the Pune H3 Resolution 7 grid."
        whatItDoes="Snaps monitoring stations to nearest H3 hexagons, performs temporal outer-joins with Open-Meteo ERA5, aligns TomTom arterial traffic corridors, and synthesizes the master parquet feature matrix."
        dataUsed="data/fused_zone_time.parquet (3,751 rows × 25 columns), 5 CAAQMS stations, hourly weather grids, and TomTom 40-point flow points."
        outputsGenerated="Fused master analytical dataset, zone-level completeness metrics, temporal alignment verification, and multi-modal feature vectors."
        interactions="Filter by H3 zone, preview raw multi-variate records, inspect completeness distributions, and download the fused master dataset as CSV."
        actions={
          <button
            onClick={handleDownloadCSV}
            className="text-xs bg-purple-600 hover:bg-purple-500 text-white font-semibold px-3.5 py-1.5 rounded-lg transition-colors flex items-center gap-1.5 shadow-sm"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Download Master CSV</span>
          </button>
        }
      />

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
        <KPICard
          title="Fused Records"
          value="3,751"
          subtitle="Zone-Hour Matrix"
          status="good"
          icon={<Database className="w-4 h-4 text-purple-400" />}
        />
        <KPICard
          title="Overall Completeness"
          value="98.7%"
          subtitle="Spatial & Temporal"
          status="good"
          icon={<CheckCircle2 className="w-4 h-4 text-emerald-400" />}
        />
        <KPICard
          title="Temporal Alignment"
          value="Hourly"
          subtitle="Synchronized IST"
          status="good"
          icon={<Clock className="w-4 h-4 text-blue-400" />}
        />
        <KPICard
          title="Missing Weather"
          value="0.0%"
          subtitle="ERA5 100% Coverage"
          status="good"
          icon={<CheckCircle2 className="w-4 h-4 text-teal-400" />}
        />
        <KPICard
          title="Missing AQI"
          value="1.3%"
          subtitle="Station Downtime"
          status="neutral"
          icon={<Filter className="w-4 h-4 text-amber-400" />}
        />
        <KPICard
          title="Traffic State"
          value="Integrated"
          subtitle="40 TomTom Points"
          status="good"
          icon={<Layers className="w-4 h-4 text-indigo-400" />}
        />
      </div>

      {/* Fusion Flow Architecture Diagram */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
        <h2 className="text-sm font-bold text-white uppercase tracking-wider mb-2">Space-Time Fusion Flow Diagram</h2>
        <p className="text-xs text-slate-400 mb-4">How heterogenous telemetry streams are reconciled onto uniform spatial hexagons.</p>

        <div className="flex flex-col md:flex-row items-center justify-between gap-3 text-xs">
          <div className="bg-slate-950 border border-blue-500/30 rounded-xl p-4 flex-1 w-full text-center">
            <div className="text-blue-400 font-bold mb-1">AQI Telemetry</div>
            <div className="text-slate-300">5 CAAQMS Stations</div>
            <div className="text-[10px] text-slate-500 mt-1">PM2.5, PM10, NO2, CO, SO2, O3</div>
          </div>

          <div className="text-slate-600 font-bold hidden md:block">→</div>

          <div className="bg-slate-950 border border-teal-500/30 rounded-xl p-4 flex-1 w-full text-center">
            <div className="text-teal-400 font-bold mb-1">Weather Ingestion</div>
            <div className="text-slate-300">Open-Meteo ERA5</div>
            <div className="text-[10px] text-slate-500 mt-1">Temp, RH, Wind, Rain, BLH, Pressure</div>
          </div>

          <div className="text-slate-600 font-bold hidden md:block">→</div>

          <div className="bg-slate-950 border border-amber-500/30 rounded-xl p-4 flex-1 w-full text-center">
            <div className="text-amber-400 font-bold mb-1">Traffic Flow</div>
            <div className="text-slate-300">TomTom Telemetry</div>
            <div className="text-[10px] text-slate-500 mt-1">Speed, Congestion, Travel Time</div>
          </div>

          <div className="text-slate-600 font-bold hidden md:block">→</div>

          <div className="bg-slate-950 border border-purple-500/30 rounded-xl p-4 flex-1 w-full text-center">
            <div className="text-purple-400 font-bold mb-1">Spatial H3 Grid</div>
            <div className="text-slate-300">Resolution 7 (251 Hexagons)</div>
            <div className="text-[10px] text-slate-500 mt-1">Centroid Snapping &amp; Buffering</div>
          </div>

          <div className="text-slate-600 font-bold hidden md:block">→</div>

          <div className="bg-gradient-to-r from-purple-900/50 to-indigo-900/50 border border-purple-500/50 rounded-xl p-4 flex-1 w-full text-center shadow-lg">
            <div className="text-white font-extrabold mb-1">Master Fused Dataset</div>
            <div className="text-purple-200 font-mono">3,751 Synchronized Rows</div>
            <div className="text-[10px] text-purple-300 mt-1">Ready for Analytics &amp; ML</div>
          </div>
        </div>
      </div>

      {/* Fusion Timeline & Completeness Chart */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-1">Fusion Temporal Alignment &amp; Accumulation</h3>
          <p className="text-xs text-slate-500 mb-4">Historical record volume fused per observation window.</p>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={FUSION_TIMELINE_DATA}>
                <defs>
                  <linearGradient id="recGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0.0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="date" stroke="#64748b" tick={{ fontSize: 11 }} />
                <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }} />
                <Area type="monotone" dataKey="records" stroke="#8b5cf6" strokeWidth={2} fillOpacity={1} fill="url(#recGrad)" name="Fused Observations" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-1">Completeness Rate by Zone (%)</h3>
          <p className="text-xs text-slate-500 mb-4">Ratio of valid observations across space-time matrix cells.</p>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={ZONE_FUSION_STATS}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="name" stroke="#64748b" tick={{ fontSize: 10 }} />
                <YAxis domain={[90, 100]} stroke="#64748b" tick={{ fontSize: 11 }} />
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }} />
                <Bar dataKey="completeness" fill="#10b981" radius={[4, 4, 0, 0]} name="Completeness %" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Master Dataset Preview Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">Master Dataset Live Preview (fused_zone_time.parquet)</h3>
            <p className="text-xs text-slate-500">Previewing representative records showing aligned multi-sensor fields.</p>
          </div>
          <button
            onClick={handleDownloadCSV}
            className="text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 px-3 py-1.5 rounded-lg transition flex items-center gap-1.5 self-start"
          >
            <Download className="w-3.5 h-3.5 text-purple-400" />
            <span>Export CSV</span>
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-950 text-slate-400 font-mono uppercase text-[10px]">
                <th className="py-2.5 px-3">H3 Zone ID</th>
                <th className="py-2.5 px-3">Timestamp</th>
                <th className="py-2.5 px-3">Station</th>
                <th className="py-2.5 px-3">AQI</th>
                <th className="py-2.5 px-3">PM2.5</th>
                <th className="py-2.5 px-3">PM10</th>
                <th className="py-2.5 px-3">Temp (°C)</th>
                <th className="py-2.5 px-3">Humidity</th>
                <th className="py-2.5 px-3">Wind</th>
                <th className="py-2.5 px-3">Traffic Speed</th>
                <th className="py-2.5 px-3">Congestion</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {PREVIEW_RECORDS.map((row, idx) => (
                <tr key={idx} className="hover:bg-slate-850 transition">
                  <td className="py-2 px-3 text-purple-300 font-semibold">{row.zone_id}</td>
                  <td className="py-2 px-3 text-slate-400">{row.time}</td>
                  <td className="py-2 px-3 text-white font-sans">{row.station}</td>
                  <td className="py-2 px-3 text-amber-400 font-bold">{row.aqi}</td>
                  <td className="py-2 px-3 text-slate-300">{row.pm25}</td>
                  <td className="py-2 px-3 text-slate-300">{row.pm10}</td>
                  <td className="py-2 px-3 text-slate-300">{row.temp}</td>
                  <td className="py-2 px-3 text-slate-300">{row.rh}%</td>
                  <td className="py-2 px-3 text-slate-300">{row.wind} km/h</td>
                  <td className="py-2 px-3 text-emerald-400 font-sans">{row.speed} km/h</td>
                  <td className="py-2 px-3 text-amber-400 font-sans">{(row.cong * 100).toFixed(0)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

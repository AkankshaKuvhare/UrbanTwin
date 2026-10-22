import React, { useState } from 'react';
import {
  TOMTOM_COLLECTOR_STATE,
  PUNE_PCMC_ROAD_SEGMENTS,
  ZONE_GATE_REPORT,
} from '../data/mockTraffic';
import { SYNTHETIC_HOURLY_TRAFFIC } from '../data/syntheticValidation';
import { ModuleHeader } from '../components/common/ModuleHeader';
import { SufficiencyGateBadge } from '../components/common/StatusBadge';
import { SyntheticWatermark } from '../components/common/SyntheticWatermark';
import {
  ShieldAlert,
  Server,
  Activity,
  Clock,
  Route,
  Database,
  Radio,
  CheckCircle2,
  AlertCircle,
} from 'lucide-react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
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

export const TrafficAnalyticsPage: React.FC = () => {
  const [showSyntheticValidation, setShowSyntheticValidation] = useState<boolean>(false);

  return (
    <div className="space-y-6">
      <ModuleHeader
        title="Traffic Flow & Congestion Intelligence"
        subtitle="TomTom Traffic Flow Segment API collector telemetry, arterial corridors, and Real-Traffic Sufficiency Gate status."
        tag="TomTom Segment API"
        what="Automated real-time collector polling TomTom Traffic Flow API for 142 arterial road segments across Pune PMC and PCMC."
        data="Current speed, free-flow speed, travel time, delay deficit, and congestion percentage. Polled every 15 minutes."
        outputs="Corridor speed telemetry, congestion index, collector heartbeat, sufficiency gate compliance audit."
        interactions="Toggle synthetic dry-run pipeline validation, view corridor segment table, inspect zone gate compliance."
      />

      {/* Ongoing Collection Status Banner */}
      <div className="bg-blue-950/40 border border-blue-500/40 rounded-xl p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-blue-200">
        <div className="flex items-center gap-3">
          <Radio className="w-5 h-5 text-blue-400 animate-pulse flex-shrink-0" />
          <div>
            <div className="font-semibold text-white text-sm">
              Traffic collection is ongoing.
            </div>
            <div className="text-xs text-blue-300">
              TomTom Segment API collector is actively polling 142 road segments every 15 minutes. Empirical causality gates remain closed until history threshold is achieved.
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="px-2.5 py-1 rounded bg-blue-900/60 text-blue-200 font-mono text-xs border border-blue-700 whitespace-nowrap">
            15m Scheduler Active
          </span>
        </div>
      </div>

      {/* Prominent Traffic Sufficiency Gate Diagnostic Banner */}
      <div className="bg-amber-950/30 border-2 border-amber-500/40 rounded-xl p-5 text-amber-200 space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-2.5">
            <ShieldAlert className="w-6 h-6 text-amber-400 flex-shrink-0" />
            <div>
              <h4 className="text-base font-bold text-amber-100">
                Real-Traffic Sufficiency Gate: LOCKED / INSUFFICIENT DATA
              </h4>
              <p className="text-xs text-amber-300">
                Scientific protocol strictly prohibits inferring traffic-to-AQI contribution percentages until both prerequisites pass.
              </p>
            </div>
          </div>
          <SufficiencyGateBadge passed={false} />
        </div>

        {/* Gate Requirements Checklist */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2 border-t border-amber-500/30">
          <div className="p-3 bg-slate-900/80 rounded-lg border border-amber-500/30 flex items-start gap-3">
            <div className="w-5 h-5 rounded-full bg-rose-900/50 text-rose-300 font-bold flex items-center justify-center text-xs flex-shrink-0 mt-0.5">
              ✕
            </div>
            <div className="text-xs space-y-0.5">
              <span className="font-bold text-white">Prerequisite 1: Continuous Observation Window</span>
              <p className="text-slate-300">
                Required: <strong>≥ 8.0 weeks (56 days)</strong> continuous real traffic history.
              </p>
              <div className="font-mono text-[11px] text-amber-300 font-semibold pt-1">
                Current: 0.2 weeks (1.4 days) • Deficit: -7.8 weeks
              </div>
            </div>
          </div>

          <div className="p-3 bg-slate-900/80 rounded-lg border border-amber-500/30 flex items-start gap-3">
            <div className="w-5 h-5 rounded-full bg-rose-900/50 text-rose-300 font-bold flex items-center justify-center text-xs flex-shrink-0 mt-0.5">
              ✕
            </div>
            <div className="text-xs space-y-0.5">
              <span className="font-bold text-white">Prerequisite 2: Zone Spatial Completeness</span>
              <p className="text-slate-300">
                Required: <strong>≥ 85.0% polling coverage</strong> across all 11 analyzed H3 zones.
              </p>
              <div className="font-mono text-[11px] text-amber-300 font-semibold pt-1">
                Current: 1.8% average coverage • 0 / 11 Zones Passing
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Collector Telemetry & Pipeline Metadata Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-slate-900 p-4 rounded-xl border border-slate-800 space-y-1">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Collector Status</span>
            <Server className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-lg font-bold text-emerald-400 flex items-center gap-1.5 font-mono">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span>Active Heartbeat</span>
          </div>
          <span className="text-[11px] text-slate-500 block">Polling every 15 minutes</span>
        </div>

        <div className="bg-slate-900 p-4 rounded-xl border border-slate-800 space-y-1">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Monitored Corridors</span>
            <Route className="w-4 h-4 text-orange-400" />
          </div>
          <div className="text-2xl font-bold text-white font-mono">
            {TOMTOM_COLLECTOR_STATE.monitoredSegments} Segments
          </div>
          <span className="text-[11px] text-slate-500 block">Pune PMC (84) • PCMC (58)</span>
        </div>

        <div className="bg-slate-900 p-4 rounded-xl border border-slate-800 space-y-1">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Observations in DB</span>
            <Database className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-bold text-amber-400 font-mono">
            {TOMTOM_COLLECTOR_STATE.observationCount} Records
          </div>
          <span className="text-[11px] text-slate-500 block">Staging active; accumulation pending</span>
        </div>

        <div className="bg-slate-900 p-4 rounded-xl border border-slate-800 space-y-1">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Collector Reliability</span>
            <Activity className="w-4 h-4 text-blue-400" />
          </div>
          <div className="text-2xl font-bold text-white font-mono">
            99.9%
          </div>
          <span className="text-[11px] text-slate-500 block">0 fatal errors • 2 network retries</span>
        </div>
      </div>

      {/* Explicit Congestion Formula Definition */}
      <div className="bg-slate-900 rounded-xl border border-slate-800 p-4 text-xs text-slate-300 space-y-2">
        <h4 className="font-bold text-white text-sm flex items-center gap-2">
          <span>Congestion Percentage Mathematical Formulation</span>
          <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded bg-slate-800 text-blue-400 border border-slate-700">
            TomTom Traffic Flow Standard
          </span>
        </h4>
        <div className="p-3 bg-slate-950 rounded-lg font-mono text-xs text-blue-300 border border-slate-800 overflow-x-auto">
          <code>
            CongestionPct(s, t) = max( 0.0, ((CurrentTravelTime(s, t) - FreeFlowTravelTime(s)) / FreeFlowTravelTime(s)) * 100.0 )
          </code>
        </div>
        <p className="text-[11px] text-slate-400 leading-relaxed">
          Where <em className="text-slate-300">CurrentTravelTime(s, t)</em> represents harmonic mean speed transit time across segment <em className="text-slate-300">s</em> at timestamp <em className="text-slate-300">t</em>,
          and <em className="text-slate-300">FreeFlowTravelTime(s)</em> is the 85th percentile uncongested baseline travel time calculated under free-flow conditions (speed limit / design speed).
        </p>
      </div>

      {/* Arterial Road Corridors Inventory Table */}
      <div className="bg-slate-900 rounded-xl border border-slate-800 p-5 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2 border-b border-slate-800">
          <div>
            <h3 className="text-base font-bold text-white tracking-tight">
              Monitored Arterial Road Segments (Pune PMC & PCMC)
            </h3>
            <p className="text-xs text-slate-400">
              Key arterial segments configured for TomTom Flow API automated polling. Real observed speed values pending gate release.
            </p>
          </div>
          <span className="text-xs text-slate-400 font-mono">
            {PUNE_PCMC_ROAD_SEGMENTS.length} Primary Corridors Configured
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-800/60 text-slate-400 font-semibold uppercase tracking-wider text-[11px]">
                <th className="py-2.5 px-3">Road Segment Name</th>
                <th className="py-2.5 px-3">Corridor</th>
                <th className="py-2.5 px-3">Area</th>
                <th className="py-2.5 px-3 font-mono">Length (km)</th>
                <th className="py-2.5 px-3 font-mono">Free-Flow Speed</th>
                <th className="py-2.5 px-3 font-mono">Current Observed Speed</th>
                <th className="py-2.5 px-3">Congestion %</th>
                <th className="py-2.5 px-3">Data State</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 font-mono">
              {PUNE_PCMC_ROAD_SEGMENTS.map((seg) => (
                <tr key={seg.segmentId} className="hover:bg-slate-800/40 transition-colors">
                  <td className="py-2.5 px-3 font-sans font-medium text-white">
                    {seg.name}
                  </td>
                  <td className="py-2.5 px-3 font-sans text-slate-400">{seg.corridor}</td>
                  <td className="py-2.5 px-3 font-sans uppercase text-[10px] text-slate-500">
                    {seg.area}
                  </td>
                  <td className="py-2.5 px-3 text-slate-300">{seg.lengthKm} km</td>
                  <td className="py-2.5 px-3 text-slate-300">{seg.freeFlowSpeedKmh} km/h</td>
                  <td className="py-2.5 px-3 text-slate-500">
                    {seg.currentSpeedKmh ?? '— (Awaiting Poll)'}
                  </td>
                  <td className="py-2.5 px-3 text-slate-500">
                    {seg.congestionPct ?? '— (Awaiting Poll)'}
                  </td>
                  <td className="py-2.5 px-3 font-sans">
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold bg-amber-900/30 text-amber-300 border border-amber-700/60">
                      <Clock className="w-3 h-3 text-amber-400" />
                      Pending History
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Synthetic Pipeline Validation Test Harness Toggle */}
      <div className="bg-slate-900 rounded-xl border border-slate-800 p-5 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-bold text-white tracking-tight">
                Synthetic Dry-Run Pipeline Validation Module
              </h3>
              <SyntheticWatermark size="sm" />
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Test harness to verify charting and modeling ETL scripts before real traffic ingestion completes.
            </p>
          </div>

          <button
            onClick={() => setShowSyntheticValidation(!showSyntheticValidation)}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all ${
              showSyntheticValidation
                ? 'bg-amber-900/40 text-amber-200 border-amber-600'
                : 'bg-slate-800 text-slate-300 border-slate-700 hover:bg-slate-700'
            }`}
          >
            {showSyntheticValidation ? 'Hide Synthetic Test Harness' : 'Show Synthetic Test Harness'}
          </button>
        </div>

        {showSyntheticValidation && (
          <div className="pt-3 border-t border-slate-800 space-y-4">
            <SyntheticWatermark size="banner" />

            <div className="h-72 w-full pt-2">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={SYNTHETIC_HOURLY_TRAFFIC}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="timeLabel" stroke="#64748b" fontSize={10} tickMargin={8} />
                  <YAxis stroke="#64748b" fontSize={11} unit=" %" domain={[0, 100]} tickMargin={8} />
                  <Tooltip contentStyle={DARK_TOOLTIP} />
                  <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '8px', color: '#94a3b8' }} />
                  <Bar
                    dataKey="syntheticCongestionPct"
                    name="Synthetic Congestion Index (% Delay) — PIPELINE VALIDATION ONLY"
                    fill="#f97316"
                    radius={[3, 3, 0, 0]}
                  />
                  <Line
                    type="monotone"
                    dataKey="syntheticAvgSpeedKmh"
                    name="Synthetic Avg Speed (km/h) — VALIDATION ONLY"
                    stroke="#3b82f6"
                    strokeWidth={2}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="text-[11px] text-amber-300 bg-amber-950/40 p-2.5 rounded border border-amber-800/60">
              <strong>Audit Guarantee:</strong> These synthetic observations are flagged with <code>is_synthetic: true</code> and strictly omitted from all empirical econometric tables, Granger causality tests, and Model C evaluations.
            </div>
          </div>
        )}
      </div>

      {/* Zone-by-Zone Sufficiency Gate Report Table */}
      <div className="bg-slate-900 rounded-xl border border-slate-800 p-5 space-y-3">
        <h3 className="text-base font-bold text-white tracking-tight">
          H3 Zone-by-Zone Traffic Sufficiency Gate Compliance Audit
        </h3>
        <p className="text-xs text-slate-400">
          Individual zone compliance assessment against the 8-week (56-day) continuous collection and 85% interval coverage standard.
        </p>

        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-800/60 text-slate-400 font-semibold uppercase tracking-wider text-[11px]">
                <th className="py-2 px-3">H3 Zone</th>
                <th className="py-2 px-3">Area</th>
                <th className="py-2 px-3 font-mono">Days Observed</th>
                <th className="py-2 px-3 font-mono">Days Required</th>
                <th className="py-2 px-3 font-mono">Interval Coverage</th>
                <th className="py-2 px-3 font-mono">Threshold</th>
                <th className="py-2 px-3">Gate Result</th>
                <th className="py-2 px-3">Diagnostic Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 font-mono">
              {ZONE_GATE_REPORT.map((z) => (
                <tr key={z.h3Index} className="hover:bg-slate-800/40">
                  <td className="py-2 px-3 font-sans font-medium text-white">{z.zoneName}</td>
                  <td className="py-2 px-3 font-sans uppercase text-[10px] text-slate-400">{z.area}</td>
                  <td className="py-2 px-3 text-slate-300">{z.observedDays} d</td>
                  <td className="py-2 px-3 text-slate-300">{z.requiredDays} d</td>
                  <td className="py-2 px-3 text-rose-400 font-semibold">{z.coveragePct}%</td>
                  <td className="py-2 px-3 text-slate-300">{z.thresholdPct}%</td>
                  <td className="py-2 px-3 font-sans">
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-950/60 text-rose-300 border border-rose-800">
                      FAIL
                    </span>
                  </td>
                  <td className="py-2 px-3 font-sans text-slate-400 text-[11px]">{z.reason}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

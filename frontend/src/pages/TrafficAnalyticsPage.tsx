import React, { useState } from 'react';
import {
  TOMTOM_COLLECTOR_STATE,
  PUNE_PCMC_ROAD_SEGMENTS,
  ZONE_GATE_REPORT,
} from '../data/mockTraffic';
import { SYNTHETIC_HOURLY_TRAFFIC } from '../data/syntheticValidation';
import { SectionHeader } from '../components/common/SectionHeader';
import { SufficiencyGateBadge } from '../components/common/StatusBadge';
import { SyntheticWatermark } from '../components/common/SyntheticWatermark';
import {
  ShieldAlert,
  Server,
  Activity,
  Clock,
  Route,
  Database,
} from 'lucide-react';
import {
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

export const TrafficAnalyticsPage: React.FC = () => {
  const [showSyntheticValidation, setShowSyntheticValidation] = useState<boolean>(false);

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <SectionHeader
        title="Traffic Flow & Congestion Intelligence"
        subtitle="TomTom Traffic Flow Segment API collector telemetry, arterial corridors, and Real-Traffic Sufficiency Gate status."
        tag="TomTom Segment API"
      />

      {/* Prominent Traffic Sufficiency Gate Diagnostic Banner */}
      <div className="bg-amber-500/10 border-2 border-amber-500/40 rounded-xl p-5 text-amber-950 space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-2.5">
            <ShieldAlert className="w-6 h-6 text-amber-600 flex-shrink-0" />
            <div>
              <h4 className="text-base font-bold text-amber-950">
                Real-Traffic Sufficiency Gate: LOCKED / INSUFFICIENT DATA
              </h4>
              <p className="text-xs text-amber-800">
                Scientific protocol strictly prohibits inferring traffic-to-AQI contribution percentages until both prerequisites pass.
              </p>
            </div>
          </div>
          <SufficiencyGateBadge passed={false} />
        </div>

        {/* Gate Requirements Checklist */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2 border-t border-amber-300/60">
          <div className="p-3 bg-white/80 rounded-lg border border-amber-200 flex items-start gap-3">
            <div className="w-5 h-5 rounded-full bg-rose-100 text-rose-700 font-bold flex items-center justify-center text-xs flex-shrink-0 mt-0.5">
              ✕
            </div>
            <div className="text-xs space-y-0.5">
              <span className="font-bold text-slate-800">Prerequisite 1: Continuous Observation Window</span>
              <p className="text-slate-600">
                Required: <strong>≥ 8.0 weeks (56 days)</strong> continuous real traffic history.
              </p>
              <div className="font-mono text-[11px] text-amber-900 font-semibold pt-1">
                Current: 0.2 weeks (1.4 days) • Deficit: -7.8 weeks
              </div>
            </div>
          </div>

          <div className="p-3 bg-white/80 rounded-lg border border-amber-200 flex items-start gap-3">
            <div className="w-5 h-5 rounded-full bg-rose-100 text-rose-700 font-bold flex items-center justify-center text-xs flex-shrink-0 mt-0.5">
              ✕
            </div>
            <div className="text-xs space-y-0.5">
              <span className="font-bold text-slate-800">Prerequisite 2: Zone Spatial Completeness</span>
              <p className="text-slate-600">
                Required: <strong>≥ 85.0% polling coverage</strong> across all 11 analyzed H3 zones.
              </p>
              <div className="font-mono text-[11px] text-amber-900 font-semibold pt-1">
                Current: 1.8% average coverage • 0 / 11 Zones Passing
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Collector Telemetry & Pipeline Metadata Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm space-y-1">
          <div className="flex items-center justify-between text-xs text-slate-500">
            <span>Collector Status</span>
            <Server className="w-4 h-4 text-teal-600" />
          </div>
          <div className="text-lg font-bold text-emerald-700 flex items-center gap-1.5 font-mono">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span>Active Heartbeat</span>
          </div>
          <span className="text-[11px] text-slate-400 block">Polling every 15 minutes</span>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm space-y-1">
          <div className="flex items-center justify-between text-xs text-slate-500">
            <span>Monitored Road Corridors</span>
            <Route className="w-4 h-4 text-orange-600" />
          </div>
          <div className="text-2xl font-bold text-slate-900 font-mono">
            {TOMTOM_COLLECTOR_STATE.monitoredSegments} Segments
          </div>
          <span className="text-[11px] text-slate-400 block">Pune PMC (84) • PCMC (58)</span>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm space-y-1">
          <div className="flex items-center justify-between text-xs text-slate-500">
            <span>Real Observations in Storage</span>
            <Database className="w-4 h-4 text-amber-600" />
          </div>
          <div className="text-2xl font-bold text-amber-800 font-mono">
            {TOMTOM_COLLECTOR_STATE.observationCount} Records
          </div>
          <span className="text-[11px] text-slate-400 block">Staging active; accumulation pending</span>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm space-y-1">
          <div className="flex items-center justify-between text-xs text-slate-500">
            <span>Collector Reliability</span>
            <Activity className="w-4 h-4 text-teal-600" />
          </div>
          <div className="text-2xl font-bold text-slate-900 font-mono">
            99.9%
          </div>
          <span className="text-[11px] text-slate-400 block">0 fatal errors • 2 network retries</span>
        </div>
      </div>

      {/* Explicit Congestion Formula Definition */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-4 text-xs text-slate-600 space-y-2">
        <h4 className="font-bold text-slate-800 text-sm flex items-center gap-2">
          <span>Congestion Percentage Mathematical Formulation</span>
          <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded bg-slate-100 text-slate-700">
            TomTom Traffic Flow Standard
          </span>
        </h4>
        <div className="p-3 bg-slate-50 rounded-lg font-mono text-xs text-slate-800 border border-slate-200 overflow-x-auto">
          <code>
            CongestionPct(s, t) = max( 0.0, ((CurrentTravelTime(s, t) - FreeFlowTravelTime(s)) / FreeFlowTravelTime(s)) * 100.0 )
          </code>
        </div>
        <p className="text-[11px] text-slate-500 leading-relaxed">
          Where <em>CurrentTravelTime(s, t)</em> represents harmonic mean speed transit time across segment <em>s</em> at timestamp <em>t</em>,
          and <em>FreeFlowTravelTime(s)</em> is the 85th percentile uncongested baseline travel time calculated under free-flow conditions (speed limit / design speed).
        </p>
      </div>

      {/* Arterial Road Corridors Inventory Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2 border-b border-slate-100">
          <div>
            <h3 className="text-base font-bold text-slate-900 tracking-tight">
              Monitored Arterial Road Segments (Pune PMC & PCMC)
            </h3>
            <p className="text-xs text-slate-500">
              Key arterial segments configured for TomTom Flow API automated polling. Real observed speed values pending gate release.
            </p>
          </div>
          <span className="text-xs text-slate-500 font-mono">
            {PUNE_PCMC_ROAD_SEGMENTS.length} Primary Corridors Configured
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-200 bg-slate-50 text-slate-600 font-semibold uppercase tracking-wider text-[11px]">
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
            <tbody className="divide-y divide-slate-100 font-mono">
              {PUNE_PCMC_ROAD_SEGMENTS.map((seg) => (
                <tr key={seg.segmentId} className="hover:bg-slate-50/80 transition-colors">
                  <td className="py-2.5 px-3 font-sans font-medium text-slate-900">
                    {seg.name}
                  </td>
                  <td className="py-2.5 px-3 font-sans text-slate-600">{seg.corridor}</td>
                  <td className="py-2.5 px-3 font-sans uppercase text-[10px] text-slate-500">
                    {seg.area}
                  </td>
                  <td className="py-2.5 px-3 text-slate-800">{seg.lengthKm} km</td>
                  <td className="py-2.5 px-3 text-slate-800">{seg.freeFlowSpeedKmh} km/h</td>
                  <td className="py-2.5 px-3 text-slate-400">
                    {seg.currentSpeedKmh ?? '— (Awaiting Poll)'}
                  </td>
                  <td className="py-2.5 px-3 text-slate-400">
                    {seg.congestionPct ?? '— (Awaiting Poll)'}
                  </td>
                  <td className="py-2.5 px-3 font-sans">
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold bg-amber-50 text-amber-800 border border-amber-200">
                      <Clock className="w-3 h-3 text-amber-600" />
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
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-bold text-slate-900 tracking-tight">
                Synthetic Dry-Run Pipeline Validation Module
              </h3>
              <SyntheticWatermark size="sm" />
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Test harness to verify charting and modeling ETL scripts before real traffic ingestion completes.
            </p>
          </div>

          <button
            onClick={() => setShowSyntheticValidation(!showSyntheticValidation)}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all ${
              showSyntheticValidation
                ? 'bg-amber-100 text-amber-900 border-amber-300'
                : 'bg-slate-50 text-slate-700 border-slate-300 hover:bg-slate-100'
            }`}
          >
            {showSyntheticValidation ? 'Hide Synthetic Test Harness' : 'Show Synthetic Test Harness'}
          </button>
        </div>

        {showSyntheticValidation && (
          <div className="pt-3 border-t border-slate-100 space-y-4">
            <SyntheticWatermark size="banner" />

            <div className="h-72 w-full pt-2">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={SYNTHETIC_HOURLY_TRAFFIC}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="timeLabel" stroke="#94a3b8" fontSize={10} tickMargin={8} />
                  <YAxis stroke="#94a3b8" fontSize={11} unit=" %" domain={[0, 100]} tickMargin={8} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#ffffff',
                      borderRadius: '8px',
                      borderColor: '#e2e8f0',
                      fontSize: '12px',
                    }}
                  />
                  <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '8px' }} />
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
                    stroke="#0d9488"
                    strokeWidth={2}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="text-[11px] text-amber-800 bg-amber-50 p-2.5 rounded border border-amber-200">
              <strong>Audit Guarantee:</strong> These synthetic observations are flagged with <code>is_synthetic: true</code> and strictly omitted from all empirical econometric tables, Granger causality tests, and Model C evaluations.
            </div>
          </div>
        )}
      </div>

      {/* Zone-by-Zone Sufficiency Gate Report Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-3">
        <h3 className="text-base font-bold text-slate-900 tracking-tight">
          H3 Zone-by-Zone Traffic Sufficiency Gate Compliance Audit
        </h3>
        <p className="text-xs text-slate-500">
          Individual zone compliance assessment against the 8-week (56-day) continuous collection and 85% interval coverage standard.
        </p>

        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-200 bg-slate-50 text-slate-600 font-semibold uppercase tracking-wider text-[11px]">
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
            <tbody className="divide-y divide-slate-100 font-mono">
              {ZONE_GATE_REPORT.map((z) => (
                <tr key={z.h3Index} className="hover:bg-slate-50/80">
                  <td className="py-2 px-3 font-sans font-medium text-slate-900">{z.zoneName}</td>
                  <td className="py-2 px-3 font-sans uppercase text-[10px] text-slate-500">{z.area}</td>
                  <td className="py-2 px-3 text-slate-700">{z.observedDays} d</td>
                  <td className="py-2 px-3 text-slate-700">{z.requiredDays} d</td>
                  <td className="py-2 px-3 text-rose-700 font-semibold">{z.coveragePct}%</td>
                  <td className="py-2 px-3 text-slate-700">{z.thresholdPct}%</td>
                  <td className="py-2 px-3 font-sans">
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-50 text-rose-700 border border-rose-200">
                      FAIL
                    </span>
                  </td>
                  <td className="py-2 px-3 font-sans text-slate-500 text-[11px]">{z.reason}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

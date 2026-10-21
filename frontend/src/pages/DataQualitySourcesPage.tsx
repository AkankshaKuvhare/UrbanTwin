import React, { useState } from 'react';
import { PUNE_PCMC_STATIONS } from '../data/stations';
import {
  STATION_QUALITY_REPORTS,
  COLLECTOR_RUN_LOGS,
  DATA_DICTIONARY,
} from '../data/sourcesData';
import { SectionHeader } from '../components/common/SectionHeader';
import {
  CheckCircle2,
} from 'lucide-react';

export const DataQualitySourcesPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'inventory' | 'telemetry' | 'dictionary' | 'governance'>('inventory');

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <SectionHeader
        title="Data Quality, Provenance & Governance"
        subtitle="Transparent audit trails, OpenAQ station QA/QC, API ingestion telemetry, licensing metadata, and data dictionaries."
        tag="Data Governance & QA/QC"
      />

      {/* Dataset Separation & Scientific Classification Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm space-y-1.5 border-t-4 border-t-emerald-600">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase text-emerald-800">Real Ambient AQI</span>
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          </div>
          <div className="text-lg font-bold text-slate-900 font-mono">OpenAQ / CPCB</div>
          <p className="text-xs text-slate-500">
            5 Verified in-situ stations in Pune & PCMC. 96.3% valid observations.
          </p>
          <span className="text-[10px] font-mono text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded inline-block">
            Status: Fully Connected
          </span>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm space-y-1.5 border-t-4 border-t-sky-600">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase text-sky-800">Real Meteorology</span>
            <span className="w-2 h-2 rounded-full bg-sky-500 animate-pulse" />
          </div>
          <div className="text-lg font-bold text-slate-900 font-mono">Open-Meteo ERA5</div>
          <p className="text-xs text-slate-500">
            Hourly reanalysis & GFS numerical forecast (~11 km grid resolution).
          </p>
          <span className="text-[10px] font-mono text-sky-700 bg-sky-50 px-2 py-0.5 rounded inline-block">
            Status: Fully Connected
          </span>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm space-y-1.5 border-t-4 border-t-amber-500">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase text-amber-800">Real Traffic Flow</span>
            <span className="w-2 h-2 rounded-full bg-amber-500" />
          </div>
          <div className="text-lg font-bold text-slate-900 font-mono">TomTom Segment API</div>
          <p className="text-xs text-slate-500">
            142 monitored arterial road corridors. Sufficiency gate: GATED.
          </p>
          <span className="text-[10px] font-mono text-amber-800 bg-amber-50 px-2 py-0.5 rounded inline-block font-semibold">
            Status: Accumulating (0.2/8 wks)
          </span>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm space-y-1.5 border-t-4 border-t-slate-400">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase text-slate-600">Synthetic Test Harness</span>
            <span className="w-2 h-2 rounded-full bg-slate-400" />
          </div>
          <div className="text-lg font-bold text-slate-900 font-mono">Dry-Run Pipeline</div>
          <p className="text-xs text-slate-500">
            Artificially generated strictly for UI pipeline test harness. Excluded from research.
          </p>
          <span className="text-[10px] font-mono text-slate-600 bg-slate-100 px-2 py-0.5 rounded inline-block">
            Status: Sandboxed
          </span>
        </div>
      </div>

      {/* Navigation Sub-Tabs */}
      <div className="flex items-center gap-1 bg-slate-200/70 p-1 rounded-xl text-xs font-semibold w-fit">
        <button
          onClick={() => setActiveTab('inventory')}
          className={`px-3.5 py-1.5 rounded-lg transition-all ${
            activeTab === 'inventory' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-600 hover:text-slate-900'
          }`}
        >
          Station QA/QC Inventory
        </button>
        <button
          onClick={() => setActiveTab('telemetry')}
          className={`px-3.5 py-1.5 rounded-lg transition-all ${
            activeTab === 'telemetry' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-600 hover:text-slate-900'
          }`}
        >
          API Collector Logs
        </button>
        <button
          onClick={() => setActiveTab('dictionary')}
          className={`px-3.5 py-1.5 rounded-lg transition-all ${
            activeTab === 'dictionary' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-600 hover:text-slate-900'
          }`}
        >
          Data Dictionary & Units
        </button>
        <button
          onClick={() => setActiveTab('governance')}
          className={`px-3.5 py-1.5 rounded-lg transition-all ${
            activeTab === 'governance' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-600 hover:text-slate-900'
          }`}
        >
          Licenses & Citations
        </button>
      </div>

      {/* Tab 1: Station Inventory & Data Quality Breakdown */}
      {activeTab === 'inventory' && (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-4">
          <div className="pb-2 border-b border-slate-100">
            <h3 className="text-base font-bold text-slate-900 tracking-tight">
              OpenAQ Continuous Station Inventory & Completeness Audit
            </h3>
            <p className="text-xs text-slate-500">
              Verified ground monitoring stations, sensor locations, missingness percentages, duplicate audits, and outlier flags.
            </p>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50 text-slate-600 font-semibold uppercase tracking-wider text-[11px]">
                  <th className="py-2.5 px-3">Station & Location</th>
                  <th className="py-2.5 px-3">Coordinates (Lat, Lon)</th>
                  <th className="py-2.5 px-3">Operator</th>
                  <th className="py-2.5 px-3 font-mono">Records Rcvd / Exp</th>
                  <th className="py-2.5 px-3 font-mono">Missing (%)</th>
                  <th className="py-2.5 px-3 font-mono">Duplicates</th>
                  <th className="py-2.5 px-3 font-mono">Outliers Flagged</th>
                  <th className="py-2.5 px-3">Quality Score</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-mono">
                {STATION_QUALITY_REPORTS.map((rep) => {
                  const st = PUNE_PCMC_STATIONS.find((s) => s.id === rep.stationId);
                  return (
                    <tr key={rep.stationId} className="hover:bg-slate-50/80 transition-colors">
                      <td className="py-2.5 px-3 font-sans font-semibold text-slate-900">
                        <div>{rep.stationName}</div>
                        <span className="text-[10px] text-slate-400 font-sans">{st?.stationType}</span>
                      </td>
                      <td className="py-2.5 px-3 text-slate-600">
                        {st?.lat.toFixed(4)}°N, {st?.lon.toFixed(4)}°E
                      </td>
                      <td className="py-2.5 px-3 font-sans text-slate-600">{st?.operator}</td>
                      <td className="py-2.5 px-3 text-slate-800">
                        {rep.totalRecordsReceived} / {rep.totalRecordsExpected}
                      </td>
                      <td className="py-2.5 px-3 text-emerald-700 font-semibold">
                        {rep.missingPct}%
                      </td>
                      <td className="py-2.5 px-3 text-slate-600">{rep.duplicateCount}</td>
                      <td className="py-2.5 px-3 text-amber-700">{rep.outlierCount} spikes</td>
                      <td className="py-2.5 px-3 font-sans">
                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-800 border border-emerald-200">
                          <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                          {rep.validObservationsPct}% Valid
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          <div className="p-3 bg-slate-50 rounded-lg text-xs text-slate-600 space-y-1 border border-slate-200">
            <strong>Outlier Filtering Protocol:</strong> Automatic filters reject unphysical negative concentrations (&lt; 0 µg/m³), sensor flatlines (&gt; 6 consecutive identical float values), and impossible instantaneous rate-of-change spikes (&gt; 250 µg/m³/hr).
          </div>
        </div>
      )}

      {/* Tab 2: API Collector Run History */}
      {activeTab === 'telemetry' && (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-4">
          <div className="pb-2 border-b border-slate-100">
            <h3 className="text-base font-bold text-slate-900 tracking-tight">
              API Collector Run History & Latency Log
            </h3>
            <p className="text-xs text-slate-500">
              Live audit of background ingestion tasks for OpenAQ, Open-Meteo, and TomTom traffic workers.
            </p>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50 text-slate-600 font-semibold uppercase text-[11px]">
                  <th className="py-2 px-3">Run ID</th>
                  <th className="py-2 px-3">Data Feed Source</th>
                  <th className="py-2 px-3">Timestamp (IST)</th>
                  <th className="py-2 px-3 font-mono">Status</th>
                  <th className="py-2 px-3 font-mono">HTTP</th>
                  <th className="py-2 px-3 font-mono">Duration</th>
                  <th className="py-2 px-3">Execution Diagnostic</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-mono">
                {COLLECTOR_RUN_LOGS.map((log) => (
                  <tr key={log.runId} className="hover:bg-slate-50">
                    <td className="py-2 px-3 font-semibold text-slate-800">{log.runId}</td>
                    <td className="py-2 px-3 font-sans font-medium text-slate-900">{log.source}</td>
                    <td className="py-2 px-3 text-slate-600">{log.timestamp}</td>
                    <td className="py-2 px-3 font-sans">
                      {log.status === 'SUCCESS' && (
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                          SUCCESS
                        </span>
                      )}
                      {log.status === 'WARNING' && (
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-50 text-amber-700 border border-amber-200">
                          WARNING
                        </span>
                      )}
                      {log.status === 'GATED' && (
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-50 text-amber-800 border border-amber-300">
                          GATED
                        </span>
                      )}
                    </td>
                    <td className="py-2 px-3 text-slate-700">{log.httpStatus}</td>
                    <td className="py-2 px-3 text-slate-700">{log.durationMs} ms</td>
                    <td className="py-2 px-3 font-sans text-slate-600 text-[11px]">{log.message}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 3: Data Dictionary */}
      {activeTab === 'dictionary' && (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-4">
          <div className="pb-2 border-b border-slate-100">
            <h3 className="text-base font-bold text-slate-900 tracking-tight">
              Standardized Data Dictionary & Measurement Units
            </h3>
            <p className="text-xs text-slate-500">
              Canonical nomenclature, physical measurement units, averaging intervals, and CPCB national ambient regulatory standards.
            </p>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50 text-slate-600 font-semibold uppercase text-[11px]">
                  <th className="py-2 px-3">Parameter Code</th>
                  <th className="py-2 px-3">Canonical Description</th>
                  <th className="py-2 px-3">Primary Source</th>
                  <th className="py-2 px-3 font-mono">Unit</th>
                  <th className="py-2 px-3">Averaging Window</th>
                  <th className="py-2 px-3 font-mono">CPCB NAAQS Standard</th>
                  <th className="py-2 px-3">Atmospheric Chemistry Function</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-mono">
                {DATA_DICTIONARY.map((entry) => (
                  <tr key={entry.parameter} className="hover:bg-slate-50">
                    <td className="py-2 px-3 font-bold text-slate-900 font-sans">{entry.parameter}</td>
                    <td className="py-2 px-3 font-sans text-slate-800 font-medium">{entry.canonicalName}</td>
                    <td className="py-2 px-3 font-sans text-slate-600">{entry.source}</td>
                    <td className="py-2 px-3 text-teal-700 font-bold">{entry.unit}</td>
                    <td className="py-2 px-3 font-sans text-slate-600">{entry.averagingWindow}</td>
                    <td className="py-2 px-3 text-slate-800">{entry.cpcbStandard}</td>
                    <td className="py-2 px-3 font-sans text-slate-500 text-[11px]">{entry.description}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 4: Provenance, Licenses & Citations */}
      {activeTab === 'governance' && (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-4">
          <div className="pb-2 border-b border-slate-100">
            <h3 className="text-base font-bold text-slate-900 tracking-tight">
              Data Provenance, Open Data Licenses & Academic Attribution
            </h3>
            <p className="text-xs text-slate-500">
              Licensing compliance for public and commercial API datasets used within the UrbanTwin research framework.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-2">
              <h4 className="font-bold text-slate-900 flex items-center justify-between">
                <span>OpenAQ Ambient Air Quality Feed</span>
                <span className="font-mono text-[10px] bg-slate-200 px-2 py-0.5 rounded">CC-BY 4.0</span>
              </h4>
              <p className="text-slate-600 leading-relaxed">
                OpenAQ aggregates open air quality observations from governmental monitoring agencies including Central Pollution Control Board (CPCB) and Maharashtra Pollution Control Board (MPCB). Data is licensed under Creative Commons Attribution 4.0 International.
              </p>
              <div className="text-[11px] text-teal-700 font-medium">
                Citation: OpenAQ Community (2026). Open Air Quality Data Platform.
              </div>
            </div>

            <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-2">
              <h4 className="font-bold text-slate-900 flex items-center justify-between">
                <span>Open-Meteo Weather API</span>
                <span className="font-mono text-[10px] bg-slate-200 px-2 py-0.5 rounded">CC-BY 4.0 / ODbL</span>
              </h4>
              <p className="text-slate-600 leading-relaxed">
                Meteorological historical variables and boundary layer heights derived from ECMWF ERA5 atmospheric reanalysis models and Copernicus Climate Change Service (C3S).
              </p>
              <div className="text-[11px] text-teal-700 font-medium">
                Citation: Hersbach et al. (2020). The ERA5 global reanalysis. Q.J.R. Meteorol. Soc.
              </div>
            </div>

            <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-2">
              <h4 className="font-bold text-slate-900 flex items-center justify-between">
                <span>TomTom Traffic Flow Segment API</span>
                <span className="font-mono text-[10px] bg-slate-200 px-2 py-0.5 rounded">Commercial Academic Tier</span>
              </h4>
              <p className="text-slate-600 leading-relaxed">
                Real-time harmonic mean travel times and delay estimates queried over defined Pune/PCMC corridor segments. Used under developer terms with automated rate-limiting.
              </p>
              <div className="text-[11px] text-teal-700 font-medium">
                Reference: TomTom NV Traffic Flow API v4 Documentation.
              </div>
            </div>

            <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-2">
              <h4 className="font-bold text-slate-900 flex items-center justify-between">
                <span>Uber H3 Spatial Indexing System</span>
                <span className="font-mono text-[10px] bg-slate-200 px-2 py-0.5 rounded">Apache 2.0</span>
              </h4>
              <p className="text-slate-600 leading-relaxed">
                Discrete global grid system partitioned into resolution 7 hexagonal cells (~1.2 km edge length) for uniform urban partition and spatial autocorrelation diagnostics.
              </p>
              <div className="text-[11px] text-teal-700 font-medium">
                Citation: Uber Technologies Inc. (2018). H3: A Hexagonal Hierarchical Spatial Index.
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

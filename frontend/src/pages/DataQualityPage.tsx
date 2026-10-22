import React, { useState } from 'react';
import { ModuleHeader } from '../components/common/ModuleHeader';
import { KPICard } from '../components/common/KPICard';
import { PUNE_PCMC_STATIONS } from '../data/stations';
import {
  CheckCircle2,
  AlertTriangle,
  FileText,
  Database,
  BarChart2,
  Calendar,
  Layers,
  ShieldCheck,
  Download,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

const QA_STATION_METRICS = [
  { name: 'Shivajinagar (IITM)', records: 750, validPct: 98.4, missingPct: 1.6, duplicates: 0, outliers: 3 },
  { name: 'SPPU Campus (MPCB)', records: 750, validPct: 97.8, missingPct: 2.2, duplicates: 0, outliers: 2 },
  { name: 'Karve Road (MPCB)', records: 750, validPct: 96.9, missingPct: 3.1, duplicates: 0, outliers: 5 },
  { name: 'Katraj Dairy (MPCB)', records: 750, validPct: 95.4, missingPct: 4.6, duplicates: 0, outliers: 4 },
  { name: 'Park St Wakad (PCMC)', records: 751, validPct: 99.1, missingPct: 0.9, duplicates: 0, outliers: 1 },
];

const VALIDATION_HISTORY = [
  { runId: 'VAL-2026-10-22', date: '22 Oct 2026 09:05', passedChecks: '24 / 24', score: '100%', status: 'PASSED', target: 'Milestone 10 Simulator Engine' },
  { runId: 'VAL-2026-10-22-GIS', date: '22 Oct 2026 08:42', passedChecks: '30 / 30', score: '100%', status: 'PASSED', target: 'Milestone 9 GIS & Digital Twin' },
  { runId: 'VAL-2026-10-21-REL', date: '21 Oct 2026 21:50', passedChecks: '28 / 28', score: '100%', status: 'PASSED', target: 'Milestone 8 Relationship Analytics' },
  { runId: 'VAL-2026-10-21-SYS', date: '21 Oct 2026 21:45', passedChecks: '18 / 18', score: '97%', status: 'PASSED', target: 'Milestone 7 System-Wide Pipeline' },
];

export const DataQualityPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'audit' | 'stations' | 'history'>('audit');

  return (
    <div className="space-y-6 animate-fadeIn">
      <ModuleHeader
        title="Data Quality &amp; Governance"
        badge="QA/QC Engine"
        badgeColor="bg-emerald-500/20 text-emerald-300 border-emerald-500/30"
        purpose="Monitor data integrity, sensor completeness, missingness ratios, outlier distributions, and formal audit history across the UrbanTwin conurbation."
        whatItDoes="Executes multi-stage validation checks (completeness checks, duplicate elimination, physical boundary enforcement, zero-variance screening, and outlier isolation)."
        dataUsed="3,751 fused space-time records, 5 CAAQMS station audit logs, Open-Meteo coverage logs, and TomTom checkpoint polls."
        outputsGenerated="Station QA/QC scorecard, automated pipeline validation reports (data_quality_summary.json, validation_report.html), and error logs."
        interactions="Inspect individual station completeness, review chronological validation test history, and download audit summaries."
      />

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <KPICard
          title="Overall Quality Score"
          value="98.2%"
          subtitle="Validated Observations"
          status="good"
          icon={<ShieldCheck className="w-4 h-4 text-emerald-400" />}
        />
        <KPICard
          title="Completeness Rate"
          value="97.5%"
          subtitle="All 5 Stations"
          status="good"
          icon={<CheckCircle2 className="w-4 h-4 text-blue-400" />}
        />
        <KPICard
          title="Duplicate Records"
          value="0"
          subtitle="Zero Redundancy"
          status="good"
          icon={<Database className="w-4 h-4 text-purple-400" />}
        />
        <KPICard
          title="Spatial Coverage"
          value="100%"
          subtitle="PMC &amp; PCMC Conurbation"
          status="good"
          icon={<Layers className="w-4 h-4 text-teal-400" />}
        />
        <KPICard
          title="Total Outliers Filtered"
          value="15 Points"
          subtitle="Isolated via IQR 3.0"
          status="neutral"
          icon={<AlertTriangle className="w-4 h-4 text-amber-400" />}
        />
      </div>

      {/* Station QA/QC Scorecard */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-sm font-bold text-white uppercase tracking-wider">Station QA/QC Completeness Scorecard</h2>
            <p className="text-xs text-slate-400">Validity and missing rates across in-situ CAAQMS continuous monitors.</p>
          </div>
          <span className="text-[10px] font-mono text-emerald-400 bg-emerald-500/10 border border-emerald-500/30 px-2.5 py-1 rounded">
            5/5 Stations Certified
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-950 text-slate-400 font-mono uppercase text-[10px]">
                <th className="py-2.5 px-3">Monitoring Station</th>
                <th className="py-2.5 px-3">Records Fused</th>
                <th className="py-2.5 px-3">Valid %</th>
                <th className="py-2.5 px-3">Missing %</th>
                <th className="py-2.5 px-3">Duplicates</th>
                <th className="py-2.5 px-3">Outliers Isolated</th>
                <th className="py-2.5 px-3">Audit Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-sans">
              {QA_STATION_METRICS.map((st, idx) => (
                <tr key={idx} className="hover:bg-slate-850 transition">
                  <td className="py-2.5 px-3 font-semibold text-white">{st.name}</td>
                  <td className="py-2.5 px-3 text-slate-300 font-mono">{st.records}</td>
                  <td className="py-2.5 px-3 text-emerald-400 font-bold font-mono">{st.validPct}%</td>
                  <td className="py-2.5 px-3 text-slate-400 font-mono">{st.missingPct}%</td>
                  <td className="py-2.5 px-3 text-slate-400 font-mono">{st.duplicates}</td>
                  <td className="py-2.5 px-3 text-amber-400 font-mono">{st.outliers}</td>
                  <td className="py-2.5 px-3">
                    <span className="text-[10px] font-semibold text-emerald-400 bg-emerald-500/10 border border-emerald-500/30 px-2 py-0.5 rounded">
                      VERIFIED
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Validation Test Run History */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3">Automated Validation Test History</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-950 text-slate-400 font-mono uppercase text-[10px]">
                <th className="py-2.5 px-3">Run ID</th>
                <th className="py-2.5 px-3">Date</th>
                <th className="py-2.5 px-3">Target Module</th>
                <th className="py-2.5 px-3">Passed Checks</th>
                <th className="py-2.5 px-3">Quality Score</th>
                <th className="py-2.5 px-3">Outcome</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-sans">
              {VALIDATION_HISTORY.map((h, idx) => (
                <tr key={idx} className="hover:bg-slate-850 transition">
                  <td className="py-2.5 px-3 font-mono text-blue-400 font-semibold">{h.runId}</td>
                  <td className="py-2.5 px-3 text-slate-400 font-mono">{h.date}</td>
                  <td className="py-2.5 px-3 text-white font-medium">{h.target}</td>
                  <td className="py-2.5 px-3 text-slate-300 font-mono">{h.passedChecks}</td>
                  <td className="py-2.5 px-3 text-emerald-400 font-bold font-mono">{h.score}</td>
                  <td className="py-2.5 px-3">
                    <span className="text-[10px] font-bold text-emerald-400 bg-emerald-500/10 border border-emerald-500/30 px-2 py-0.5 rounded">
                      {h.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

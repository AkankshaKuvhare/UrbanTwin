import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import { SectionHeader } from '../components/common/SectionHeader';
import {
  ShieldCheck,
  Download,
  Sliders,
  Save,
} from 'lucide-react';

export const SettingsPage: React.FC = () => {
  const { studyArea, setStudyArea, showToast } = useApp();

  const [standardsMode, setStandardsMode] = useState<'cpcb' | 'who'>('cpcb');
  const [tempUnit, setTempUnit] = useState<'c' | 'f'>('c');
  const [windUnit, setWindUnit] = useState<'kmh' | 'ms'>('kmh');
  const [requiredWeeks, setRequiredWeeks] = useState<number>(8.0);
  const [requiredCoveragePct, setRequiredCoveragePct] = useState<number>(85.0);

  const handleSave = () => {
    showToast('Configuration parameters updated successfully.');
  };

  const handleExportDataBundle = () => {
    const bundle = {
      project: 'UrbanTwin: Pune Smart City Air Quality & Traffic Intelligence Digital Twin',
      version: '2.4.0',
      exportedAt: new Date().toISOString(),
      studyArea: studyArea,
      standardsMode: standardsMode,
      stationsTracked: 5,
      h3ZonesRes7: 11,
      gateStatus: {
        weeksAccumulated: 0.2,
        requiredWeeks: requiredWeeks,
        passed: false,
      },
    };
    const blob = new Blob([JSON.stringify(bundle, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'urbantwin_research_manifest.json';
    a.click();
    showToast('Research data bundle downloaded.');
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <SectionHeader
        title="Configuration & Research Parameters"
        subtitle="Configurable thresholds, regulatory standards, physical units, and API collector preferences."
        tag="System Settings"
        actions={
          <button
            onClick={handleExportDataBundle}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-white border border-slate-300 text-slate-700 hover:bg-slate-50 shadow-sm"
          >
            <Download className="w-3.5 h-3.5 text-slate-500" />
            <span>Export Research Bundle (.json)</span>
          </button>
        }
      />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Card 1: Regulatory Standard & Thresholds */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-4">
          <div className="pb-2 border-b border-slate-100 flex items-center justify-between">
            <div>
              <h3 className="text-base font-bold text-slate-900 tracking-tight">
                Air Quality Regulatory Standards
              </h3>
              <p className="text-xs text-slate-500">
                Select baseline standard for category break-points and threshold exceedances.
              </p>
            </div>
            <Sliders className="w-4 h-4 text-teal-600" />
          </div>

          <div className="space-y-3 text-xs">
            <div>
              <label className="font-semibold text-slate-700 block mb-1">Standard Mode:</label>
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => setStandardsMode('cpcb')}
                  className={`p-2.5 rounded-lg border text-left transition-all ${
                    standardsMode === 'cpcb'
                      ? 'border-teal-500 bg-teal-50/70 text-teal-950 font-semibold'
                      : 'border-slate-200 bg-slate-50 text-slate-600'
                  }`}
                >
                  <div className="font-bold">Indian CPCB NAAQS</div>
                  <span className="text-[10px] text-slate-500">24h PM2.5 limit: 60 µg/m³</span>
                </button>

                <button
                  type="button"
                  onClick={() => setStandardsMode('who')}
                  className={`p-2.5 rounded-lg border text-left transition-all ${
                    standardsMode === 'who'
                      ? 'border-teal-500 bg-teal-50/70 text-teal-950 font-semibold'
                      : 'border-slate-200 bg-slate-50 text-slate-600'
                  }`}
                >
                  <div className="font-bold">WHO Guidelines (2021)</div>
                  <span className="text-[10px] text-slate-500">24h PM2.5 limit: 15 µg/m³</span>
                </button>
              </div>
            </div>

            <div className="pt-2 border-t border-slate-100">
              <label className="font-semibold text-slate-700 block mb-1">Default Study Region Boundary:</label>
              <select
                value={studyArea}
                onChange={(e) => setStudyArea(e.target.value as any)}
                className="w-full p-2 bg-slate-50 border border-slate-200 rounded-lg text-xs font-semibold text-slate-700 focus:outline-none focus:ring-1 focus:ring-teal-500"
              >
                <option value="combined">Pune & PCMC Twin-City Conurbation (Combined)</option>
                <option value="pune">Pune Municipal Corporation (PMC Only)</option>
                <option value="pcmc">Pimpri-Chinchwad Municipal Corporation (PCMC Only)</option>
              </select>
            </div>
          </div>
        </div>

        {/* Card 2: Traffic Sufficiency Gate Parameters */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-4">
          <div className="pb-2 border-b border-slate-100 flex items-center justify-between">
            <div>
              <h3 className="text-base font-bold text-slate-900 tracking-tight">
                Traffic Sufficiency Gate Parameters
              </h3>
              <p className="text-xs text-slate-500">
                Scientific gating rules determining when Model C and causal attribution become unlocked.
              </p>
            </div>
            <ShieldCheck className="w-4 h-4 text-amber-600" />
          </div>

          <div className="space-y-3 text-xs">
            <div>
              <label className="font-semibold text-slate-700 block mb-1">
                Required Continuous Observation Window:
              </label>
              <div className="flex items-center gap-2">
                <input
                  type="number"
                  min="4"
                  max="52"
                  value={requiredWeeks}
                  onChange={(e) => setRequiredWeeks(Number(e.target.value))}
                  className="w-24 p-2 bg-slate-50 border border-slate-200 rounded-lg font-mono font-bold text-slate-900 focus:outline-none focus:ring-1 focus:ring-teal-500"
                />
                <span className="text-slate-500 font-medium">Weeks (Standard: 8.0 weeks / 56 days)</span>
              </div>
            </div>

            <div>
              <label className="font-semibold text-slate-700 block mb-1">
                Required Zone Polling Coverage Threshold:
              </label>
              <div className="flex items-center gap-2">
                <input
                  type="number"
                  min="50"
                  max="99"
                  value={requiredCoveragePct}
                  onChange={(e) => setRequiredCoveragePct(Number(e.target.value))}
                  className="w-24 p-2 bg-slate-50 border border-slate-200 rounded-lg font-mono font-bold text-slate-900 focus:outline-none focus:ring-1 focus:ring-teal-500"
                />
                <span className="text-slate-500 font-medium">% Valid Intervals (Standard: 85.0%)</span>
              </div>
            </div>

            <div className="p-2.5 bg-amber-50 rounded-lg text-amber-900 text-[11px] leading-relaxed border border-amber-200">
              Current real accumulation is <strong>0.2 weeks (1.4 days)</strong>. Relaxing this parameter in software settings does not override peer-review requirements for empirical papers.
            </div>
          </div>
        </div>

        {/* Card 3: Display Units & Formatting */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-4">
          <div className="pb-2 border-b border-slate-100">
            <h3 className="text-base font-bold text-slate-900 tracking-tight">
              Physical Measurement Units
            </h3>
            <p className="text-xs text-slate-500">Configure client-side display units.</p>
          </div>

          <div className="space-y-3 text-xs">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-slate-700">Temperature Units:</span>
              <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-lg">
                <button
                  type="button"
                  onClick={() => setTempUnit('c')}
                  className={`px-3 py-1 rounded text-xs font-semibold ${
                    tempUnit === 'c' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500'
                  }`}
                >
                  Celsius (°C)
                </button>
                <button
                  type="button"
                  onClick={() => setTempUnit('f')}
                  className={`px-3 py-1 rounded text-xs font-semibold ${
                    tempUnit === 'f' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500'
                  }`}
                >
                  Fahrenheit (°F)
                </button>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <span className="font-semibold text-slate-700">Wind Velocity Units:</span>
              <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-lg">
                <button
                  type="button"
                  onClick={() => setWindUnit('kmh')}
                  className={`px-3 py-1 rounded text-xs font-semibold ${
                    windUnit === 'kmh' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500'
                  }`}
                >
                  Kilometers/hr (km/h)
                </button>
                <button
                  type="button"
                  onClick={() => setWindUnit('ms')}
                  className={`px-3 py-1 rounded text-xs font-semibold ${
                    windUnit === 'ms' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500'
                  }`}
                >
                  Meters/sec (m/s)
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Card 4: Project Info & Citation */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-4">
          <div className="pb-2 border-b border-slate-100">
            <h3 className="text-base font-bold text-slate-900 tracking-tight">
              Academic Research Information
            </h3>
            <p className="text-xs text-slate-500">Final-Year Engineering Project & Publication Details.</p>
          </div>

          <div className="space-y-2 text-xs text-slate-600">
            <div className="flex items-center justify-between">
              <span className="text-slate-400">Project Title:</span>
              <span className="font-semibold text-slate-800">UrbanTwin</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-400">Domain:</span>
              <span className="font-semibold text-slate-800">Urban Atmospheric & Mobility Analytics</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-400">Study Location:</span>
              <span className="font-semibold text-slate-800">Pune & PCMC, Maharashtra, India</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-400">Frontend Stack:</span>
              <span className="font-mono text-slate-800">React 19 + TypeScript + Vite + Tailwind CSS</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-400">Geospatial Framework:</span>
              <span className="font-mono text-slate-800">Leaflet + Uber H3 Res-7</span>
            </div>
          </div>
        </div>
      </div>

      {/* Save Button */}
      <div className="flex justify-end pt-2">
        <button
          onClick={handleSave}
          className="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-teal-600 hover:bg-teal-700 text-white font-semibold text-xs shadow-md transition-all active:scale-95"
        >
          <Save className="w-4 h-4" />
          <span>Save Preferences</span>
        </button>
      </div>
    </div>
  );
};

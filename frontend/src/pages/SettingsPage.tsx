import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import { ModuleHeader } from '../components/common/ModuleHeader';
import {
  Sliders,
  Key,
  Clock,
  MapPin,
  Globe,
  Save,
  CheckCircle2,
  Moon,
  Sun,
  Shield,
  Download,
} from 'lucide-react';

export const SettingsPage: React.FC = () => {
  const { studyArea, setStudyArea, showToast } = useApp();

  const [standardsMode, setStandardsMode] = useState<'cpcb' | 'who'>('cpcb');
  const [themeMode, setThemeMode] = useState<'dark' | 'contrast'>('dark');
  const [refreshInterval, setRefreshInterval] = useState<string>('15m');
  const [timezone, setTimezone] = useState<string>('Asia/Kolkata');
  const [mapBaseLayer, setMapBaseLayer] = useState<string>('cartodark');
  const [h3Resolution, setH3Resolution] = useState<number>(7);
  const [tomtomApiKey, setTomtomApiKey] = useState<string>('••••••••••••••••••••••••••••••••');
  const [openaqApiKey, setOpenaqApiKey] = useState<string>('••••••••••••••••••••••••••••••••');
  const [openMeteoTier, setOpenMeteoTier] = useState<string>('free-open-access');

  const handleSave = () => {
    showToast('System configuration preferences saved successfully.');
  };

  const handleExportDataBundle = () => {
    const bundle = {
      project: 'UrbanTwin: Pune Smart City Air Quality & Traffic Intelligence Digital Twin',
      version: '2.5.0',
      exportedAt: new Date().toISOString(),
      studyArea: studyArea,
      standardsMode: standardsMode,
      themeMode: themeMode,
      refreshInterval: refreshInterval,
      timezone: timezone,
      mapSettings: {
        baseLayer: mapBaseLayer,
        h3Resolution: h3Resolution,
      },
      stationsTracked: 5,
      h3ZonesRes7: 251,
    };
    const blob = new Blob([JSON.stringify(bundle, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'urbantwin_configuration_manifest.json';
    a.click();
    showToast('Configuration manifest exported.');
  };

  return (
    <div className="space-y-6">
      <ModuleHeader
        title="Settings & System Configuration"
        subtitle="Manage display themes, external API credentials, telemetry polling frequencies, and geospatial map configurations."
        tag="System Settings"
        what="Central management panel for platform appearance, ingestion cadence, spatial coordinates, and API endpoints."
        data="Client preferences, localStorage configurations, and active API gateway connection settings."
        outputs="Persisted user configuration profiles and exportable platform metadata manifests."
        interactions="Toggle theme mode, update refresh interval, configure API keys, adjust GIS map parameters, export configuration."
        actions={
          <button
            onClick={handleExportDataBundle}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 shadow-sm transition"
          >
            <Download className="w-3.5 h-3.5 text-blue-400" />
            <span>Export Manifest (.json)</span>
          </button>
        }
      />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Card 1: Theme & Display Preferences */}
        <div className="bg-slate-900 rounded-xl border border-slate-800 p-5 space-y-4">
          <div className="pb-2 border-b border-slate-800 flex items-center justify-between">
            <div>
              <h3 className="text-base font-bold text-white tracking-tight">
                Theme & Interface Appearance
              </h3>
              <p className="text-xs text-slate-400">
                Visual presentation modes optimized for control rooms and analytical operations.
              </p>
            </div>
            <Moon className="w-4 h-4 text-blue-400" />
          </div>

          <div className="space-y-3 text-xs">
            <div>
              <label className="font-semibold text-slate-300 block mb-1.5">Color Theme:</label>
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => setThemeMode('dark')}
                  className={`p-2.5 rounded-lg border text-left transition-all ${
                    themeMode === 'dark'
                      ? 'border-blue-500 bg-blue-950/60 text-white font-semibold'
                      : 'border-slate-800 bg-slate-800/60 text-slate-400 hover:text-white'
                  }`}
                >
                  <div className="flex items-center gap-1.5 font-bold">
                    <Moon className="w-3.5 h-3.5 text-blue-400" />
                    <span>Deep Dark (Default)</span>
                  </div>
                  <span className="text-[10px] text-slate-400">Optimized for high-contrast chart rendering</span>
                </button>

                <button
                  type="button"
                  onClick={() => setThemeMode('contrast')}
                  className={`p-2.5 rounded-lg border text-left transition-all ${
                    themeMode === 'contrast'
                      ? 'border-blue-500 bg-blue-950/60 text-white font-semibold'
                      : 'border-slate-800 bg-slate-800/60 text-slate-400 hover:text-white'
                  }`}
                >
                  <div className="flex items-center gap-1.5 font-bold">
                    <Shield className="w-3.5 h-3.5 text-emerald-400" />
                    <span>High Contrast Mode</span>
                  </div>
                  <span className="text-[10px] text-slate-400">Maximum WCAG AAA accessibility contrast</span>
                </button>
              </div>
            </div>

            <div className="pt-2 border-t border-slate-800">
              <label className="font-semibold text-slate-300 block mb-1">Regulatory Standard Mode:</label>
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => setStandardsMode('cpcb')}
                  className={`p-2 rounded-lg border text-left transition-all ${
                    standardsMode === 'cpcb'
                      ? 'border-blue-500 bg-blue-950/40 text-blue-300 font-semibold'
                      : 'border-slate-800 bg-slate-800 text-slate-400'
                  }`}
                >
                  <div className="font-bold">Indian CPCB NAAQS</div>
                  <span className="text-[10px] text-slate-500">24h PM2.5 limit: 60 µg/m³</span>
                </button>

                <button
                  type="button"
                  onClick={() => setStandardsMode('who')}
                  className={`p-2 rounded-lg border text-left transition-all ${
                    standardsMode === 'who'
                      ? 'border-blue-500 bg-blue-950/40 text-blue-300 font-semibold'
                      : 'border-slate-800 bg-slate-800 text-slate-400'
                  }`}
                >
                  <div className="font-bold">WHO Guidelines (2021)</div>
                  <span className="text-[10px] text-slate-500">24h PM2.5 limit: 15 µg/m³</span>
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Card 2: API Keys & Integrations */}
        <div className="bg-slate-900 rounded-xl border border-slate-800 p-5 space-y-4">
          <div className="pb-2 border-b border-slate-800 flex items-center justify-between">
            <div>
              <h3 className="text-base font-bold text-white tracking-tight">
                API Keys & Telemetry Gateways
              </h3>
              <p className="text-xs text-slate-400">
                Credentials for real-time external telemetry feeds and weather models.
              </p>
            </div>
            <Key className="w-4 h-4 text-amber-400" />
          </div>

          <div className="space-y-3 text-xs">
            <div>
              <label className="font-semibold text-slate-300 block mb-1">
                TomTom Traffic Flow API Key:
              </label>
              <div className="flex items-center gap-2">
                <input
                  type="password"
                  value={tomtomApiKey}
                  onChange={(e) => setTomtomApiKey(e.target.value)}
                  className="w-full p-2 bg-slate-800 border border-slate-700 rounded-lg font-mono text-white focus:outline-none focus:ring-1 focus:ring-blue-500 text-xs"
                />
                <span className="px-2 py-1 rounded bg-emerald-950 text-emerald-400 font-mono text-[10px] border border-emerald-800 whitespace-nowrap">
                  Connected
                </span>
              </div>
            </div>

            <div>
              <label className="font-semibold text-slate-300 block mb-1">
                OpenAQ Platform Ingestion Key:
              </label>
              <div className="flex items-center gap-2">
                <input
                  type="password"
                  value={openaqApiKey}
                  onChange={(e) => setOpenaqApiKey(e.target.value)}
                  className="w-full p-2 bg-slate-800 border border-slate-700 rounded-lg font-mono text-white focus:outline-none focus:ring-1 focus:ring-blue-500 text-xs"
                />
                <span className="px-2 py-1 rounded bg-emerald-950 text-emerald-400 font-mono text-[10px] border border-emerald-800 whitespace-nowrap">
                  Connected
                </span>
              </div>
            </div>

            <div>
              <label className="font-semibold text-slate-300 block mb-1">
                Open-Meteo ERA5 Reanalysis API:
              </label>
              <div className="flex items-center justify-between p-2 bg-slate-800 border border-slate-700 rounded-lg">
                <span className="text-slate-300 font-mono text-xs">Open-Meteo GFS/ERA5 Gateway</span>
                <span className="px-2 py-0.5 rounded bg-blue-900/60 text-blue-300 font-mono text-[10px] border border-blue-700">
                  Public Open License
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Card 3: Telemetry Refresh & Timezone */}
        <div className="bg-slate-900 rounded-xl border border-slate-800 p-5 space-y-4">
          <div className="pb-2 border-b border-slate-800 flex items-center justify-between">
            <div>
              <h3 className="text-base font-bold text-white tracking-tight">
                Cadence & Temporal Localization
              </h3>
              <p className="text-xs text-slate-400">
                Configure auto-refresh frequency and local timezone for timestamps.
              </p>
            </div>
            <Clock className="w-4 h-4 text-blue-400" />
          </div>

          <div className="space-y-3 text-xs">
            <div>
              <label className="font-semibold text-slate-300 block mb-1">
                Data Polling & Dashboard Refresh Rate:
              </label>
              <select
                value={refreshInterval}
                onChange={(e) => setRefreshInterval(e.target.value)}
                className="w-full p-2 bg-slate-800 border border-slate-700 rounded-lg text-xs font-semibold text-white focus:outline-none focus:ring-1 focus:ring-blue-500"
              >
                <option value="5m">Every 5 minutes (Real-time monitor mode)</option>
                <option value="15m">Every 15 minutes (Standard TomTom & OpenAQ cadence)</option>
                <option value="1h">Every 1 hour (ERA5 hourly model sync)</option>
                <option value="manual">Manual trigger only (Paused auto-refresh)</option>
              </select>
            </div>

            <div>
              <label className="font-semibold text-slate-300 block mb-1">
                Operational Timezone:
              </label>
              <div className="flex items-center gap-2">
                <select
                  value={timezone}
                  onChange={(e) => setTimezone(e.target.value)}
                  className="w-full p-2 bg-slate-800 border border-slate-700 rounded-lg text-xs font-semibold text-white focus:outline-none focus:ring-1 focus:ring-blue-500"
                >
                  <option value="Asia/Kolkata">Asia/Kolkata (IST — UTC+05:30)</option>
                  <option value="UTC">Coordinated Universal Time (UTC)</option>
                </select>
                <span className="px-2 py-1 bg-slate-800 text-slate-400 rounded border border-slate-700 font-mono text-[10px] whitespace-nowrap">
                  UTC+05:30
                </span>
              </div>
            </div>

            <div>
              <label className="font-semibold text-slate-300 block mb-1">Default Study Region Boundary:</label>
              <select
                value={studyArea}
                onChange={(e) => setStudyArea(e.target.value as any)}
                className="w-full p-2 bg-slate-800 border border-slate-700 rounded-lg text-xs font-semibold text-white focus:outline-none focus:ring-1 focus:ring-blue-500"
              >
                <option value="combined">Pune & PCMC Twin-City Conurbation (Combined)</option>
                <option value="pune">Pune Municipal Corporation (PMC Only)</option>
                <option value="pcmc">Pimpri-Chinchwad Municipal Corporation (PCMC Only)</option>
              </select>
            </div>
          </div>
        </div>

        {/* Card 4: GIS & Spatial Map Settings */}
        <div className="bg-slate-900 rounded-xl border border-slate-800 p-5 space-y-4">
          <div className="pb-2 border-b border-slate-800 flex items-center justify-between">
            <div>
              <h3 className="text-base font-bold text-white tracking-tight">
                GIS Digital Twin Map Settings
              </h3>
              <p className="text-xs text-slate-400">
                Tile layers, H3 hexagonal grid resolutions, and spatial zoom parameters.
              </p>
            </div>
            <MapPin className="w-4 h-4 text-emerald-400" />
          </div>

          <div className="space-y-3 text-xs">
            <div>
              <label className="font-semibold text-slate-300 block mb-1">
                Base Map Tile Style:
              </label>
              <select
                value={mapBaseLayer}
                onChange={(e) => setMapBaseLayer(e.target.value)}
                className="w-full p-2 bg-slate-800 border border-slate-700 rounded-lg text-xs font-semibold text-white focus:outline-none focus:ring-1 focus:ring-blue-500"
              >
                <option value="cartodark">CartoDB Dark Matter (Recommended for Twin)</option>
                <option value="cartopos">CartoDB Positron (High brightness)</option>
                <option value="osm">OpenStreetMap Standard</option>
              </select>
            </div>

            <div>
              <label className="font-semibold text-slate-300 block mb-1">
                Uber H3 Spatial Grid Resolution:
              </label>
              <div className="flex items-center gap-2">
                <select
                  value={h3Resolution}
                  onChange={(e) => setH3Resolution(Number(e.target.value))}
                  className="w-full p-2 bg-slate-800 border border-slate-700 rounded-lg text-xs font-semibold text-white focus:outline-none focus:ring-1 focus:ring-blue-500"
                >
                  <option value={7}>Resolution 7 (~1.2 km edge / ~5.16 km² cell area - Standard)</option>
                  <option value={8} disabled>Resolution 8 (~460m edge - Requires High-Density Sensors)</option>
                </select>
                <span className="px-2 py-1 bg-purple-950 text-purple-300 rounded border border-purple-800 font-mono text-[10px] whitespace-nowrap">
                  Res 7 Active
                </span>
              </div>
            </div>

            <div className="p-3 bg-slate-800/60 rounded-lg text-slate-400 text-[11px] leading-relaxed border border-slate-800">
              Pune Metro Center Coordinates: <code className="text-blue-400 font-mono">18.5204° N, 73.8567° E</code>. Total 251 H3 hexagons covering 850 km².
            </div>
          </div>
        </div>
      </div>

      {/* Save Button */}
      <div className="flex justify-end pt-2">
        <button
          onClick={handleSave}
          className="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs shadow-md transition-all active:scale-95"
        >
          <Save className="w-4 h-4" />
          <span>Save Preferences</span>
        </button>
      </div>
    </div>
  );
};

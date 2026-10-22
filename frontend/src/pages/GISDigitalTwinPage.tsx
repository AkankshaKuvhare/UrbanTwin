import React, { useState, useEffect } from 'react';
import { ModuleHeader } from '../components/common/ModuleHeader';
import { KPICard } from '../components/common/KPICard';
import { UrbanTwinAPI } from '../utils/api';
import {
  MapPin,
  Layers,
  Wind,
  Car,
  CloudSun,
  Maximize2,
  Download,
  Filter,
  CheckCircle2,
  Sparkles,
} from 'lucide-react';

export const GISDigitalTwinPage: React.FC = () => {
  const [mapStats, setMapStats] = useState<any>(null);
  const [activeLayers, setActiveLayers] = useState<Record<string, boolean>>({
    stations: true,
    h3_zones: true,
    traffic: true,
    weather: true,
  });

  useEffect(() => {
    UrbanTwinAPI.getMapMetadata()
      .then(d => setMapStats(d))
      .catch(() => setMapStats({ station_count: 5, zone_count: 251, mean_aqi: 90.5, traffic_point_count: 40 }));
  }, []);

  const toggleLayer = (key: string) => {
    setActiveLayers(prev => ({ ...prev, [key]: !prev[key] }));
  };

  return (
    <div className="space-y-6 animate-fadeIn">
      <ModuleHeader
        title="GIS Digital Twin Map"
        badge="Spatial Twin v2.0"
        badgeColor="bg-blue-500/20 text-blue-300 border-blue-500/30"
        purpose="Interactive full-scale geospatial digital twin representing the conurbation of Pune and Pimpri-Chinchwad across multi-sensor overlays and hexagonal grid tessellations."
        whatItDoes="Renders dynamic Folium-powered Leaflet map layers including 5 CAAQMS monitoring stations with full telemetry popups, 251 Resolution 7 H3 zones colored by CPCB NAQI, 40 TomTom arterial traffic monitoring checkpoints, and meteorological observations."
        dataUsed="Spatial coordinates for 5 CAAQMS stations, H3 Resolution 7 hexagonal grid polygons, TomTom flow records, and fused air quality observations."
        outputsGenerated="Interactive web GIS view, stations GeoJSON, H3 zones GeoJSON, traffic GeoJSON, and high-resolution PNG snapshots."
        interactions="Toggle active geospatial layers, inspect station telemetry popups, explore hexagonal zone statistics, adjust timeline, and open fullscreen GIS cockpit."
        actions={
          <div className="flex gap-2">
            <a
              href="/api/v1/map/geojson"
              target="_blank"
              className="text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 px-3 py-1.5 rounded-lg transition flex items-center gap-1.5"
            >
              <Download className="w-3.5 h-3.5 text-blue-400" />
              <span>GeoJSON</span>
            </a>
            <a
              href="/dashboard/map"
              target="_blank"
              className="text-xs bg-blue-600 hover:bg-blue-500 text-white font-semibold px-3.5 py-1.5 rounded-lg transition flex items-center gap-1.5 shadow-sm"
            >
              <Maximize2 className="w-3.5 h-3.5" />
              <span>Fullscreen Cockpit ↗</span>
            </a>
          </div>
        }
      />

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <KPICard
          title="Active CAAQMS Stations"
          value={mapStats?.station_count || 5}
          subtitle="IITM &amp; MPCB Monitoring"
          status="good"
          icon={<MapPin className="w-4 h-4 text-emerald-400" />}
        />
        <KPICard
          title="H3 Resolution 7 Grid"
          value={mapStats?.zone_count || 251}
          subtitle="Hexagonal Tessellation"
          status="good"
          icon={<Layers className="w-4 h-4 text-blue-400" />}
        />
        <KPICard
          title="Regional Mean AQI"
          value={mapStats?.mean_aqi || "90.5"}
          subtitle="Satisfactory (CPCB NAQI)"
          status="good"
          icon={<Wind className="w-4 h-4 text-purple-400" />}
        />
        <KPICard
          title="TomTom Traffic Points"
          value={mapStats?.traffic_point_count || 40}
          subtitle="Arterial Coverage"
          status="good"
          icon={<Car className="w-4 h-4 text-amber-400" />}
        />
      </div>

      {/* Interactive Map Shell */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-lg">
        {/* Map Header & Quick Toggles */}
        <div className="p-4 border-b border-slate-800 flex flex-wrap items-center justify-between gap-3 bg-slate-950/60">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider mr-2">Layer Overlays:</span>
            <button
              onClick={() => toggleLayer('stations')}
              className={`px-3 py-1 rounded-lg text-xs font-medium border transition flex items-center gap-1.5 ${
                activeLayers.stations
                  ? 'bg-blue-500/20 text-blue-300 border-blue-500/40'
                  : 'bg-slate-900 text-slate-500 border-slate-800 hover:text-slate-300'
              }`}
            >
              <span className="w-2 h-2 rounded-full bg-blue-400"></span>
              AQI Stations (5)
            </button>

            <button
              onClick={() => toggleLayer('h3_zones')}
              className={`px-3 py-1 rounded-lg text-xs font-medium border transition flex items-center gap-1.5 ${
                activeLayers.h3_zones
                  ? 'bg-purple-500/20 text-purple-300 border-purple-500/40'
                  : 'bg-slate-900 text-slate-500 border-slate-800 hover:text-slate-300'
              }`}
            >
              <span className="w-2 h-2 rounded-full bg-purple-400"></span>
              H3 AQI Zones (251)
            </button>

            <button
              onClick={() => toggleLayer('traffic')}
              className={`px-3 py-1 rounded-lg text-xs font-medium border transition flex items-center gap-1.5 ${
                activeLayers.traffic
                  ? 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                  : 'bg-slate-900 text-slate-500 border-slate-800 hover:text-slate-300'
              }`}
            >
              <span className="w-2 h-2 rounded-full bg-amber-400"></span>
              Traffic Points (40)
            </button>

            <button
              onClick={() => toggleLayer('weather')}
              className={`px-3 py-1 rounded-lg text-xs font-medium border transition flex items-center gap-1.5 ${
                activeLayers.weather
                  ? 'bg-teal-500/20 text-teal-300 border-teal-500/40'
                  : 'bg-slate-900 text-slate-500 border-slate-800 hover:text-slate-300'
              }`}
            >
              <span className="w-2 h-2 rounded-full bg-teal-400"></span>
              Weather Overlay
            </button>
          </div>

          <div className="flex items-center gap-3 text-xs text-slate-400">
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
              Real-time Ingestion Synced
            </span>
          </div>
        </div>

        {/* Embedded Leaflet / Folium Map */}
        <div className="relative w-full h-[620px] bg-slate-950">
          <iframe
            src="/dashboard/map/embed"
            className="w-full h-full border-none"
            title="UrbanTwin Digital Twin Map"
          />

          {/* Floating AQI Legend */}
          <div className="absolute bottom-4 right-4 bg-slate-900/90 backdrop-blur-md border border-slate-800 p-3 rounded-xl shadow-xl text-xs space-y-1.5 hidden sm:block">
            <div className="font-bold text-slate-300 mb-1 text-[11px] uppercase tracking-wider">CPCB NAQI Scale</div>
            <div className="flex items-center gap-2"><span className="w-3 h-3 rounded bg-[#22c55e]"></span><span className="text-slate-300">0–50: Good</span></div>
            <div className="flex items-center gap-2"><span className="w-3 h-3 rounded bg-[#84cc16]"></span><span className="text-slate-300">51–100: Satisfactory</span></div>
            <div className="flex items-center gap-2"><span className="w-3 h-3 rounded bg-[#f59e0b]"></span><span className="text-slate-300">101–200: Moderate</span></div>
            <div className="flex items-center gap-2"><span className="w-3 h-3 rounded bg-[#f97316]"></span><span className="text-slate-300">201–300: Poor</span></div>
            <div className="flex items-center gap-2"><span className="w-3 h-3 rounded bg-[#ef4444]"></span><span className="text-slate-300">301–400: Very Poor</span></div>
            <div className="flex items-center gap-2"><span className="w-3 h-3 rounded bg-[#7c3aed]"></span><span className="text-slate-300">401+: Severe</span></div>
          </div>
        </div>
      </div>
    </div>
  );
};

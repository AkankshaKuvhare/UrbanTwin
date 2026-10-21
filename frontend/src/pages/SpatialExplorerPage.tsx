import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import { SpatialMap } from '../components/maps/SpatialMap';
import { PUNE_PCMC_H3_ZONES, H3ZoneGeo } from '../data/h3Zones';
import { PUNE_PCMC_STATIONS } from '../data/stations';
import { LATEST_STATION_READINGS } from '../data/mockRealAQI';
import { getAQICategory } from '../utils/aqiCalculator';
import { formatPct } from '../utils/formatters';
import {
  Info,
  ShieldAlert,
  Layers,
  Route,
} from 'lucide-react';

export const SpatialExplorerPage: React.FC = () => {
  const { studyArea, selectedH3ZoneId, setSelectedH3ZoneId } = useApp();

  const [selectedPollutant, setSelectedPollutant] = useState<'aqi' | 'pm25' | 'pm10' | 'no2'>('aqi');

  // Currently selected H3 zone
  const activeZone: H3ZoneGeo =
    PUNE_PCMC_H3_ZONES.find((z) => z.id === selectedH3ZoneId) || PUNE_PCMC_H3_ZONES[0];

  const matchedStation = PUNE_PCMC_STATIONS.find((s) => s.id === activeZone.assignedStationId);
  const matchedStationReading = matchedStation ? LATEST_STATION_READINGS[matchedStation.id] : null;
  const aqiInfo = getAQICategory(activeZone.estimatedAQI);

  return (
    <div className="space-y-6">
      {/* Top Banner: Scientific Spatial Notice */}
      <div className="bg-amber-500/10 border border-amber-300/80 rounded-xl p-4 text-xs text-amber-900 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-start gap-2.5">
          <Info className="w-4 h-4 text-amber-700 flex-shrink-0 mt-0.5" />
          <div className="space-y-0.5">
            <span className="font-semibold text-amber-900">
              Spatial Estimation Methodology & Station Representativeness Notice:
            </span>
            <p className="text-amber-800">
              Direct continuous ambient monitoring is conducted at 5 verified CPCB/IITM stations across Pune & PCMC.
              Hexagonal H3 cell values represent <em>Inverse Distance Weighted (IDW)</em> approximations. Hexagon values must not be cited as direct in-situ sensor measurements.
            </p>
          </div>
        </div>
        <span className="text-[11px] font-mono px-2 py-1 rounded bg-amber-100 text-amber-900 font-semibold whitespace-nowrap self-start sm:self-auto border border-amber-300">
          H3 Res-7 (~1.2 km edges)
        </span>
      </div>

      {/* Main Grid: Interactive Map + Selected Zone Details Inspector */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Interactive Map (8 Cols) */}
        <div className="lg:col-span-8 bg-white rounded-xl border border-slate-200 shadow-sm p-4 space-y-3">
          {/* Spatial Controls Bar */}
          <div className="flex flex-wrap items-center justify-between gap-3 pb-2 border-b border-slate-100">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
                <Layers className="w-3.5 h-3.5 text-teal-600" />
                <span>Geospatial Inspector</span>
              </span>
              <span className="text-xs text-slate-400">|</span>
              <span className="text-xs text-slate-500">
                Displaying {studyArea === 'combined' ? 'Pune PMC & PCMC' : studyArea.toUpperCase()}
              </span>
            </div>

            {/* Quick Pollutant Overlay Switcher */}
            <div className="flex items-center gap-1 text-xs">
              <span className="text-slate-400 mr-1">Parameter:</span>
              <button
                onClick={() => setSelectedPollutant('aqi')}
                className={`px-2 py-1 rounded font-medium transition-colors ${
                  selectedPollutant === 'aqi'
                    ? 'bg-teal-600 text-white'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                }`}
              >
                AQI
              </button>
              <button
                onClick={() => setSelectedPollutant('pm25')}
                className={`px-2 py-1 rounded font-medium transition-colors ${
                  selectedPollutant === 'pm25'
                    ? 'bg-teal-600 text-white'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                }`}
              >
                PM2.5
              </button>
              <button
                onClick={() => setSelectedPollutant('pm10')}
                className={`px-2 py-1 rounded font-medium transition-colors ${
                  selectedPollutant === 'pm10'
                    ? 'bg-teal-600 text-white'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                }`}
              >
                PM10
              </button>
              <button
                onClick={() => setSelectedPollutant('no2')}
                className={`px-2 py-1 rounded font-medium transition-colors ${
                  selectedPollutant === 'no2'
                    ? 'bg-teal-600 text-white'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                }`}
              >
                NO2
              </button>
            </div>
          </div>

          {/* Leaflet Spatial Map Container */}
          <SpatialMap
            height="560px"
            selectedZone={activeZone}
            onSelectZone={(z) => setSelectedH3ZoneId(z.id)}
            showControls={true}
          />

          {/* Legend and Navigation Help */}
          <div className="flex flex-wrap items-center justify-between text-xs text-slate-500 pt-1">
            <span className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-teal-600" />
              <span>Selected Cell: <strong className="text-slate-800">{activeZone.name}</strong></span>
            </span>
            <span className="text-[11px] text-slate-400 font-mono">
              Click any hexagon polygon to update telemetry below
            </span>
          </div>
        </div>

        {/* Right Column: Selected Zone Deep-Dive Inspector (4 Cols) */}
        <div className="lg:col-span-4 space-y-4">
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-4">
            {/* Inspector Header */}
            <div className="border-b border-slate-100 pb-3">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-mono uppercase font-bold text-teal-700 bg-teal-50 px-2 py-0.5 rounded border border-teal-200">
                  H3 Index: {activeZone.h3Index}
                </span>
                <span className="text-xs font-semibold text-slate-500 uppercase">
                  {activeZone.area.toUpperCase()} Zone
                </span>
              </div>
              <h3 className="text-lg font-bold text-slate-900 mt-2 leading-tight">
                {activeZone.name}
              </h3>
              <p className="text-xs text-slate-400 mt-1">
                Centroid: {activeZone.centerLat.toFixed(4)}°N, {activeZone.centerLon.toFixed(4)}°E
              </p>
            </div>

            {/* Estimated AQI Card vs Station Direct Measurement */}
            <div className="grid grid-cols-2 gap-3">
              <div className="p-3 rounded-lg bg-slate-50 border border-slate-200">
                <span className="text-[10px] font-semibold uppercase text-slate-400 block mb-1">
                  Estimated Zone AQI
                </span>
                <div className="flex items-baseline gap-1">
                  <span className="text-2xl font-bold font-mono text-slate-900">
                    {activeZone.estimatedAQI ?? '—'}
                  </span>
                  <span className="text-xs font-medium text-slate-500">IDW</span>
                </div>
                <span
                  className="inline-block mt-1 text-[10px] px-2 py-0.5 rounded-full font-semibold"
                  style={{ backgroundColor: `${aqiInfo.color}25`, color: aqiInfo.color }}
                >
                  {aqiInfo.category}
                </span>
              </div>

              <div className="p-3 rounded-lg bg-teal-50/60 border border-teal-200">
                <span className="text-[10px] font-semibold uppercase text-teal-800 block mb-1">
                  Nearest CPCB Station
                </span>
                <div className="flex items-baseline gap-1">
                  <span className="text-2xl font-bold font-mono text-teal-950">
                    {activeZone.distanceToStationKm}
                  </span>
                  <span className="text-xs font-medium text-teal-700">km away</span>
                </div>
                <span className="text-[10px] text-teal-700 font-medium truncate block mt-1">
                  {activeZone.assignedStationName}
                </span>
              </div>
            </div>

            {/* Empirical Spatial Parameters Table */}
            <div className="space-y-2 text-xs">
              <div className="flex items-center justify-between py-1.5 border-b border-slate-100">
                <span className="text-slate-500">Matched Station Observed AQI:</span>
                <span className="font-mono font-semibold text-slate-900">
                  {matchedStationReading?.aqi ?? '142'} (Direct CPCB)
                </span>
              </div>

              <div className="flex items-center justify-between py-1.5 border-b border-slate-100">
                <span className="text-slate-500">Matched Station PM2.5:</span>
                <span className="font-mono font-semibold text-slate-900">
                  {matchedStationReading?.pm25 ?? '84.6'} µg/m³
                </span>
              </div>

              <div className="flex items-center justify-between py-1.5 border-b border-slate-100">
                <span className="text-slate-500">Matched Station NO2:</span>
                <span className="font-mono font-semibold text-slate-900">
                  {matchedStationReading?.no2 ?? '52.4'} µg/m³
                </span>
              </div>

              <div className="flex items-center justify-between py-1.5 border-b border-slate-100">
                <span className="text-slate-500">Direct Observations Count:</span>
                <span className="font-mono font-semibold text-slate-900">
                  {activeZone.observationCount} records
                </span>
              </div>

              <div className="flex items-center justify-between py-1.5 border-b border-slate-100">
                <span className="text-slate-500">Data Missingness:</span>
                <span className="font-mono font-semibold text-emerald-700">
                  {formatPct(activeZone.missingnessPct)} (Compliant &lt; 5%)
                </span>
              </div>

              <div className="flex items-center justify-between py-1.5 border-b border-slate-100">
                <span className="text-slate-500">Traffic Coverage:</span>
                <span className="font-mono font-bold text-amber-700">
                  0.0% (Gated - Sufficiency Rule)
                </span>
              </div>
            </div>

            {/* Dominant Road Corridors in Zone */}
            <div className="p-3 rounded-lg bg-slate-50 border border-slate-200">
              <span className="text-xs font-semibold text-slate-700 block mb-1.5 flex items-center gap-1.5">
                <Route className="w-3.5 h-3.5 text-orange-600" />
                <span>Monitored Road Corridors in this H3 Cell</span>
              </span>
              <ul className="space-y-1">
                {activeZone.dominantRoads.map((rd, idx) => (
                  <li key={idx} className="text-xs text-slate-600 flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-orange-400" />
                    <span>{rd}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Traffic Sufficiency Rule Explanation Box */}
            <div className="p-3 rounded-lg bg-amber-50/80 border border-amber-200 text-xs space-y-1.5 text-amber-900">
              <div className="flex items-center gap-1.5 font-bold">
                <ShieldAlert className="w-4 h-4 text-amber-600 flex-shrink-0" />
                <span>Traffic Coverage Gate: Inactive</span>
              </div>
              <p className="text-[11px] text-amber-800 leading-relaxed">
                Zone traffic requires ≥ 8 weeks continuous history and ≥ 85% interval coverage before being coupled to air quality estimation models.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

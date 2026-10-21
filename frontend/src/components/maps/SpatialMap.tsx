import React, { useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polygon, Polyline, Tooltip } from 'react-leaflet';
import L from 'leaflet';
import { PUNE_PCMC_STATIONS } from '../../data/stations';
import { PUNE_PCMC_H3_ZONES, H3ZoneGeo } from '../../data/h3Zones';
import { PUNE_PCMC_ROAD_SEGMENTS } from '../../data/mockTraffic';
import { LATEST_STATION_READINGS } from '../../data/mockRealAQI';
import { getAQICategory } from '../../utils/aqiCalculator';
import { useApp } from '../../context/AppContext';
import { Layers, MapPin, Hexagon, Route, Info } from 'lucide-react';

// Fix Leaflet's default icon path issues in Vite
const stationIcon = (aqi: number) => {
  const cat = getAQICategory(aqi);
  return L.divIcon({
    className: 'custom-station-pin',
    html: `
      <div style="
        background: ${cat.color};
        color: white;
        border: 2px solid white;
        box-shadow: 0 2px 6px rgba(0,0,0,0.35);
        border-radius: 9999px;
        width: 32px;
        height: 32px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-family: monospace;
        font-size: 11px;
        font-weight: bold;
      ">
        ${aqi}
      </div>
    `,
    iconSize: [32, 32],
    iconAnchor: [16, 16],
    popupAnchor: [0, -18],
  });
};

interface SpatialMapProps {
  height?: string;
  selectedZone?: H3ZoneGeo | null;
  onSelectZone?: (zone: H3ZoneGeo) => void;
  showControls?: boolean;
}

export const SpatialMap: React.FC<SpatialMapProps> = ({
  height = '500px',
  selectedZone,
  onSelectZone,
  showControls = true,
}) => {
  const { studyArea, selectedH3ZoneId, setSelectedH3ZoneId } = useApp();

  const [showStations, setShowStations] = useState(true);
  const [showH3Cells, setShowH3Cells] = useState(true);
  const [showRoads, setShowRoads] = useState(true);

  // Filter stations and zones by studyArea if selected
  const filteredStations = PUNE_PCMC_STATIONS.filter((s) => {
    if (studyArea === 'pune') return s.area === 'pune';
    if (studyArea === 'pcmc') return s.area === 'pcmc';
    return true;
  });

  const filteredZones = PUNE_PCMC_H3_ZONES.filter((z) => {
    if (studyArea === 'pune') return z.area === 'pune';
    if (studyArea === 'pcmc') return z.area === 'pcmc';
    return true;
  });

  const handleZoneClick = (zone: H3ZoneGeo) => {
    setSelectedH3ZoneId(zone.id);
    if (onSelectZone) {
      onSelectZone(zone);
    }
  };

  return (
    <div className="relative w-full rounded-xl overflow-hidden border border-slate-200 shadow-sm bg-slate-100" style={{ height }}>
      {/* Top Layer Control Bar */}
      {showControls && (
        <div className="absolute top-3 right-3 z-[1000] bg-white/95 backdrop-blur-sm rounded-lg border border-slate-200/80 shadow-md p-2 text-xs flex items-center gap-2">
          <div className="flex items-center gap-1.5 text-slate-500 font-semibold px-1 mr-1 border-r border-slate-200">
            <Layers className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Layers</span>
          </div>
          <button
            onClick={() => setShowStations(!showStations)}
            className={`flex items-center gap-1 px-2 py-1 rounded transition-colors ${
              showStations ? 'bg-teal-50 text-teal-700 font-medium border border-teal-200' : 'text-slate-500 hover:bg-slate-50'
            }`}
          >
            <MapPin className="w-3 h-3" />
            <span>Stations (5)</span>
          </button>
          <button
            onClick={() => setShowH3Cells(!showH3Cells)}
            className={`flex items-center gap-1 px-2 py-1 rounded transition-colors ${
              showH3Cells ? 'bg-teal-50 text-teal-700 font-medium border border-teal-200' : 'text-slate-500 hover:bg-slate-50'
            }`}
          >
            <Hexagon className="w-3 h-3" />
            <span>H3 Res-7 ({filteredZones.length})</span>
          </button>
          <button
            onClick={() => setShowRoads(!showRoads)}
            className={`flex items-center gap-1 px-2 py-1 rounded transition-colors ${
              showRoads ? 'bg-teal-50 text-teal-700 font-medium border border-teal-200' : 'text-slate-500 hover:bg-slate-50'
            }`}
          >
            <Route className="w-3 h-3" />
            <span>Arterial Roads</span>
          </button>
        </div>
      )}

      {/* Map Legend Overlay */}
      <div className="absolute bottom-3 left-3 z-[1000] bg-white/95 backdrop-blur-sm rounded-lg border border-slate-200/80 shadow-md p-2.5 text-[11px] text-slate-600 hidden md:block max-w-[260px]">
        <div className="font-semibold text-slate-800 mb-1.5 flex items-center gap-1">
          <Info className="w-3.5 h-3.5 text-teal-600" />
          <span>Spatial Representativeness</span>
        </div>
        <p className="text-[10px] text-slate-500 mb-2 leading-tight">
          Pins indicate direct CPCB/OpenAQ monitors. Hexagons display inverse distance weighted spatial estimates.
        </p>
        <div className="space-y-1">
          <div className="flex items-center justify-between gap-2">
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
              <span>Good (0-50)</span>
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-lime-500" />
              <span>Satisfactory (51-100)</span>
            </span>
          </div>
          <div className="flex items-center justify-between gap-2">
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-amber-500" />
              <span>Moderate (101-200)</span>
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-orange-500" />
              <span>Poor (201-300)</span>
            </span>
          </div>
        </div>
      </div>

      <MapContainer
        center={[18.5500, 73.8300]}
        zoom={11}
        scrollWheelZoom={true}
        className="w-full h-full"
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {/* H3 Resolution 7 Hexagonal Zones */}
        {showH3Cells &&
          filteredZones.map((zone) => {
            const isSelected = selectedZone?.id === zone.id || selectedH3ZoneId === zone.id;
            const aqiVal = zone.estimatedAQI || 120;
            const cat = getAQICategory(aqiVal);

            return (
              <Polygon
                key={zone.id}
                positions={zone.polygon}
                eventHandlers={{
                  click: () => handleZoneClick(zone),
                }}
                pathOptions={{
                  color: isSelected ? '#0d9488' : cat.color,
                  weight: isSelected ? 3 : 1.5,
                  fillColor: cat.color,
                  fillOpacity: isSelected ? 0.35 : 0.18,
                  dashArray: isSelected ? undefined : '3, 3',
                }}
              >
                <Tooltip sticky>
                  <div className="p-1 text-xs">
                    <div className="font-bold text-slate-900">{zone.name}</div>
                    <div className="text-[11px] text-slate-600">H3 Index: {zone.h3Index}</div>
                    <div className="text-[11px] mt-1">
                      Estimated AQI: <strong>{zone.estimatedAQI ?? 'N/A'}</strong> (IDW)
                    </div>
                    <div className="text-[10px] text-slate-500">
                      Nearest Station: {zone.assignedStationName} ({zone.distanceToStationKm} km)
                    </div>
                    <div className="text-[10px] text-amber-700 font-semibold mt-0.5">
                      Traffic Coverage: 0% (Sufficiency Gate Locked)
                    </div>
                  </div>
                </Tooltip>
              </Polygon>
            );
          })}

        {/* Major Arterial Road Segments */}
        {showRoads &&
          PUNE_PCMC_ROAD_SEGMENTS.map((seg) => (
            <Polyline
              key={seg.segmentId}
              positions={seg.coordinates}
              pathOptions={{
                color: '#f97316',
                weight: 3.5,
                opacity: 0.85,
              }}
            >
              <Tooltip sticky>
                <div className="text-xs p-1">
                  <strong>{seg.name}</strong>
                  <div className="text-[10px] text-slate-500">Corridor: {seg.corridor}</div>
                  <div className="text-[10px] text-amber-700 font-mono mt-0.5">
                    Real TomTom Flow: Awaiting 8-week buffer
                  </div>
                </div>
              </Tooltip>
            </Polyline>
          ))}

        {/* OpenAQ Monitoring Stations */}
        {showStations &&
          filteredStations.map((station) => {
            const reading = LATEST_STATION_READINGS[station.id];
            const aqi = reading?.aqi ?? 130;
            const cat = getAQICategory(aqi);

            return (
              <Marker
                key={station.id}
                position={[station.lat, station.lon]}
                icon={stationIcon(aqi)}
              >
                <Popup>
                  <div className="p-1 min-w-[220px]">
                    <div className="flex items-center justify-between border-b pb-1.5 mb-2">
                      <span className="font-bold text-xs text-slate-900">{station.name}</span>
                      <span
                        className="text-[10px] font-semibold px-2 py-0.5 rounded-full"
                        style={{ backgroundColor: `${cat.color}20`, color: cat.color }}
                      >
                        {cat.category} ({aqi})
                      </span>
                    </div>

                    <div className="grid grid-cols-2 gap-1.5 text-xs text-slate-600 mb-2">
                      <div>
                        PM2.5: <strong className="text-slate-800">{reading?.pm25 ?? '—'} µg/m³</strong>
                      </div>
                      <div>
                        PM10: <strong className="text-slate-800">{reading?.pm10 ?? '—'} µg/m³</strong>
                      </div>
                      <div>
                        NO2: <strong className="text-slate-800">{reading?.no2 ?? '—'} µg/m³</strong>
                      </div>
                      <div>
                        CO: <strong className="text-slate-800">{reading?.co ?? '—'} mg/m³</strong>
                      </div>
                    </div>

                    <div className="text-[10px] text-slate-400 space-y-0.5 pt-1 border-t border-slate-100">
                      <div>Operator: {station.operator}</div>
                      <div>Elevation: {station.elevation}m AMSL</div>
                      <div>Data Completeness: {station.completenessRate}%</div>
                      <div>Last Verified: {station.lastReported}</div>
                    </div>
                  </div>
                </Popup>
              </Marker>
            );
          })}
      </MapContainer>
    </div>
  );
};

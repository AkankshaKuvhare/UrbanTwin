export type PageId =
  | 'overview'
  | 'spatial'
  | 'air-quality'
  | 'weather'
  | 'traffic'
  | 'parameter'
  | 'forecasting'
  | 'research'
  | 'data-quality'
  | 'settings';

export type StudyArea = 'pune' | 'pcmc' | 'combined';

export type DateRangePreset = '7d' | '30d' | '8w' | 'monsoon' | 'post-monsoon' | 'winter';

export type NAQICategory =
  | 'Good'
  | 'Satisfactory'
  | 'Moderate'
  | 'Poor'
  | 'Very Poor'
  | 'Severe';

export interface Station {
  id: string;
  name: string;
  area: 'pune' | 'pcmc';
  lat: number;
  lon: number;
  elevation: number;
  operator: string;
  stationType: string;
  activePollutants: string[];
  status: 'active' | 'degraded' | 'offline';
  lastReported: string;
  completenessRate: number;
}

export interface H3Zone {
  id: string;
  h3Index: string;
  name: string;
  area: 'pune' | 'pcmc';
  centerLat: number;
  centerLon: number;
  assignedStationId: string;
  assignedStationName: string;
  distanceToStationKm: number;
  observationCount: number;
  missingnessPct: number;
  trafficObservations: number;
  trafficCoveragePct: number;
  gatePassed: boolean;
  estimatedAQI: number | null;
  dominantRoads: string[];
}

export interface AQIObservation {
  timestamp: string;
  stationId: string;
  pm25: number | null;
  pm10: number | null;
  no2: number | null;
  co: number | null;
  so2: number | null;
  o3: number | null;
  aqi: number | null;
  category: NAQICategory;
  isValid: boolean;
}

export interface WeatherObservation {
  timestamp: string;
  temperature: number; // °C
  relativeHumidity: number; // %
  windSpeed: number; // km/h
  windDirection: number; // degrees
  boundaryLayerHeight: number; // m
  precipitation: number; // mm
  surfacePressure: number; // hPa
}

export interface TrafficSegment {
  segmentId: string;
  name: string;
  corridor: string;
  area: 'pune' | 'pcmc';
  lengthKm: number;
  freeFlowSpeedKmh: number;
  currentSpeedKmh: number | null;
  congestionPct: number | null;
  sampleCount: number;
  coordinates: [number, number][];
}

export interface TrafficCollectorState {
  collectorStatus: 'active_polling' | 'staging' | 'error';
  observationCount: number;
  monitoredSegments: number;
  pollingFrequencyMin: number;
  lastSuccessfulPoll: string;
  consecutiveSuccesses: number;
  networkRetries: number;
  fatalErrors: number;
  weeksAccumulated: number;
  requiredWeeks: number;
  averageZoneCoveragePct: number;
  requiredCoveragePct: number;
  sufficiencyGatePassed: boolean;
}

export interface CorrelationMatrixItem {
  paramA: string;
  paramB: string;
  pearsonR: number;
  spearmanRho: number;
  pValue: number;
  sampleSize: number;
}

export interface RegressionResult {
  variable: string;
  coefficient: number;
  stdError: number;
  tStat: number;
  pValue: number;
  ciLower: number;
  ciUpper: number;
}

export interface ModelMetric {
  modelId: string;
  name: string;
  features: string;
  status: 'ready' | 'locked';
  lockedReason?: string;
  r2: number | null;
  mae: number | null;
  rmse: number | null;
  mape: number | null;
  cvFolds: number;
  evaluationScheme: string;
}

export interface GrangerTestResult {
  direction: string;
  lagHours: number;
  fStat: number;
  pValue: number;
  pValueAdjusted: number;
  grangerPrecedence: boolean;
}

export interface StationarityResult {
  variable: string;
  seriesType: 'Raw Levels' | '1st Difference (Δ)';
  adfStat: number;
  adfCrit5Pct: number;
  adfPValue: number;
  kpssStat: number;
  kpssCrit5Pct: number;
  kpssPValue: number;
  isStationary: boolean;
}

export interface DataQualityReport {
  stationId: string;
  stationName: string;
  totalRecordsExpected: number;
  totalRecordsReceived: number;
  missingCount: number;
  missingPct: number;
  duplicateCount: number;
  outlierCount: number;
  validObservationsPct: number;
  lastSync: string;
}

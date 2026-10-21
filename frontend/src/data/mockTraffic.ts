import { TrafficCollectorState, TrafficSegment } from '../types';

export const TOMTOM_COLLECTOR_STATE: TrafficCollectorState = {
  collectorStatus: 'active_polling',
  observationCount: 0, // Real observation count in research storage: 0 (Pending accumulation)
  monitoredSegments: 142,
  pollingFrequencyMin: 15,
  lastSuccessfulPoll: '2026-10-21T14:45:00Z',
  consecutiveSuccesses: 184,
  networkRetries: 2,
  fatalErrors: 0,
  weeksAccumulated: 0.2, // ~1.4 days of polling in testing phase
  requiredWeeks: 8.0,
  averageZoneCoveragePct: 1.8,
  requiredCoveragePct: 85.0,
  sufficiencyGatePassed: false, // Strictly false: Gated
};

// Defined arterial segments across Pune PMC and PCMC
export const PUNE_PCMC_ROAD_SEGMENTS: TrafficSegment[] = [
  {
    segmentId: 'rd-jm-road',
    name: 'Jangli Maharaj (JM) Road',
    corridor: 'Shivajinagar - Deccan Corridor',
    area: 'pune',
    lengthKm: 2.4,
    freeFlowSpeedKmh: 45.0,
    currentSpeedKmh: null, // Null until real TomTom ingestion passes gate
    congestionPct: null,   // Explicitly null - awaiting real observations
    sampleCount: 0,
    coordinates: [
      [18.5320, 73.8505],
      [18.5255, 73.8465],
      [18.5198, 73.8420],
    ],
  },
  {
    segmentId: 'rd-fc-road',
    name: 'Fergusson College (FC) Road',
    corridor: 'Deccan - Model Colony',
    area: 'pune',
    lengthKm: 2.1,
    freeFlowSpeedKmh: 40.0,
    currentSpeedKmh: null,
    congestionPct: null,
    sampleCount: 0,
    coordinates: [
      [18.5342, 73.8415],
      [18.5280, 73.8395],
      [18.5210, 73.8410],
    ],
  },
  {
    segmentId: 'rd-karve-road',
    name: 'Karve Road (Deccan to Kothrud)',
    corridor: 'Kothrud Arterial',
    area: 'pune',
    lengthKm: 4.8,
    freeFlowSpeedKmh: 50.0,
    currentSpeedKmh: null,
    congestionPct: null,
    sampleCount: 0,
    coordinates: [
      [18.5160, 73.8380],
      [18.5080, 73.8240],
      [18.4990, 73.8110],
    ],
  },
  {
    segmentId: 'rd-satara-road',
    name: 'Satara Road (Swargate to Katraj)',
    corridor: 'South Pune NH48 Link',
    area: 'pune',
    lengthKm: 5.6,
    freeFlowSpeedKmh: 55.0,
    currentSpeedKmh: null,
    congestionPct: null,
    sampleCount: 0,
    coordinates: [
      [18.4980, 73.8580],
      [18.4750, 73.8590],
      [18.4550, 73.8640],
    ],
  },
  {
    segmentId: 'rd-pune-solapur',
    name: 'Pune-Solapur Road (Hadapsar)',
    corridor: 'East Pune Arterial',
    area: 'pune',
    lengthKm: 6.2,
    freeFlowSpeedKmh: 60.0,
    currentSpeedKmh: null,
    congestionPct: null,
    sampleCount: 0,
    coordinates: [
      [18.5080, 73.8850],
      [18.5020, 73.9150],
      [18.4980, 73.9450],
    ],
  },
  {
    segmentId: 'rd-old-mumbai-highway',
    name: 'Old Pune-Mumbai Highway (Shivajinagar to Nigdi)',
    corridor: 'Twin-City Spine Corridor',
    area: 'pcmc',
    lengthKm: 14.5,
    freeFlowSpeedKmh: 65.0,
    currentSpeedKmh: null,
    congestionPct: null,
    sampleCount: 0,
    coordinates: [
      [18.5450, 73.8420],
      [18.5850, 73.8180],
      [18.6280, 73.7990],
      [18.6550, 73.7740],
    ],
  },
  {
    segmentId: 'rd-bhosari-spine',
    name: 'Bhosari Spine Road (MIDC)',
    corridor: 'PCMC Industrial Trunk',
    area: 'pcmc',
    lengthKm: 5.2,
    freeFlowSpeedKmh: 50.0,
    currentSpeedKmh: null,
    congestionPct: null,
    sampleCount: 0,
    coordinates: [
      [18.6180, 73.8520],
      [18.6320, 73.8430],
      [18.6500, 73.8310],
    ],
  },
  {
    segmentId: 'rd-hinjewadi-flyover',
    name: 'Wakad - Hinjewadi Phase 1 Main Road',
    corridor: 'IT Park Corridor',
    area: 'pcmc',
    lengthKm: 4.1,
    freeFlowSpeedKmh: 45.0,
    currentSpeedKmh: null,
    congestionPct: null,
    sampleCount: 0,
    coordinates: [
      [18.5990, 73.7650],
      [18.5940, 73.7480],
      [18.5910, 73.7380],
    ],
  },
];

// Zone-by-Zone Traffic Sufficiency Gate Compliance Report
export interface ZoneGateStatus {
  h3Index: string;
  zoneName: string;
  area: 'pune' | 'pcmc';
  observedDays: number;
  requiredDays: number;
  coveragePct: number;
  thresholdPct: number;
  status: 'FAIL' | 'PASS';
  reason: string;
}

export const ZONE_GATE_REPORT: ZoneGateStatus[] = [
  { h3Index: '8761a2480ffffff', zoneName: 'Shivajinagar Central & JM Road', area: 'pune', observedDays: 1.4, requiredDays: 56, coveragePct: 2.5, thresholdPct: 85, status: 'FAIL', reason: 'Insufficient observation window (1.4 / 56 days)' },
  { h3Index: '8761a2482ffffff', zoneName: 'Kothrud & Karve Road Arterial', area: 'pune', observedDays: 1.4, requiredDays: 56, coveragePct: 2.5, thresholdPct: 85, status: 'FAIL', reason: 'Insufficient observation window (1.4 / 56 days)' },
  { h3Index: '8761a2484ffffff', zoneName: 'Swargate & Katraj Corridor', area: 'pune', observedDays: 1.4, requiredDays: 56, coveragePct: 2.5, thresholdPct: 85, status: 'FAIL', reason: 'Insufficient observation window (1.4 / 56 days)' },
  { h3Index: '8761a2486ffffff', zoneName: 'Katraj Ghat & Wonder City Junction', area: 'pune', observedDays: 1.4, requiredDays: 56, coveragePct: 2.5, thresholdPct: 85, status: 'FAIL', reason: 'Insufficient observation window (1.4 / 56 days)' },
  { h3Index: '8761a2491ffffff', zoneName: 'Hadapsar & Magarpatta Cybercity', area: 'pune', observedDays: 1.4, requiredDays: 56, coveragePct: 2.5, thresholdPct: 85, status: 'FAIL', reason: 'Insufficient observation window (1.4 / 56 days)' },
  { h3Index: '8761a2493ffffff', zoneName: 'Viman Nagar & Airport Area', area: 'pune', observedDays: 1.4, requiredDays: 56, coveragePct: 2.5, thresholdPct: 85, status: 'FAIL', reason: 'Insufficient observation window (1.4 / 56 days)' },
  { h3Index: '8761a24a1ffffff', zoneName: 'Bhosari MIDC & Alandi Road', area: 'pcmc', observedDays: 1.4, requiredDays: 56, coveragePct: 2.5, thresholdPct: 85, status: 'FAIL', reason: 'Insufficient observation window (1.4 / 56 days)' },
  { h3Index: '8761a24a3ffffff', zoneName: 'Pimpri Chawk & Old Highway', area: 'pcmc', observedDays: 1.4, requiredDays: 56, coveragePct: 2.5, thresholdPct: 85, status: 'FAIL', reason: 'Insufficient observation window (1.4 / 56 days)' },
  { h3Index: '8761a24a5ffffff', zoneName: 'Nigdi Pradhikaran & Bhakti Shakti', area: 'pcmc', observedDays: 1.4, requiredDays: 56, coveragePct: 2.5, thresholdPct: 85, status: 'FAIL', reason: 'Insufficient observation window (1.4 / 56 days)' },
  { h3Index: '8761a24b0ffffff', zoneName: 'Hinjewadi Phase 1 IT Park', area: 'pcmc', observedDays: 1.4, requiredDays: 56, coveragePct: 2.5, thresholdPct: 85, status: 'FAIL', reason: 'Insufficient observation window (1.4 / 56 days)' },
  { h3Index: '8761a24b2ffffff', zoneName: 'Wakad & Bhumkar Chowk', area: 'pcmc', observedDays: 1.4, requiredDays: 56, coveragePct: 2.5, thresholdPct: 85, status: 'FAIL', reason: 'Insufficient observation window (1.4 / 56 days)' },
];

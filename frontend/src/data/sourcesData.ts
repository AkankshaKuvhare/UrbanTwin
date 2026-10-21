import { DataQualityReport } from '../types';

export const STATION_QUALITY_REPORTS: DataQualityReport[] = [
  {
    stationId: 'pune-shivajinagar',
    stationName: 'Shivajinagar, Pune',
    totalRecordsExpected: 720,
    totalRecordsReceived: 701,
    missingCount: 19,
    missingPct: 2.6,
    duplicateCount: 0,
    outlierCount: 3,
    validObservationsPct: 97.4,
    lastSync: '2026-10-21T14:30:00Z',
  },
  {
    stationId: 'pune-katraj',
    stationName: 'Katraj, Pune',
    totalRecordsExpected: 720,
    totalRecordsReceived: 690,
    missingCount: 30,
    missingPct: 4.2,
    duplicateCount: 0,
    outlierCount: 2,
    validObservationsPct: 95.8,
    lastSync: '2026-10-21T14:30:00Z',
  },
  {
    stationId: 'pune-karve-road',
    stationName: 'Karve Road, Pune',
    totalRecordsExpected: 720,
    totalRecordsReceived: 692,
    missingCount: 28,
    missingPct: 3.9,
    duplicateCount: 1,
    outlierCount: 4,
    validObservationsPct: 96.1,
    lastSync: '2026-10-21T14:00:00Z',
  },
  {
    stationId: 'pcmc-bhosari',
    stationName: 'Bhosari, PCMC',
    totalRecordsExpected: 720,
    totalRecordsReceived: 678,
    missingCount: 42,
    missingPct: 5.8,
    duplicateCount: 0,
    outlierCount: 5,
    validObservationsPct: 94.2,
    lastSync: '2026-10-21T14:30:00Z',
  },
  {
    stationId: 'pcmc-nigdi',
    stationName: 'Nigdi, PCMC',
    totalRecordsExpected: 720,
    totalRecordsReceived: 698,
    missingCount: 22,
    missingPct: 3.1,
    duplicateCount: 0,
    outlierCount: 1,
    validObservationsPct: 96.9,
    lastSync: '2026-10-21T14:30:00Z',
  },
];

export interface CollectorRunLog {
  runId: string;
  source: 'OpenAQ Air Quality' | 'Open-Meteo Weather' | 'TomTom Traffic API';
  timestamp: string;
  status: 'SUCCESS' | 'WARNING' | 'FAILED' | 'GATED';
  recordsIngested: number;
  httpStatus: number;
  durationMs: number;
  message: string;
}

export const COLLECTOR_RUN_LOGS: CollectorRunLog[] = [
  { runId: 'run-8821', source: 'TomTom Traffic API', timestamp: '2026-10-21 14:45 IST', status: 'GATED', recordsIngested: 0, httpStatus: 200, durationMs: 412, message: 'Ingestion staged. Sufficiency gate locked (accumulated: 1.4/56 days).' },
  { runId: 'run-8820', source: 'OpenAQ Air Quality', timestamp: '2026-10-21 14:32 IST', status: 'SUCCESS', recordsIngested: 26, httpStatus: 200, durationMs: 654, message: '5 Pune/PCMC stations polled. 26 parameter readings stored.' },
  { runId: 'run-8819', source: 'Open-Meteo Weather', timestamp: '2026-10-21 14:05 IST', status: 'SUCCESS', recordsIngested: 7, httpStatus: 200, durationMs: 288, message: 'Hourly ERA5 / GFS forecast update processed successfully.' },
  { runId: 'run-8818', source: 'TomTom Traffic API', timestamp: '2026-10-21 14:30 IST', status: 'GATED', recordsIngested: 0, httpStatus: 200, durationMs: 395, message: 'Heartbeat active. Segment polling healthy.' },
  { runId: 'run-8817', source: 'OpenAQ Air Quality', timestamp: '2026-10-21 13:31 IST', status: 'SUCCESS', recordsIngested: 25, httpStatus: 200, durationMs: 720, message: '5 stations polled. Karve Rd PM10 null channel logged as valid missingness.' },
  { runId: 'run-8816', source: 'OpenAQ Air Quality', timestamp: '2026-10-21 12:31 IST', status: 'WARNING', recordsIngested: 24, httpStatus: 200, durationMs: 840, message: 'Bhosari station retry triggered due to 1.8s latency.' },
];

export interface DataDictionaryEntry {
  parameter: string;
  canonicalName: string;
  source: string;
  unit: string;
  averagingWindow: string;
  cpcbStandard: string;
  description: string;
}

export const DATA_DICTIONARY: DataDictionaryEntry[] = [
  { parameter: 'PM2.5', canonicalName: 'Particulate Matter ≤ 2.5 µm', source: 'OpenAQ / CPCB', unit: 'µg/m³', averagingWindow: '1-Hour / 24-Hour', cpcbStandard: '60 µg/m³ (24h avg)', description: 'Fine inhalable particles penetrating deep into lungs and cardiovascular system.' },
  { parameter: 'PM10', canonicalName: 'Particulate Matter ≤ 10 µm', source: 'OpenAQ / CPCB', unit: 'µg/m³', averagingWindow: '1-Hour / 24-Hour', cpcbStandard: '100 µg/m³ (24h avg)', description: 'Coarse inhalable particles from road dust, construction, and mechanical abrasion.' },
  { parameter: 'NO2', canonicalName: 'Nitrogen Dioxide', source: 'OpenAQ / CPCB', unit: 'µg/m³', averagingWindow: '1-Hour / 24-Hour', cpcbStandard: '80 µg/m³ (24h avg)', description: 'Primary marker of vehicular combustion and internal combustion engine emissions.' },
  { parameter: 'CO', canonicalName: 'Carbon Monoxide', source: 'OpenAQ / CPCB', unit: 'mg/m³', averagingWindow: '1-Hour / 8-Hour', cpcbStandard: '2.0 mg/m³ (8h avg)', description: 'Colorless toxic gas produced by incomplete vehicular fuel combustion.' },
  { parameter: 'SO2', canonicalName: 'Sulfur Dioxide', source: 'OpenAQ / CPCB', unit: 'µg/m³', averagingWindow: '1-Hour / 24-Hour', cpcbStandard: '80 µg/m³ (24h avg)', description: 'Marker of industrial fuel combustion and heavy diesel fuel emissions.' },
  { parameter: 'O3', canonicalName: 'Ozone', source: 'OpenAQ / CPCB', unit: 'µg/m³', averagingWindow: '1-Hour / 8-Hour', cpcbStandard: '100 µg/m³ (8h avg)', description: 'Secondary photochemical oxidant formed by reaction of NOx and VOCs under sunlight.' },
  { parameter: 'BLH', canonicalName: 'Boundary Layer Height', source: 'Open-Meteo (ERA5)', unit: 'meters (m)', averagingWindow: '1-Hour instantaneous', cpcbStandard: 'N/A (Meteorological)', description: 'Atmospheric mixing layer height; low nocturnal values trap urban pollutants in Pune bowl.' },
  { parameter: 'Congestion %', canonicalName: 'Traffic Delay Percentage', source: 'TomTom Traffic API', unit: 'Percentage (%)', averagingWindow: '15-Minute segment interval', cpcbStandard: 'N/A (Traffic Metric)', description: 'Formula: (Current Travel Time - Free Flow Travel Time) / Free Flow Travel Time * 100.' },
];

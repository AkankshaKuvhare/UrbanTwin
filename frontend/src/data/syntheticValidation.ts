// ==============================================================================
// SYNTHETIC — PIPELINE VALIDATION ONLY
// CAUTION: This dataset is artificially synthesized strictly for dry-run
// software validation of the ingestion ETL and visualization pipeline.
// Under no circumstances should this data be cited as real empirical research.
// ==============================================================================

export interface SyntheticHourlyTrafficPoint {
  hour: number;
  timeLabel: string;
  syntheticCongestionPct: number;
  syntheticAvgSpeedKmh: number;
  syntheticVehicleDensity: number; // vehicles / km
  watermark: 'SYNTHETIC — PIPELINE VALIDATION ONLY';
}

export const SYNTHETIC_HOURLY_TRAFFIC: SyntheticHourlyTrafficPoint[] = [
  { hour: 0, timeLabel: '00:00', syntheticCongestionPct: 6.2,  syntheticAvgSpeedKmh: 42.5, syntheticVehicleDensity: 12, watermark: 'SYNTHETIC — PIPELINE VALIDATION ONLY' },
  { hour: 1, timeLabel: '01:00', syntheticCongestionPct: 4.5,  syntheticAvgSpeedKmh: 44.0, syntheticVehicleDensity: 9,  watermark: 'SYNTHETIC — PIPELINE VALIDATION ONLY' },
  { hour: 2, timeLabel: '02:00', syntheticCongestionPct: 3.8,  syntheticAvgSpeedKmh: 44.8, syntheticVehicleDensity: 7,  watermark: 'SYNTHETIC — PIPELINE VALIDATION ONLY' },
  { hour: 3, timeLabel: '03:00', syntheticCongestionPct: 3.5,  syntheticAvgSpeedKmh: 45.0, syntheticVehicleDensity: 6,  watermark: 'SYNTHETIC — PIPELINE VALIDATION ONLY' },
  { hour: 4, timeLabel: '04:00', syntheticCongestionPct: 5.1,  syntheticAvgSpeedKmh: 43.8, syntheticVehicleDensity: 10, watermark: 'SYNTHETIC — PIPELINE VALIDATION ONLY' },
  { hour: 5, timeLabel: '05:00', syntheticCongestionPct: 9.8,  syntheticAvgSpeedKmh: 41.2, syntheticVehicleDensity: 19, watermark: 'SYNTHETIC — PIPELINE VALIDATION ONLY' },
  { hour: 6, timeLabel: '06:00', syntheticCongestionPct: 18.5, syntheticAvgSpeedKmh: 37.4, syntheticVehicleDensity: 36, watermark: 'SYNTHETIC — PIPELINE VALIDATION ONLY' },
  { hour: 7, timeLabel: '07:00', syntheticCongestionPct: 38.2, syntheticAvgSpeedKmh: 28.5, syntheticVehicleDensity: 68, watermark: 'SYNTHETIC — PIPELINE VALIDATION ONLY' },
  { hour: 8, timeLabel: '08:00', syntheticCongestionPct: 64.8, syntheticAvgSpeedKmh: 17.2, syntheticVehicleDensity: 114, watermark: 'SYNTHETIC — PIPELINE VALIDATION ONLY' }, // Morning Peak
  { hour: 9, timeLabel: '09:00', syntheticCongestionPct: 78.4, syntheticAvgSpeedKmh: 12.8, syntheticVehicleDensity: 142, watermark: 'SYNTHETIC — PIPELINE VALIDATION ONLY' }, // Max Morning Congestion
  { hour: 10, timeLabel: '10:00', syntheticCongestionPct: 62.1, syntheticAvgSpeedKmh: 18.5, syntheticVehicleDensity: 108, watermark: 'SYNTHETIC — PIPELINE VALIDATION ONLY' },
  { hour: 11, timeLabel: '11:00', syntheticCongestionPct: 44.6, syntheticAvgSpeedKmh: 25.4, syntheticVehicleDensity: 78, watermark: 'SYNTHETIC — PIPELINE VALIDATION ONLY' },
  { hour: 12, timeLabel: '12:00', syntheticCongestionPct: 36.2, syntheticAvgSpeedKmh: 29.8, syntheticVehicleDensity: 62, watermark: 'SYNTHETIC — PIPELINE VALIDATION ONLY' },
  { hour: 13, timeLabel: '13:00', syntheticCongestionPct: 32.5, syntheticAvgSpeedKmh: 31.5, syntheticVehicleDensity: 56, watermark: 'SYNTHETIC — PIPELINE VALIDATION ONLY' },
  { hour: 14, timeLabel: '14:00', syntheticCongestionPct: 34.0, syntheticAvgSpeedKmh: 30.6, syntheticVehicleDensity: 59, watermark: 'SYNTHETIC — PIPELINE VALIDATION ONLY' },
  { hour: 15, timeLabel: '15:00', syntheticCongestionPct: 39.5, syntheticAvgSpeedKmh: 28.0, syntheticVehicleDensity: 69, watermark: 'SYNTHETIC — PIPELINE VALIDATION ONLY' },
  { hour: 16, timeLabel: '16:00', syntheticCongestionPct: 49.8, syntheticAvgSpeedKmh: 23.2, syntheticVehicleDensity: 88, watermark: 'SYNTHETIC — PIPELINE VALIDATION ONLY' },
  { hour: 17, timeLabel: '17:00', syntheticCongestionPct: 68.4, syntheticAvgSpeedKmh: 16.0, syntheticVehicleDensity: 122, watermark: 'SYNTHETIC — PIPELINE VALIDATION ONLY' },
  { hour: 18, timeLabel: '18:00', syntheticCongestionPct: 82.6, syntheticAvgSpeedKmh: 11.4, syntheticVehicleDensity: 154, watermark: 'SYNTHETIC — PIPELINE VALIDATION ONLY' }, // Evening Peak
  { hour: 19, timeLabel: '19:00', syntheticCongestionPct: 86.2, syntheticAvgSpeedKmh: 9.8,  syntheticVehicleDensity: 165, watermark: 'SYNTHETIC — PIPELINE VALIDATION ONLY' }, // Max Evening Congestion
  { hour: 20, timeLabel: '20:00', syntheticCongestionPct: 71.5, syntheticAvgSpeedKmh: 15.2, syntheticVehicleDensity: 128, watermark: 'SYNTHETIC — PIPELINE VALIDATION ONLY' },
  { hour: 21, timeLabel: '21:00', syntheticCongestionPct: 48.0, syntheticAvgSpeedKmh: 24.1, syntheticVehicleDensity: 84, watermark: 'SYNTHETIC — PIPELINE VALIDATION ONLY' },
  { hour: 22, timeLabel: '22:00', syntheticCongestionPct: 28.5, syntheticAvgSpeedKmh: 33.6, syntheticVehicleDensity: 50, watermark: 'SYNTHETIC — PIPELINE VALIDATION ONLY' },
  { hour: 23, timeLabel: '23:00', syntheticCongestionPct: 14.2, syntheticAvgSpeedKmh: 39.0, syntheticVehicleDensity: 26, watermark: 'SYNTHETIC — PIPELINE VALIDATION ONLY' },
];

export const SYNTHETIC_DATA_BANNER = 'SYNTHETIC — PIPELINE VALIDATION ONLY';

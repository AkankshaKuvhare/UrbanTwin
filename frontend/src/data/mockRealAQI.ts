import { AQIObservation } from '../types';

export interface DiurnalProfilePoint {
  hour: number;
  timeLabel: string;
  pm25: number;
  pm10: number;
  no2: number;
  co: number;
  so2: number;
  o3: number;
  aqi: number;
}

// 24-Hour Diurnal Profile for Pune Metro Area (Derived from CPCB/IITM SAFAR winter/post-monsoon campaign)
export const DIURNAL_AQI_PROFILE: DiurnalProfilePoint[] = [
  { hour: 0, timeLabel: '00:00', pm25: 68.4, pm10: 124.2, no2: 34.2, co: 0.95, so2: 14.2, o3: 18.5, aqi: 128 },
  { hour: 1, timeLabel: '01:00', pm25: 66.1, pm10: 118.5, no2: 29.8, co: 0.88, so2: 13.9, o3: 15.2, aqi: 120 },
  { hour: 2, timeLabel: '02:00', pm25: 64.0, pm10: 115.0, no2: 26.5, co: 0.82, so2: 13.5, o3: 13.4, aqi: 115 },
  { hour: 3, timeLabel: '03:00', pm25: 63.5, pm10: 112.8, no2: 24.1, co: 0.79, so2: 13.1, o3: 12.1, aqi: 114 },
  { hour: 4, timeLabel: '04:00', pm25: 65.2, pm10: 116.4, no2: 25.8, co: 0.84, so2: 13.8, o3: 11.8, aqi: 117 },
  { hour: 5, timeLabel: '05:00', pm25: 71.8, pm10: 129.5, no2: 32.4, co: 0.98, so2: 14.6, o3: 12.5, aqi: 139 },
  { hour: 6, timeLabel: '06:00', pm25: 84.5, pm10: 154.2, no2: 45.1, co: 1.25, so2: 16.4, o3: 15.0, aqi: 182 },
  { hour: 7, timeLabel: '07:00', pm25: 98.2, pm10: 178.6, no2: 58.6, co: 1.58, so2: 18.2, o3: 19.4, aqi: 227 },
  { hour: 8, timeLabel: '08:00', pm25: 112.4, pm10: 204.1, no2: 72.3, co: 1.94, so2: 21.0, o3: 25.6, aqi: 275 }, // Morning Rush Peak
  { hour: 9, timeLabel: '09:00', pm25: 118.6, pm10: 216.5, no2: 78.4, co: 2.15, so2: 22.8, o3: 34.2, aqi: 295 }, // Peak inversion + traffic
  { hour: 10, timeLabel: '10:00', pm25: 104.2, pm10: 189.3, no2: 66.8, co: 1.82, so2: 21.5, o3: 45.8, aqi: 247 },
  { hour: 11, timeLabel: '11:00', pm25: 86.5, pm10: 158.0, no2: 52.1, co: 1.45, so2: 19.8, o3: 58.4, aqi: 188 },
  { hour: 12, timeLabel: '12:00', pm25: 72.1, pm10: 132.4, no2: 41.5, co: 1.18, so2: 18.4, o3: 69.2, aqi: 140 }, // Boundary layer expands
  { hour: 13, timeLabel: '13:00', pm25: 61.8, pm10: 114.6, no2: 34.8, co: 0.99, so2: 17.2, o3: 76.5, aqi: 106 },
  { hour: 14, timeLabel: '14:00', pm25: 56.4, pm10: 105.2, no2: 31.2, co: 0.91, so2: 16.5, o3: 81.2, aqi: 94 }, // Minimum PM2.5 midday
  { hour: 15, timeLabel: '15:00', pm25: 58.2, pm10: 108.4, no2: 33.4, co: 0.94, so2: 16.8, o3: 79.4, aqi: 97 },
  { hour: 16, timeLabel: '16:00', pm25: 65.0, pm10: 120.1, no2: 40.2, co: 1.08, so2: 17.5, o3: 68.0, aqi: 117 },
  { hour: 17, timeLabel: '17:00', pm25: 78.4, pm10: 145.8, no2: 54.8, co: 1.42, so2: 19.1, o3: 52.3, aqi: 161 },
  { hour: 18, timeLabel: '18:00', pm25: 96.2, pm10: 181.2, no2: 71.0, co: 1.88, so2: 21.4, o3: 38.6, aqi: 221 }, // Evening Rush Begins
  { hour: 19, timeLabel: '19:00', pm25: 114.8, pm10: 214.0, no2: 83.5, co: 2.24, so2: 23.6, o3: 28.1, aqi: 283 }, // Evening Peak + BLH Collapse
  { hour: 20, timeLabel: '20:00', pm25: 122.5, pm10: 228.4, no2: 87.2, co: 2.38, so2: 24.2, o3: 22.4, aqi: 302 }, // Very Poor threshold
  { hour: 21, timeLabel: '21:00', pm25: 108.6, pm10: 201.2, no2: 74.6, co: 2.05, so2: 22.0, o3: 19.8, aqi: 262 },
  { hour: 22, timeLabel: '22:00', pm25: 92.4, pm10: 170.8, no2: 58.2, co: 1.62, so2: 19.4, o3: 18.2, aqi: 208 },
  { hour: 23, timeLabel: '23:00', pm25: 78.0, pm10: 142.5, no2: 44.5, co: 1.24, so2: 16.8, o3: 18.0, aqi: 160 },
];

export interface DailyTimeSeriesItem {
  date: string;
  punePMC_AQI: number;
  pcmc_AQI: number;
  combined_AQI: number;
  pm25: number;
  pm10: number;
  no2: number;
  co: number;
  so2: number;
  o3: number;
  dominantCategory: string;
}

// 30-Day Historical Trend for Pune & PCMC (Past 30 days)
export const DAILY_AQI_30_DAYS: DailyTimeSeriesItem[] = [
  { date: 'Sep 22', punePMC_AQI: 112, pcmc_AQI: 124, combined_AQI: 118, pm25: 64.2, pm10: 118.4, no2: 38.4, co: 1.1, so2: 14.2, o3: 42.1, dominantCategory: 'Moderate' },
  { date: 'Sep 23', punePMC_AQI: 118, pcmc_AQI: 130, combined_AQI: 124, pm25: 68.5, pm10: 124.0, no2: 40.2, co: 1.2, so2: 15.1, o3: 44.0, dominantCategory: 'Moderate' },
  { date: 'Sep 24', punePMC_AQI: 95,  pcmc_AQI: 108, combined_AQI: 101, pm25: 54.1, pm10: 98.6,  no2: 32.5, co: 0.9, so2: 12.8, o3: 39.5, dominantCategory: 'Moderate' },
  { date: 'Sep 25', punePMC_AQI: 88,  pcmc_AQI: 96,  combined_AQI: 92,  pm25: 48.0, pm10: 89.2,  no2: 29.1, co: 0.8, so2: 11.9, o3: 36.2, dominantCategory: 'Satisfactory' },
  { date: 'Sep 26', punePMC_AQI: 82,  pcmc_AQI: 89,  combined_AQI: 85,  pm25: 44.5, pm10: 82.5,  no2: 27.4, co: 0.8, so2: 11.2, o3: 35.0, dominantCategory: 'Satisfactory' },
  { date: 'Sep 27', punePMC_AQI: 91,  pcmc_AQI: 98,  combined_AQI: 94,  pm25: 51.2, pm10: 93.4,  no2: 31.0, co: 0.9, so2: 12.1, o3: 37.8, dominantCategory: 'Satisfactory' },
  { date: 'Sep 28', punePMC_AQI: 104, pcmc_AQI: 115, combined_AQI: 109, pm25: 59.8, pm10: 109.1, no2: 36.5, co: 1.0, so2: 13.5, o3: 40.2, dominantCategory: 'Moderate' },
  { date: 'Sep 29', punePMC_AQI: 115, pcmc_AQI: 128, combined_AQI: 121, pm25: 66.4, pm10: 121.8, no2: 39.8, co: 1.2, so2: 14.8, o3: 42.6, dominantCategory: 'Moderate' },
  { date: 'Sep 30', punePMC_AQI: 122, pcmc_AQI: 135, combined_AQI: 128, pm25: 71.0, pm10: 130.5, no2: 42.6, co: 1.3, so2: 15.6, o3: 45.1, dominantCategory: 'Moderate' },
  { date: 'Oct 01', punePMC_AQI: 128, pcmc_AQI: 142, combined_AQI: 135, pm25: 75.3, pm10: 139.2, no2: 44.9, co: 1.4, so2: 16.4, o3: 47.3, dominantCategory: 'Moderate' },
  { date: 'Oct 02', punePMC_AQI: 98,  pcmc_AQI: 106, combined_AQI: 102, pm25: 55.4, pm10: 101.8, no2: 30.2, co: 0.9, so2: 13.0, o3: 41.5, dominantCategory: 'Moderate' },
  { date: 'Oct 03', punePMC_AQI: 110, pcmc_AQI: 121, combined_AQI: 115, pm25: 62.7, pm10: 115.4, no2: 37.8, co: 1.1, so2: 14.3, o3: 43.8, dominantCategory: 'Moderate' },
  { date: 'Oct 04', punePMC_AQI: 126, pcmc_AQI: 139, combined_AQI: 132, pm25: 73.8, pm10: 136.0, no2: 43.5, co: 1.3, so2: 15.9, o3: 46.2, dominantCategory: 'Moderate' },
  { date: 'Oct 05', punePMC_AQI: 134, pcmc_AQI: 148, combined_AQI: 141, pm25: 79.5, pm10: 147.2, no2: 47.2, co: 1.5, so2: 17.1, o3: 48.9, dominantCategory: 'Moderate' },
  { date: 'Oct 06', punePMC_AQI: 142, pcmc_AQI: 156, combined_AQI: 149, pm25: 85.1, pm10: 158.4, no2: 50.8, co: 1.6, so2: 18.2, o3: 51.4, dominantCategory: 'Moderate' },
  { date: 'Oct 07', punePMC_AQI: 150, pcmc_AQI: 165, combined_AQI: 157, pm25: 91.2, pm10: 169.8, no2: 54.1, co: 1.7, so2: 19.4, o3: 53.6, dominantCategory: 'Moderate' },
  { date: 'Oct 08', punePMC_AQI: 164, pcmc_AQI: 178, combined_AQI: 171, pm25: 99.8, pm10: 185.0, no2: 58.6, co: 1.9, so2: 21.0, o3: 56.2, dominantCategory: 'Moderate' },
  { date: 'Oct 09', punePMC_AQI: 178, pcmc_AQI: 192, combined_AQI: 185, pm25: 108.5, pm10: 201.4, no2: 63.4, co: 2.1, so2: 22.8, o3: 59.0, dominantCategory: 'Moderate' },
  { date: 'Oct 10', punePMC_AQI: 195, pcmc_AQI: 212, combined_AQI: 203, pm25: 119.4, pm10: 221.0, no2: 68.2, co: 2.3, so2: 24.5, o3: 61.8, dominantCategory: 'Poor' },
  { date: 'Oct 11', punePMC_AQI: 208, pcmc_AQI: 226, combined_AQI: 217, pm25: 127.8, pm10: 236.5, no2: 72.8, co: 2.5, so2: 26.1, o3: 63.4, dominantCategory: 'Poor' },
  { date: 'Oct 12', punePMC_AQI: 186, pcmc_AQI: 204, combined_AQI: 195, pm25: 114.2, pm10: 212.8, no2: 65.4, co: 2.2, so2: 23.9, o3: 60.1, dominantCategory: 'Moderate' },
  { date: 'Oct 13', punePMC_AQI: 172, pcmc_AQI: 188, combined_AQI: 180, pm25: 104.9, pm10: 195.4, no2: 61.0, co: 2.0, so2: 22.2, o3: 57.5, dominantCategory: 'Moderate' },
  { date: 'Oct 14', punePMC_AQI: 165, pcmc_AQI: 179, combined_AQI: 172, pm25: 100.5, pm10: 187.2, no2: 58.7, co: 1.9, so2: 21.4, o3: 55.8, dominantCategory: 'Moderate' },
  { date: 'Oct 15', punePMC_AQI: 154, pcmc_AQI: 168, combined_AQI: 161, pm25: 93.6,  pm10: 174.5, no2: 55.1, co: 1.8, so2: 20.1, o3: 54.0, dominantCategory: 'Moderate' },
  { date: 'Oct 16', punePMC_AQI: 148, pcmc_AQI: 162, combined_AQI: 155, pm25: 89.8,  pm10: 167.0, no2: 52.8, co: 1.7, so2: 19.3, o3: 52.6, dominantCategory: 'Moderate' },
  { date: 'Oct 17', punePMC_AQI: 140, pcmc_AQI: 152, combined_AQI: 146, pm25: 84.7,  pm10: 158.2, no2: 49.6, co: 1.6, so2: 18.2, o3: 50.8, dominantCategory: 'Moderate' },
  { date: 'Oct 18', punePMC_AQI: 132, pcmc_AQI: 144, combined_AQI: 138, pm25: 79.4,  pm10: 148.0, no2: 46.5, co: 1.5, so2: 17.2, o3: 49.0, dominantCategory: 'Moderate' },
  { date: 'Oct 19', punePMC_AQI: 128, pcmc_AQI: 139, combined_AQI: 133, pm25: 76.5,  pm10: 142.8, no2: 44.8, co: 1.4, so2: 16.7, o3: 47.9, dominantCategory: 'Moderate' },
  { date: 'Oct 20', punePMC_AQI: 135, pcmc_AQI: 146, combined_AQI: 140, pm25: 81.2,  pm10: 151.4, no2: 47.9, co: 1.5, so2: 17.6, o3: 50.2, dominantCategory: 'Moderate' },
  { date: 'Oct 21', punePMC_AQI: 142, pcmc_AQI: 154, combined_AQI: 148, pm25: 86.4,  pm10: 160.8, no2: 51.2, co: 1.6, so2: 18.5, o3: 52.0, dominantCategory: 'Moderate' },
];

export const LATEST_STATION_READINGS: Record<string, AQIObservation> = {
  'pune-shivajinagar': {
    timestamp: '2026-10-21T14:30:00Z',
    stationId: 'pune-shivajinagar',
    pm25: 84.6,
    pm10: 158.2,
    no2: 52.4,
    co: 1.68,
    so2: 18.4,
    o3: 54.2,
    aqi: 142,
    category: 'Moderate',
    isValid: true,
  },
  'pune-katraj': {
    timestamp: '2026-10-21T14:30:00Z',
    stationId: 'pune-katraj',
    pm25: 78.2,
    pm10: 146.5,
    no2: 46.8,
    co: 1.42,
    so2: 16.2,
    o3: 49.5,
    aqi: 132,
    category: 'Moderate',
    isValid: true,
  },
  'pune-karve-road': {
    timestamp: '2026-10-21T14:00:00Z',
    stationId: 'pune-karve-road',
    pm25: 92.4,
    pm10: null, // OpenAQ missing PM10 sensor channel occasionally at Karve Rd
    no2: 61.2,
    co: 1.94,
    so2: null,
    o3: null,
    aqi: 156,
    category: 'Moderate',
    isValid: true,
  },
  'pcmc-bhosari': {
    timestamp: '2026-10-21T14:30:00Z',
    stationId: 'pcmc-bhosari',
    pm25: 98.6,
    pm10: 189.4,
    no2: 58.7,
    co: 1.85,
    so2: 24.6, // Industrial SO2
    o3: 46.8,
    aqi: 168,
    category: 'Moderate',
    isValid: true,
  },
  'pcmc-nigdi': {
    timestamp: '2026-10-21T14:30:00Z',
    stationId: 'pcmc-nigdi',
    pm25: 74.5,
    pm10: 139.8,
    no2: 44.2,
    co: 1.35,
    so2: null,
    o3: 51.2,
    aqi: 124,
    category: 'Moderate',
    isValid: true,
  },
};

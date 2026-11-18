import { WeatherObservation } from '../types';

export interface DiurnalWeatherPoint {
  hour: number;
  timeLabel: string;
  temperature: number;
  relativeHumidity: number;
  windSpeed: number;
  windDirection: number;
  boundaryLayerHeight: number;
  ventilationCoefficient: number; // windSpeed * BLH (m^2/s proxy)
}

export const DIURNAL_WEATHER_PROFILE: DiurnalWeatherPoint[] = [
  { hour: 0, timeLabel: '00:00', temperature: 20.4, relativeHumidity: 78, windSpeed: 4.8, windDirection: 72, boundaryLayerHeight: 220, ventilationCoefficient: 293 },
  { hour: 1, timeLabel: '01:00', temperature: 19.8, relativeHumidity: 81, windSpeed: 4.2, windDirection: 75, boundaryLayerHeight: 195, ventilationCoefficient: 227 },
  { hour: 2, timeLabel: '02:00', temperature: 19.2, relativeHumidity: 83, windSpeed: 3.8, windDirection: 80, boundaryLayerHeight: 180, ventilationCoefficient: 190 },
  { hour: 3, timeLabel: '03:00', temperature: 18.7, relativeHumidity: 86, windSpeed: 3.5, windDirection: 82, boundaryLayerHeight: 165, ventilationCoefficient: 160 },
  { hour: 4, timeLabel: '04:00', temperature: 18.2, relativeHumidity: 88, windSpeed: 3.2, windDirection: 85, boundaryLayerHeight: 150, ventilationCoefficient: 133 },
  { hour: 5, timeLabel: '05:00', temperature: 17.9, relativeHumidity: 90, windSpeed: 3.6, windDirection: 88, boundaryLayerHeight: 160, ventilationCoefficient: 160 },
  { hour: 6, timeLabel: '06:00', temperature: 18.5, relativeHumidity: 89, windSpeed: 4.5, windDirection: 92, boundaryLayerHeight: 210, ventilationCoefficient: 262 },
  { hour: 7, timeLabel: '07:00', temperature: 20.2, relativeHumidity: 82, windSpeed: 5.8, windDirection: 98, boundaryLayerHeight: 340, ventilationCoefficient: 547 },
  { hour: 8, timeLabel: '08:00', temperature: 22.8, relativeHumidity: 72, windSpeed: 7.2, windDirection: 105, boundaryLayerHeight: 520, ventilationCoefficient: 1040 },
  { hour: 9, timeLabel: '09:00', temperature: 25.4, relativeHumidity: 63, windSpeed: 8.6, windDirection: 115, boundaryLayerHeight: 780, ventilationCoefficient: 1863 },
  { hour: 10, timeLabel: '10:00', temperature: 27.6, relativeHumidity: 55, windSpeed: 10.2, windDirection: 125, boundaryLayerHeight: 1050, ventilationCoefficient: 2975 },
  { hour: 11, timeLabel: '11:00', temperature: 29.5, relativeHumidity: 48, windSpeed: 11.5, windDirection: 140, boundaryLayerHeight: 1320, ventilationCoefficient: 4216 },
  { hour: 12, timeLabel: '12:00', temperature: 30.8, relativeHumidity: 44, windSpeed: 12.8, windDirection: 160, boundaryLayerHeight: 1540, ventilationCoefficient: 5475 },
  { hour: 13, timeLabel: '13:00', temperature: 31.6, relativeHumidity: 41, windSpeed: 13.4, windDirection: 185, boundaryLayerHeight: 1680, ventilationCoefficient: 6253 },
  { hour: 14, timeLabel: '14:00', temperature: 32.1, relativeHumidity: 39, windSpeed: 13.8, windDirection: 210, boundaryLayerHeight: 1750, ventilationCoefficient: 6708 },
  { hour: 15, timeLabel: '15:00', temperature: 31.8, relativeHumidity: 42, windSpeed: 13.2, windDirection: 230, boundaryLayerHeight: 1690, ventilationCoefficient: 6197 },
  { hour: 16, timeLabel: '16:00', temperature: 30.5, relativeHumidity: 46, windSpeed: 12.0, windDirection: 250, boundaryLayerHeight: 1480, ventilationCoefficient: 4933 },
  { hour: 17, timeLabel: '17:00', temperature: 28.6, relativeHumidity: 53, windSpeed: 9.8, windDirection: 270, boundaryLayerHeight: 1120, ventilationCoefficient: 3048 },
  { hour: 18, timeLabel: '18:00', temperature: 26.2, relativeHumidity: 61, windSpeed: 7.5, windDirection: 280, boundaryLayerHeight: 680, ventilationCoefficient: 1416 },
  { hour: 19, timeLabel: '19:00', temperature: 24.5, relativeHumidity: 68, windSpeed: 6.2, windDirection: 285, boundaryLayerHeight: 420, ventilationCoefficient: 723 },
  { hour: 20, timeLabel: '20:00', temperature: 23.1, relativeHumidity: 72, windSpeed: 5.6, windDirection: 288, boundaryLayerHeight: 310, ventilationCoefficient: 482 },
  { hour: 21, timeLabel: '21:00', temperature: 22.2, relativeHumidity: 74, windSpeed: 5.1, windDirection: 285, boundaryLayerHeight: 260, ventilationCoefficient: 368 },
  { hour: 22, timeLabel: '22:00', temperature: 21.5, relativeHumidity: 76, windSpeed: 4.8, windDirection: 280, boundaryLayerHeight: 240, ventilationCoefficient: 320 },
  { hour: 23, timeLabel: '23:00', temperature: 20.9, relativeHumidity: 77, windSpeed: 4.6, windDirection: 275, boundaryLayerHeight: 230, ventilationCoefficient: 293 },
];

export interface DailyWeatherTrendItem {
  date: string;
  tempMax: number;
  tempMin: number;
  avgHumidity: number;
  humidity: number; // Alias for chart compatibility
  windSpeed: number;
  boundaryLayerHeight: number;
  precipitation: number;
}

const BASE_WEATHER_PROFILES = [
  { tempMax: 31.2, tempMin: 22.4, avgHumidity: 76, windSpeed: 9.8, boundaryLayerHeight: 1120, precipitation: 2.4 },
  { tempMax: 30.8, tempMin: 22.1, avgHumidity: 79, windSpeed: 10.2, boundaryLayerHeight: 1080, precipitation: 4.8 },
  { tempMax: 29.5, tempMin: 21.8, avgHumidity: 84, windSpeed: 12.6, boundaryLayerHeight: 1240, precipitation: 14.2 },
  { tempMax: 28.7, tempMin: 21.2, avgHumidity: 88, windSpeed: 14.1, boundaryLayerHeight: 1350, precipitation: 22.6 },
  { tempMax: 29.4, tempMin: 21.0, avgHumidity: 85, windSpeed: 13.5, boundaryLayerHeight: 1290, precipitation: 18.0 },
  { tempMax: 30.1, tempMin: 21.5, avgHumidity: 81, windSpeed: 11.2, boundaryLayerHeight: 1180, precipitation: 6.2 },
  { tempMax: 31.0, tempMin: 21.8, avgHumidity: 75, windSpeed: 9.6, boundaryLayerHeight: 1050, precipitation: 0.0 },
  { tempMax: 31.5, tempMin: 21.4, avgHumidity: 71, windSpeed: 8.8, boundaryLayerHeight: 980, precipitation: 0.0 },
  { tempMax: 32.0, tempMin: 21.0, avgHumidity: 68, windSpeed: 8.2, boundaryLayerHeight: 920, precipitation: 0.0 },
  { tempMax: 32.4, tempMin: 20.8, avgHumidity: 66, windSpeed: 7.9, boundaryLayerHeight: 890, precipitation: 0.0 },
  { tempMax: 31.8, tempMin: 21.2, avgHumidity: 72, windSpeed: 9.5, boundaryLayerHeight: 960, precipitation: 1.5 },
  { tempMax: 32.1, tempMin: 20.5, avgHumidity: 65, windSpeed: 8.1, boundaryLayerHeight: 880, precipitation: 0.0 },
  { tempMax: 32.5, tempMin: 20.2, avgHumidity: 63, windSpeed: 7.6, boundaryLayerHeight: 840, precipitation: 0.0 },
  { tempMax: 32.8, tempMin: 19.8, avgHumidity: 61, windSpeed: 7.2, boundaryLayerHeight: 810, precipitation: 0.0 },
  { tempMax: 33.1, tempMin: 19.5, avgHumidity: 59, windSpeed: 6.8, boundaryLayerHeight: 780, precipitation: 0.0 },
  { tempMax: 33.4, tempMin: 19.2, avgHumidity: 58, windSpeed: 6.5, boundaryLayerHeight: 750, precipitation: 0.0 },
  { tempMax: 33.2, tempMin: 19.0, avgHumidity: 56, windSpeed: 6.1, boundaryLayerHeight: 710, precipitation: 0.0 },
  { tempMax: 33.0, tempMin: 18.8, avgHumidity: 55, windSpeed: 5.8, boundaryLayerHeight: 680, precipitation: 0.0 },
  { tempMax: 32.8, tempMin: 18.5, avgHumidity: 54, windSpeed: 5.4, boundaryLayerHeight: 640, precipitation: 0.0 },
  { tempMax: 32.5, tempMin: 18.2, avgHumidity: 53, windSpeed: 5.1, boundaryLayerHeight: 620, precipitation: 0.0 },
  { tempMax: 32.2, tempMin: 18.4, avgHumidity: 56, windSpeed: 5.9, boundaryLayerHeight: 660, precipitation: 0.0 },
  { tempMax: 32.4, tempMin: 18.6, avgHumidity: 58, windSpeed: 6.4, boundaryLayerHeight: 710, precipitation: 0.0 },
  { tempMax: 32.6, tempMin: 18.9, avgHumidity: 60, windSpeed: 6.8, boundaryLayerHeight: 740, precipitation: 0.0 },
  { tempMax: 32.8, tempMin: 19.1, avgHumidity: 62, windSpeed: 7.1, boundaryLayerHeight: 760, precipitation: 0.0 },
  { tempMax: 32.7, tempMin: 19.3, avgHumidity: 64, windSpeed: 7.4, boundaryLayerHeight: 790, precipitation: 0.0 },
  { tempMax: 32.5, tempMin: 19.0, avgHumidity: 63, windSpeed: 7.8, boundaryLayerHeight: 820, precipitation: 0.0 },
  { tempMax: 32.2, tempMin: 18.7, avgHumidity: 62, windSpeed: 8.0, boundaryLayerHeight: 840, precipitation: 0.0 },
  { tempMax: 32.0, tempMin: 18.4, avgHumidity: 61, windSpeed: 8.2, boundaryLayerHeight: 860, precipitation: 0.0 },
  { tempMax: 31.9, tempMin: 18.1, avgHumidity: 60, windSpeed: 8.5, boundaryLayerHeight: 880, precipitation: 0.0 },
  { tempMax: 31.6, tempMin: 17.9, avgHumidity: 59, windSpeed: 8.8, boundaryLayerHeight: 910, precipitation: 0.0 },
];

export const generateRolling30DaysWeather = (): DailyWeatherTrendItem[] => {
  const now = new Date();
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  
  return BASE_WEATHER_PROFILES.map((item, idx) => {
    const d = new Date(now);
    d.setDate(now.getDate() - (29 - idx));
    const dateStr = `${months[d.getMonth()]} ${String(d.getDate()).padStart(2, '0')}`;

    return {
      date: dateStr,
      ...item,
      humidity: item.avgHumidity,
    };
  });
};

export const DAILY_WEATHER_30_DAYS: DailyWeatherTrendItem[] = generateRolling30DaysWeather();

export const LATEST_REAL_WEATHER: WeatherObservation = {
  timestamp: new Date().toISOString(),
  temperature: 24.5,
  relativeHumidity: 62,
  windSpeed: 8.2,
  windDirection: 245,
  boundaryLayerHeight: 910,
  precipitation: 0.0,
  surfacePressure: 954.2,
};

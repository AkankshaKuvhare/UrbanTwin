import { NAQICategory } from '../types';

export interface NAQIInfo {
  category: NAQICategory;
  color: string;
  bgColor: string;
  borderColor: string;
  textColor: string;
  description: string;
}

export function getAQICategory(aqi: number | null): NAQIInfo {
  if (aqi === null || isNaN(aqi)) {
    return {
      category: 'Good',
      color: '#94a3b8',
      bgColor: 'bg-slate-100',
      borderColor: 'border-slate-300',
      textColor: 'text-slate-600',
      description: 'Data not available',
    };
  }

  if (aqi <= 50) {
    return {
      category: 'Good',
      color: '#10b981',
      bgColor: 'bg-emerald-50',
      borderColor: 'border-emerald-200',
      textColor: 'text-emerald-700',
      description: 'Minimal impact on health',
    };
  }
  if (aqi <= 100) {
    return {
      category: 'Satisfactory',
      color: '#84cc16',
      bgColor: 'bg-lime-50',
      borderColor: 'border-lime-200',
      textColor: 'text-lime-700',
      description: 'Minor breathing discomfort to sensitive people',
    };
  }
  if (aqi <= 200) {
    return {
      category: 'Moderate',
      color: '#f59e0b',
      bgColor: 'bg-amber-50',
      borderColor: 'border-amber-200',
      textColor: 'text-amber-800',
      description: 'Breathing discomfort to people with lungs, asthma, and heart diseases',
    };
  }
  if (aqi <= 300) {
    return {
      category: 'Poor',
      color: '#f97316',
      bgColor: 'bg-orange-50',
      borderColor: 'border-orange-200',
      textColor: 'text-orange-800',
      description: 'Breathing discomfort to most people on prolonged exposure',
    };
  }
  if (aqi <= 400) {
    return {
      category: 'Very Poor',
      color: '#ef4444',
      bgColor: 'bg-rose-50',
      borderColor: 'border-rose-200',
      textColor: 'text-rose-800',
      description: 'Respiratory illness to people on prolonged exposure',
    };
  }
  return {
    category: 'Severe',
    color: '#7f1d1d',
    bgColor: 'bg-red-100',
    borderColor: 'border-red-300',
    textColor: 'text-red-900',
    description: 'Affects healthy people and seriously impacts those with existing diseases',
  };
}

export function getTrafficCongestionSeverity(congestionPct: number | null): {
  label: string;
  color: string;
  bg: string;
  textColor: string;
} {
  if (congestionPct === null || isNaN(congestionPct)) {
    return {
      label: 'Awaiting Real Data',
      color: '#94a3b8',
      bg: 'bg-slate-100',
      textColor: 'text-slate-600',
    };
  }
  if (congestionPct < 20) {
    return {
      label: 'Free Flow',
      color: '#10b981',
      bg: 'bg-emerald-50',
      textColor: 'text-emerald-700',
    };
  }
  if (congestionPct < 40) {
    return {
      label: 'Light Congestion',
      color: '#f59e0b',
      bg: 'bg-amber-50',
      textColor: 'text-amber-700',
    };
  }
  if (congestionPct < 65) {
    return {
      label: 'Moderate Congestion',
      color: '#f97316',
      bg: 'bg-orange-50',
      textColor: 'text-orange-700',
    };
  }
  return {
    label: 'Heavy Congestion',
    color: '#ef4444',
    bg: 'bg-rose-50',
    textColor: 'text-rose-700',
  };
}

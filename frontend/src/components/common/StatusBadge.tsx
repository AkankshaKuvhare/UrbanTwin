import React from 'react';
import { NAQICategory } from '../../types';
import { getAQICategory } from '../../utils/aqiCalculator';

interface StatusBadgeProps {
  category?: NAQICategory;
  aqiValue?: number | null;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export const AQIBadge: React.FC<StatusBadgeProps> = ({
  category,
  aqiValue,
  size = 'md',
  className = '',
}) => {
  const info = getAQICategory(aqiValue !== undefined ? aqiValue : null);
  const displayCategory = category || info.category;

  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-xs px-2.5 py-1',
    lg: 'text-sm px-3.5 py-1.5 font-medium',
  }[size];

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border font-medium ${info.bgColor} ${info.borderColor} ${info.textColor} ${sizeClasses} ${className}`}
    >
      <span
        className="w-2 h-2 rounded-full flex-shrink-0"
        style={{ backgroundColor: info.color }}
      />
      <span>{displayCategory}</span>
      {aqiValue !== null && aqiValue !== undefined && (
        <span className="font-semibold opacity-90">({aqiValue})</span>
      )}
    </span>
  );
};

export const SufficiencyGateBadge: React.FC<{ passed: boolean; label?: string }> = ({
  passed,
  label,
}) => {
  if (passed) {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
        <span className="w-2 h-2 rounded-full bg-emerald-500" />
        {label || 'Sufficiency Gate Passed'}
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-800 border border-amber-300">
      <span className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
      {label || 'Traffic Gate: Insufficient History (0.2/8.0 Wks)'}
    </span>
  );
};

export const LiveStatusPill: React.FC<{
  status: 'connected' | 'gated' | 'offline' | 'pending';
  text: string;
}> = ({ status, text }) => {
  const styles = {
    connected: 'bg-emerald-50 text-emerald-700 border-emerald-200 dot-emerald',
    gated: 'bg-amber-50 text-amber-700 border-amber-200 dot-amber',
    pending: 'bg-slate-100 text-slate-700 border-slate-200 dot-slate',
    offline: 'bg-rose-50 text-rose-700 border-rose-200 dot-rose',
  }[status];

  const dotColor = {
    connected: 'bg-emerald-500',
    gated: 'bg-amber-500',
    pending: 'bg-slate-400',
    offline: 'bg-rose-500',
  }[status];

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium border ${styles}`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${dotColor}`} />
      <span>{text}</span>
    </span>
  );
};

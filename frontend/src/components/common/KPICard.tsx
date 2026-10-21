import React, { ReactNode } from 'react';

interface KPICardProps {
  title: string;
  value: string | number;
  unit?: string;
  subtitle?: string;
  stationOrSource?: string;
  timestamp?: string;
  icon: ReactNode;
  iconBgColor?: string;
  badge?: ReactNode;
  isPending?: boolean;
  pendingText?: string;
  observationCount?: number;
  highlightBorder?: string;
}

export const KPICard: React.FC<KPICardProps> = ({
  title,
  value,
  unit,
  subtitle,
  stationOrSource,
  timestamp,
  icon,
  iconBgColor = 'bg-teal-50 text-teal-600 border-teal-100',
  badge,
  isPending = false,
  pendingText = 'Real traffic data pending',
  observationCount,
  highlightBorder,
}) => {
  return (
    <div
      className={`relative bg-white rounded-xl p-5 border border-slate-200 shadow-sm hover:shadow-md transition-all duration-200 flex flex-col justify-between ${
        highlightBorder ? `border-l-4 ${highlightBorder}` : ''
      }`}
    >
      {/* Top Header */}
      <div className="flex items-start justify-between gap-2 mb-3">
        <div>
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            {title}
          </span>
          {subtitle && (
            <p className="text-xs text-slate-400 mt-0.5">{subtitle}</p>
          )}
        </div>
        <div
          className={`p-2.5 rounded-lg border flex-shrink-0 flex items-center justify-center ${iconBgColor}`}
        >
          {icon}
        </div>
      </div>

      {/* Main Value Display */}
      <div className="my-1">
        {isPending ? (
          <div>
            <div className="text-lg font-bold text-amber-700 font-mono tracking-tight">
              {pendingText}
            </div>
            {observationCount !== undefined && (
              <span className="text-xs text-slate-400 mt-1 block">
                Observations in storage: <strong className="text-slate-600 font-mono">{observationCount}</strong> (Gated)
              </span>
            )}
          </div>
        ) : (
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-bold tracking-tight text-slate-900 font-mono">
              {value}
            </span>
            {unit && (
              <span className="text-sm font-medium text-slate-500">{unit}</span>
            )}
          </div>
        )}
      </div>

      {/* Badge & Metadata Footer */}
      <div className="mt-3 pt-3 border-t border-slate-100 flex flex-wrap items-center justify-between gap-2 text-xs">
        {badge ? (
          <div>{badge}</div>
        ) : (
          <div className="text-slate-500 text-[11px] font-medium truncate max-w-[150px]">
            {stationOrSource}
          </div>
        )}

        {timestamp && (
          <span className="text-slate-400 text-[11px] font-mono flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
            {timestamp}
          </span>
        )}
      </div>
    </div>
  );
};

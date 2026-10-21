import React from 'react';
import { AlertTriangle } from 'lucide-react';

interface SyntheticWatermarkProps {
  className?: string;
  size?: 'sm' | 'md' | 'banner';
}

export const SyntheticWatermark: React.FC<SyntheticWatermarkProps> = ({
  className = '',
  size = 'md',
}) => {
  if (size === 'banner') {
    return (
      <div
        className={`w-full bg-amber-500/10 border-2 border-dashed border-amber-500/40 rounded-lg p-3 text-amber-900 flex items-center justify-between gap-3 text-xs md:text-sm font-mono tracking-wide ${className}`}
      >
        <div className="flex items-center gap-2 font-semibold">
          <AlertTriangle className="w-4 h-4 text-amber-600 flex-shrink-0" />
          <span>SYNTHETIC — PIPELINE VALIDATION ONLY</span>
        </div>
        <span className="hidden sm:inline text-xs text-amber-700 font-sans">
          Artificially generated strictly for UI pipeline test harness. Excluded from research findings.
        </span>
      </div>
    );
  }

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] font-mono font-bold tracking-wider uppercase bg-amber-100 text-amber-900 border border-amber-300 shadow-sm ${className}`}
    >
      <AlertTriangle className="w-3 h-3 text-amber-700" />
      <span>SYNTHETIC — PIPELINE VALIDATION ONLY</span>
    </span>
  );
};

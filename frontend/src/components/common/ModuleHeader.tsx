import React, { useState } from 'react';
import { HelpCircle, ChevronDown, ChevronUp, Database, Cpu, Sliders, Info } from 'lucide-react';

export interface ModuleHeaderProps {
  title: string;
  badge?: string;
  tag?: string;
  badgeColor?: string;
  purpose?: string;
  subtitle?: string;
  whatItDoes?: string;
  what?: string;
  dataUsed?: string;
  data?: string;
  outputsGenerated?: string;
  outputs?: string;
  interactions: string;
  actions?: React.ReactNode;
}

export const ModuleHeader: React.FC<ModuleHeaderProps> = ({
  title,
  badge,
  tag,
  badgeColor = 'bg-blue-500/20 text-blue-300 border-blue-500/30',
  purpose,
  subtitle,
  whatItDoes,
  what,
  dataUsed,
  data,
  outputsGenerated,
  outputs,
  interactions,
  actions,
}) => {
  const [detailsOpen, setDetailsOpen] = useState(false);

  const effectiveBadge = badge ?? tag ?? 'Active Module';
  const effectivePurpose = purpose ?? subtitle ?? '';
  const effectiveWhat = whatItDoes ?? what ?? '';
  const effectiveData = dataUsed ?? data ?? '';
  const effectiveOutputs = outputsGenerated ?? outputs ?? '';

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 mb-6 shadow-sm">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2.5 mb-1.5">
            <h1 className="text-2xl font-extrabold text-white tracking-tight">{title}</h1>
            <span className={`text-[11px] font-mono px-2 py-0.5 rounded border ${badgeColor}`}>
              {effectiveBadge}
            </span>
          </div>
          <p className="text-sm text-slate-300 max-w-3xl leading-relaxed">{effectivePurpose}</p>
        </div>

        <div className="flex items-center gap-3 self-start md:self-auto flex-wrap">
          <button
            onClick={() => setDetailsOpen(!detailsOpen)}
            className="text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 px-3 py-1.5 rounded-lg transition-colors flex items-center gap-1.5"
          >
            <HelpCircle className="w-3.5 h-3.5 text-blue-400" />
            <span>Architecture &amp; Data Contract</span>
            {detailsOpen ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>
          {actions}
        </div>
      </div>

      {detailsOpen && (
        <div className="mt-5 pt-4 border-t border-slate-800/80 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 animate-fadeIn text-xs">
          <div className="bg-slate-950/70 border border-slate-800 rounded-xl p-3.5">
            <div className="font-semibold text-blue-400 flex items-center gap-1.5 mb-1">
              <Cpu className="w-3.5 h-3.5" />
              <span>What it does</span>
            </div>
            <p className="text-slate-400 leading-relaxed">{effectiveWhat}</p>
          </div>

          <div className="bg-slate-950/70 border border-slate-800 rounded-xl p-3.5">
            <div className="font-semibold text-cyan-400 flex items-center gap-1.5 mb-1">
              <Database className="w-3.5 h-3.5" />
              <span>Data used</span>
            </div>
            <p className="text-slate-400 leading-relaxed">{effectiveData}</p>
          </div>

          <div className="bg-slate-950/70 border border-slate-800 rounded-xl p-3.5">
            <div className="font-semibold text-emerald-400 flex items-center gap-1.5 mb-1">
              <Info className="w-3.5 h-3.5" />
              <span>Outputs generated</span>
            </div>
            <p className="text-slate-400 leading-relaxed">{effectiveOutputs}</p>
          </div>

          <div className="bg-slate-950/70 border border-slate-800 rounded-xl p-3.5">
            <div className="font-semibold text-amber-400 flex items-center gap-1.5 mb-1">
              <Sliders className="w-3.5 h-3.5" />
              <span>User interactions</span>
            </div>
            <p className="text-slate-400 leading-relaxed">{interactions}</p>
          </div>
        </div>
      )}
    </div>
  );
};
export default ModuleHeader;

import React from 'react';
import { useApp } from '../../context/AppContext';
import { PageId } from '../../types';
import {
  LayoutDashboard,
  Map,
  Wind,
  CloudSun,
  Car,
  SlidersHorizontal,
  TrendingUp,
  GitBranch,
  Database,
  Settings,
  ChevronLeft,
  ChevronRight,
  ShieldCheck,
  X,
} from 'lucide-react';

interface NavItem {
  id: PageId;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  tag?: string;
  tagColor?: string;
}

const NAV_ITEMS: NavItem[] = [
  { id: 'overview', label: 'Overview', icon: LayoutDashboard },
  { id: 'spatial', label: 'Spatial Explorer', icon: Map },
  { id: 'air-quality', label: 'Air Quality', icon: Wind },
  { id: 'weather', label: 'Weather Analytics', icon: CloudSun },
  { id: 'traffic', label: 'Traffic Analytics', icon: Car, tag: 'Gated', tagColor: 'bg-amber-900/60 text-amber-300' },
  { id: 'parameter', label: 'Parameter Analysis', icon: SlidersHorizontal },
  { id: 'forecasting', label: 'Forecasting Lab', icon: TrendingUp },
  { id: 'research', label: 'Research & Causality', icon: GitBranch },
  { id: 'data-quality', label: 'Data Quality & Sources', icon: Database },
  { id: 'settings', label: 'Settings', icon: Settings },
];

export const Sidebar: React.FC = () => {
  const { activePage, setActivePage, sidebarCollapsed, setSidebarCollapsed, mobileNavOpen, setMobileNavOpen } = useApp();

  const handleNavClick = (id: PageId) => {
    setActivePage(id);
    setMobileNavOpen(false);
  };

  return (
    <aside
      className={`fixed inset-y-0 left-0 z-50 flex flex-col bg-slate-900 border-r border-slate-800 text-slate-300 transition-all duration-300 ease-in-out ${
        sidebarCollapsed ? 'lg:w-20' : 'lg:w-64'
      } w-64 ${
        mobileNavOpen ? 'translate-x-0 shadow-2xl' : '-translate-x-full lg:translate-x-0'
      }`}
    >
      {/* Brand Header */}
      <div className="h-16 flex items-center justify-between px-4 border-b border-slate-800/80 bg-slate-950/40">
        <div
          onClick={() => handleNavClick('overview')}
          className="flex items-center gap-3 cursor-pointer overflow-hidden"
        >
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-teal-600 to-teal-400 flex items-center justify-center text-white shadow-md shadow-teal-900/40 flex-shrink-0">
            <Wind className="w-5 h-5 text-white stroke-[2.2]" />
          </div>
          {(!sidebarCollapsed || mobileNavOpen) && (
            <div className="flex flex-col min-w-0">
              <span className="font-bold text-base tracking-tight text-white flex items-center gap-1.5">
                UrbanTwin
                <span className="text-[10px] uppercase font-mono px-1.5 py-0.2 rounded bg-teal-500/20 text-teal-300 border border-teal-500/30">
                  v2.0
                </span>
              </span>
              <span className="text-[10px] text-slate-400 truncate tracking-wide">
                Pune &amp; PCMC Twin
              </span>
            </div>
          )}
        </div>

        {/* Mobile Close Button */}
        <button
          onClick={() => setMobileNavOpen(false)}
          className="lg:hidden p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          aria-label="Close menu"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Desktop Collapse Toggle */}
        <button
          onClick={() => setSidebarCollapsed((prev) => !prev)}
          className="hidden lg:flex w-7 h-7 rounded-lg items-center justify-center text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          title={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {sidebarCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>
      </div>

      {/* Navigation List */}
      <div className="flex-1 overflow-y-auto py-4 px-3 space-y-1">
        {!sidebarCollapsed && (
          <div className="px-3 pb-2 text-[10px] font-mono uppercase tracking-wider text-slate-400 font-semibold">
            Intelligence Modules
          </div>
        )}
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const isActive = activePage === item.id;

          return (
            <button
              key={item.id}
              onClick={() => handleNavClick(item.id)}
              title={sidebarCollapsed ? item.label : undefined}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 group relative ${
                isActive
                  ? 'bg-teal-600 text-white shadow-sm shadow-teal-950 font-semibold'
                  : 'text-slate-300 hover:text-white hover:bg-slate-800/70'
              }`}
            >
              <Icon
                className={`w-5 h-5 flex-shrink-0 transition-colors ${
                  isActive ? 'text-white' : 'text-slate-400 group-hover:text-slate-200'
                }`}
              />

              {!sidebarCollapsed && (
                <div className="flex items-center justify-between flex-1 truncate">
                  <span className="truncate">{item.label}</span>
                  {item.tag && (
                    <span
                      className={`text-[10px] font-mono px-1.5 py-0.5 rounded ${
                        item.tagColor || 'bg-slate-800 text-slate-300'
                      }`}
                    >
                      {item.tag}
                    </span>
                  )}
                </div>
              )}

              {/* Collapsed Tooltip Pill */}
              {sidebarCollapsed && (
                <div className="absolute left-full ml-3 px-2.5 py-1 bg-slate-950 text-white text-xs rounded-md shadow-xl border border-slate-700 whitespace-nowrap opacity-0 pointer-events-none group-hover:opacity-100 transition-opacity z-50">
                  {item.label}
                  {item.tag && ` (${item.tag})`}
                </div>
              )}
            </button>
          );
        })}
      </div>

      {/* Research Compliance & Sufficiency Status in Sidebar */}
      {!sidebarCollapsed ? (
        <div className="p-3 m-3 rounded-xl bg-slate-950/60 border border-slate-800 text-xs space-y-2">
          <div className="flex items-center justify-between text-[11px] font-semibold text-slate-300 border-b border-slate-800/80 pb-1.5">
            <span className="flex items-center gap-1.5">
              <ShieldCheck className="w-3.5 h-3.5 text-teal-400" />
              <span>Pipeline Integrity</span>
            </span>
            <span className="text-[10px] font-mono text-emerald-400">Strict QA</span>
          </div>

          <div className="space-y-1 text-[11px] text-slate-400">
            <div className="flex items-center justify-between">
              <span>OpenAQ Air:</span>
              <span className="text-emerald-400 font-mono font-medium">5 Stations (OK)</span>
            </div>
            <div className="flex items-center justify-between">
              <span>Open-Meteo:</span>
              <span className="text-emerald-400 font-mono font-medium">ERA5 Synced</span>
            </div>
            <div className="flex items-center justify-between">
              <span>TomTom Flow:</span>
              <span className="text-amber-400 font-mono font-medium">Gated (0.2/8 wks)</span>
            </div>
          </div>
        </div>
      ) : (
        <div className="p-3 flex justify-center border-t border-slate-800">
          <div
            className="w-3 h-3 rounded-full bg-amber-500 animate-pulse"
            title="Traffic Gate: Awaiting observations"
          />
        </div>
      )}
    </aside>
  );
};

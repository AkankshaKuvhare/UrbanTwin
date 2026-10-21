import React from 'react';
import { useApp } from '../../context/AppContext';
import { StudyArea, DateRangePreset } from '../../types';
import {
  Menu,
  RotateCw,
  Calendar,
  MapPin,
  Clock,
} from 'lucide-react';

const PAGE_TITLES: Record<string, { title: string; category: string }> = {
  overview: { title: 'Overview Dashboard', category: 'Executive Summary' },
  spatial: { title: 'Spatial Explorer', category: 'Geospatial Analytics' },
  'air-quality': { title: 'Air Quality Dynamics', category: 'Atmospheric Chemistry' },
  weather: { title: 'Weather & Meteorology', category: 'Covariate Analysis' },
  traffic: { title: 'Traffic Flow & Congestion', category: 'Arterial Mobility' },
  parameter: { title: 'Parameter Analysis & Correlation', category: 'Statistical Inference' },
  forecasting: { title: 'Forecasting Lab', category: 'Predictive Modeling' },
  research: { title: 'Research & Causality Precedence', category: 'Econometric Diagnostics' },
  'data-quality': { title: 'Data Quality & Provenance', category: 'Audit & Governance' },
  settings: { title: 'Configuration & Settings', category: 'System Parameters' },
};

export const Header: React.FC = () => {
  const {
    activePage,
    studyArea,
    setStudyArea,
    dateRange,
    setDateRange,
    isRefreshing,
    triggerRefresh,
    lastUpdated,
    sidebarCollapsed,
    mobileNavOpen,
    setMobileNavOpen,
  } = useApp();

  const currentInfo = PAGE_TITLES[activePage] || {
    title: 'Analytics Dashboard',
    category: 'UrbanTwin',
  };

  return (
    <header
      className={`sticky top-0 z-30 bg-white/90 backdrop-blur-md border-b border-slate-200/80 transition-all duration-300 ${
        sidebarCollapsed ? 'lg:pl-20' : 'lg:pl-64'
      }`}
    >
      <div className="px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-4">
        {/* Left: Mobile Menu Toggle & Breadcrumb */}
        <div className="flex items-center gap-3 min-w-0">
          <button
            onClick={() => setMobileNavOpen(!mobileNavOpen)}
            className="lg:hidden p-2 rounded-lg text-slate-600 hover:text-slate-900 hover:bg-slate-100 focus:outline-none"
            aria-label="Toggle navigation menu"
          >
            <Menu className="w-5 h-5" />
          </button>

          <div className="min-w-0">
            <div className="flex items-center gap-1.5 text-xs text-slate-400 font-medium">
              <span>CongestAir</span>
              <span>/</span>
              <span className="text-teal-700 font-medium">{currentInfo.category}</span>
            </div>
            <h1 className="text-base sm:text-lg font-bold text-slate-900 truncate tracking-tight">
              {currentInfo.title}
            </h1>
          </div>
        </div>

        {/* Right: Study Area Selector, Date Selector, Data Status, Refresh */}
        <div className="flex items-center gap-2 sm:gap-3 flex-shrink-0">
          {/* Study Area Dropdown */}
          <div className="relative hidden md:flex items-center">
            <MapPin className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 pointer-events-none" />
            <select
              value={studyArea}
              onChange={(e) => setStudyArea(e.target.value as StudyArea)}
              className="pl-8 pr-7 py-1.5 text-xs font-semibold bg-slate-50 border border-slate-200 rounded-lg text-slate-700 hover:border-slate-300 focus:outline-none focus:ring-1 focus:ring-teal-500 cursor-pointer transition-colors"
            >
              <option value="combined">Pune & PCMC (Combined)</option>
              <option value="pune">Pune Municipal Corp (PMC)</option>
              <option value="pcmc">Pimpri-Chinchwad (PCMC)</option>
            </select>
          </div>

          {/* Date Range Selector */}
          <div className="relative hidden sm:flex items-center">
            <Calendar className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 pointer-events-none" />
            <select
              value={dateRange}
              onChange={(e) => setDateRange(e.target.value as DateRangePreset)}
              className="pl-8 pr-7 py-1.5 text-xs font-medium bg-slate-50 border border-slate-200 rounded-lg text-slate-700 hover:border-slate-300 focus:outline-none focus:ring-1 focus:ring-teal-500 cursor-pointer transition-colors"
            >
              <option value="7d">Last 7 Days (Recent High-Res)</option>
              <option value="30d">Last 30 Days (Analysis Standard)</option>
              <option value="8w">Last 8 Weeks (Traffic Gate Window)</option>
              <option value="post-monsoon">Season: Post-Monsoon (Oct-Nov)</option>
              <option value="winter">Season: Winter Inversion (Dec-Feb)</option>
              <option value="monsoon">Season: SW Monsoon (Jun-Sep)</option>
            </select>
          </div>

          {/* Last Updated Timestamp & Status Indicator */}
          <div className="hidden xl:flex items-center gap-2 px-2.5 py-1 rounded-lg bg-slate-50 border border-slate-200 text-xs text-slate-600">
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span className="font-medium text-slate-700">Real Feeds Active</span>
            </div>
            <span className="text-slate-300">|</span>
            <div className="flex items-center gap-1 text-[11px] text-slate-500 font-mono">
              <Clock className="w-3 h-3 text-slate-400" />
              <span>{lastUpdated}</span>
            </div>
          </div>

          {/* Refresh Action Button */}
          <button
            onClick={triggerRefresh}
            disabled={isRefreshing}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg border transition-all ${
              isRefreshing
                ? 'bg-teal-50 text-teal-700 border-teal-200 cursor-wait'
                : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-50 hover:border-slate-300 shadow-sm active:bg-slate-100'
            }`}
            title="Poll real data feeds now"
          >
            <RotateCw
              className={`w-3.5 h-3.5 ${
                isRefreshing ? 'animate-spin text-teal-600' : 'text-slate-500'
              }`}
            />
            <span className="hidden sm:inline">
              {isRefreshing ? 'Refreshing...' : 'Refresh'}
            </span>
          </button>
        </div>
      </div>
    </header>
  );
};

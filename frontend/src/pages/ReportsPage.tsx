import React, { useState } from 'react';
import { ModuleHeader } from '../components/common/ModuleHeader';
import { KPICard } from '../components/common/KPICard';
import {
  FileText,
  Download,
  Search,
  ExternalLink,
  Filter,
  CheckCircle2,
  FileSpreadsheet,
  Image,
  Code,
  Layers,
} from 'lucide-react';

interface ReportItem {
  id: string;
  name: string;
  filename: string;
  category: 'Validation' | 'EDA' | 'Forecasting' | 'Relationships' | 'GIS' | 'Simulator';
  format: 'HTML' | 'CSV' | 'PNG' | 'JSON' | 'GeoJSON';
  size: string;
  description: string;
  url: string;
}

const REPORT_REGISTRY: ReportItem[] = [
  // Validation
  { id: 'val-1', name: 'System E2E Validation Report', filename: 'validation_report.html', category: 'Validation', format: 'HTML', size: '24 KB', description: 'Complete 12-stage automated pipeline validation results (Health: 97/100).', url: '/reports/validation_report.html' },
  { id: 'val-2', name: 'Data Quality Summary', filename: 'data_quality_summary.json', category: 'Validation', format: 'JSON', size: '3.4 KB', description: 'Completeness rates, missing values, duplicates, and outlier counts.', url: '/reports/data_quality_summary.json' },

  // EDA
  { id: 'eda-1', name: 'Exploratory Data Analysis Report', filename: 'eda_report.html', category: 'EDA', format: 'HTML', size: '1.2 MB', description: 'Comprehensive distributions, diurnal rhythms, and pollutant cross-correlations.', url: '/reports/eda_report.html' },
  { id: 'eda-2', name: 'EDA Statistics Summary', filename: 'eda_summary.csv', category: 'EDA', format: 'CSV', size: '12.8 KB', description: 'Summary statistics (mean, std, percentiles) for all Pune sensors.', url: '/reports/eda_summary.csv' },

  // Relationships
  { id: 'rel-1', name: 'Relationship Analytics Report', filename: 'relationship_report.html', category: 'Relationships', format: 'HTML', size: '1.6 MB', description: 'Pearson/Spearman/Kendall correlation matrices and NetworkX dependency graphs.', url: '/reports/relationships/relationship_report.html' },
  { id: 'rel-2', name: 'Correlation Matrix Table', filename: 'correlation_matrix.csv', category: 'Relationships', format: 'CSV', size: '4.2 KB', description: 'Full NxN pairwise correlation coefficients between AQI, weather, and traffic.', url: '/reports/relationships/correlation_matrix.csv' },
  { id: 'rel-3', name: 'Network Graph Edges', filename: 'network_edges.csv', category: 'Relationships', format: 'CSV', size: '2.1 KB', description: 'Weighted edges and centrality scores for force-directed interaction graph.', url: '/reports/relationships/network_edges.csv' },

  // Forecasting
  { id: 'fc-1', name: 'Forecasting Model Leaderboard', filename: 'forecast_leaderboard.html', category: 'Forecasting', format: 'HTML', size: '820 KB', description: 'Model comparison: Random Forest, LightGBM, XGBoost, and Linear Regression with Rolling CV.', url: '/reports/forecast_leaderboard.html' },
  { id: 'fc-2', name: 'Model Evaluation Metrics', filename: 'model_metrics.csv', category: 'Forecasting', format: 'CSV', size: '3.1 KB', description: 'MAE, RMSE, R², and MAPE performance across cross-validation folds.', url: '/reports/model_metrics.csv' },

  // GIS
  { id: 'gis-1', name: 'Digital Twin Interactive Map', filename: 'pune_digital_twin_map.html', category: 'GIS', format: 'HTML', size: '183 KB', description: 'Multi-layer Folium map with H3 Resolution 7 cells, stations, and traffic points.', url: '/dashboard/map/static' },
  { id: 'gis-2', name: 'H3 Zones GeoJSON', filename: 'h3_zones.geojson', category: 'GIS', format: 'GeoJSON', size: '295 KB', description: '251 Hexagonal cell boundaries with mean AQI attribute bindings.', url: '/reports/gis/h3_zones.geojson' },
  { id: 'gis-3', name: 'Monitoring Stations GeoJSON', filename: 'stations.geojson', category: 'GIS', format: 'GeoJSON', size: '3.1 KB', description: 'Point geometries and pollutant attributes for 5 Pune CAAQMS stations.', url: '/reports/gis/stations.geojson' },
  { id: 'gis-4', name: 'Traffic Points GeoJSON', filename: 'traffic_points.geojson', category: 'GIS', format: 'GeoJSON', size: '27.7 KB', description: '40 TomTom arterial monitoring coordinates and speeds.', url: '/reports/gis/traffic_points.geojson' },
  { id: 'gis-5', name: 'Digital Twin Static Snapshot', filename: 'pune_digital_twin_map.png', category: 'GIS', format: 'PNG', size: '523 KB', description: 'Publication-quality 200 DPI static snapshot of the Pune air quality digital twin.', url: '/reports/gis/pune_digital_twin_map.png' },

  // Simulator
  { id: 'sim-1', name: 'Scenario Simulation Report', filename: 'simulation_report.html', category: 'Simulator', format: 'HTML', size: '8.0 KB', description: 'Sensitivity analysis across 8 what-if policy and environmental presets.', url: '/reports/simulator/simulation_report.html' },
  { id: 'sim-2', name: 'Scenario Results Table', filename: 'scenario_results.csv', category: 'Simulator', format: 'CSV', size: '1.5 KB', description: 'Predicted AQI, sub-pollutants, confidence, and delta % across all presets.', url: '/reports/simulator/scenario_results.csv' },
  { id: 'sim-3', name: 'Scenario Comparison Chart', filename: 'scenario_comparison.png', category: 'Simulator', format: 'PNG', size: '95 KB', description: 'Horizontal comparison chart of AQI predictions against baseline.', url: '/reports/simulator/scenario_comparison.png' },
];

export const ReportsPage: React.FC = () => {
  const [search, setSearch] = useState('');
  const [selectedFormat, setSelectedFormat] = useState<string>('all');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');

  const filtered = REPORT_REGISTRY.filter(r => {
    const matchSearch = r.name.toLowerCase().includes(search.toLowerCase()) || r.description.toLowerCase().includes(search.toLowerCase()) || r.filename.toLowerCase().includes(search.toLowerCase());
    const matchFormat = selectedFormat === 'all' || r.format === selectedFormat;
    const matchCat = selectedCategory === 'all' || r.category === selectedCategory;
    return matchSearch && matchFormat && matchCat;
  });

  const getFormatBadge = (fmt: string) => {
    switch (fmt) {
      case 'HTML': return 'bg-blue-500/10 text-blue-400 border-blue-500/30';
      case 'CSV': return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
      case 'PNG': return 'bg-purple-500/10 text-purple-400 border-purple-500/30';
      case 'JSON':
      case 'GeoJSON': return 'bg-amber-500/10 text-amber-400 border-amber-500/30';
      default: return 'bg-slate-800 text-slate-400 border-slate-700';
    }
  };

  return (
    <div className="space-y-6 animate-fadeIn">
      <ModuleHeader
        title="Reports &amp; Artifacts Repository"
        badge="Central Repository"
        badgeColor="bg-emerald-500/20 text-emerald-300 border-emerald-500/30"
        purpose="Unified distribution catalog collecting every generated report, publication-quality chart, serialized data table, and GeoJSON artifact produced across UrbanTwin milestones."
        whatItDoes="Catalogs and serves analytical artifacts (HTML dashboards, CSV matrices, GeoJSON boundaries, and 200 DPI PNG figures) with live preview and direct download capabilities."
        dataUsed="Output artifacts generated in reports/, reports/relationships/, reports/gis/, and reports/simulator/."
        outputsGenerated="Direct access to 16 verified report artifacts covering Validation, EDA, Forecasting, Relationships, GIS, and Simulation."
        interactions="Search artifacts by keyword, filter by category or file format, preview HTML reports in new tab, and download raw CSV/JSON/GeoJSON files."
      />

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <KPICard
          title="Total Artifacts"
          value={REPORT_REGISTRY.length.toString()}
          subtitle="Generated &amp; Verified"
          status="good"
          icon={<FileText className="w-4 h-4 text-emerald-400" />}
        />
        <KPICard
          title="HTML Reports"
          value={REPORT_REGISTRY.filter(r => r.format === 'HTML').length.toString()}
          subtitle="Standalone Interactive"
          status="good"
          icon={<ExternalLink className="w-4 h-4 text-blue-400" />}
        />
        <KPICard
          title="Tabular CSVs"
          value={REPORT_REGISTRY.filter(r => r.format === 'CSV').length.toString()}
          subtitle="Direct Data Ingestion"
          status="good"
          icon={<FileSpreadsheet className="w-4 h-4 text-teal-400" />}
        />
        <KPICard
          title="Spatial GeoJSON"
          value={REPORT_REGISTRY.filter(r => r.format === 'GeoJSON').length.toString()}
          subtitle="GIS Layer Assets"
          status="good"
          icon={<Layers className="w-4 h-4 text-purple-400" />}
        />
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="relative w-full md:w-80">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search reports by title, keyword, filename..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-slate-950 border border-slate-700 text-white rounded-lg pl-9 pr-3 py-1.5 text-xs focus:outline-none focus:border-blue-500"
          />
        </div>

        <div className="flex items-center gap-2 flex-wrap w-full md:w-auto text-xs">
          <span className="text-slate-400">Category:</span>
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="bg-slate-950 border border-slate-700 text-white rounded-lg px-2.5 py-1.5 focus:outline-none"
          >
            <option value="all">All Categories</option>
            <option value="Validation">Validation</option>
            <option value="EDA">EDA</option>
            <option value="Forecasting">Forecasting</option>
            <option value="Relationships">Relationships</option>
            <option value="GIS">GIS</option>
            <option value="Simulator">Simulator</option>
          </select>

          <span className="text-slate-400 ml-2">Format:</span>
          <select
            value={selectedFormat}
            onChange={(e) => setSelectedFormat(e.target.value)}
            className="bg-slate-950 border border-slate-700 text-white rounded-lg px-2.5 py-1.5 focus:outline-none"
          >
            <option value="all">All Formats</option>
            <option value="HTML">HTML</option>
            <option value="CSV">CSV</option>
            <option value="PNG">PNG</option>
            <option value="JSON">JSON</option>
            <option value="GeoJSON">GeoJSON</option>
          </select>
        </div>
      </div>

      {/* Report Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filtered.map((item) => (
          <div key={item.id} className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex flex-col justify-between hover:border-slate-700 transition">
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className={`text-[10px] font-mono px-2 py-0.5 rounded border ${getFormatBadge(item.format)}`}>
                  {item.format}
                </span>
                <span className="text-[10px] text-slate-500 font-mono">{item.size}</span>
              </div>

              <h3 className="font-bold text-white text-sm leading-snug mb-1">{item.name}</h3>
              <div className="text-[11px] font-mono text-slate-400 mb-2 truncate" title={item.filename}>{item.filename}</div>
              <p className="text-xs text-slate-300 leading-relaxed mb-4">{item.description}</p>
            </div>

            <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between">
              <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider">{item.category}</span>
              <div className="flex gap-2">
                <a
                  href={item.url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-xs bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 px-2.5 py-1 rounded transition flex items-center gap-1"
                >
                  <ExternalLink className="w-3 h-3 text-blue-400" />
                  <span>Preview</span>
                </a>
                <a
                  href={item.url}
                  download={item.filename}
                  className="text-xs bg-blue-600 hover:bg-blue-500 text-white font-medium px-2.5 py-1 rounded transition flex items-center gap-1 shadow-sm"
                >
                  <Download className="w-3 h-3" />
                  <span>Download</span>
                </a>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

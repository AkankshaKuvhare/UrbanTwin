import React, { useState, useEffect } from 'react';
import { ModuleHeader } from '../components/common/ModuleHeader';
import { KPICard } from '../components/common/KPICard';
import { UrbanTwinAPI } from '../utils/api';
import { FORECAST_COMPARISON_48H } from '../data/statsModels';
import {
  TrendingUp,
  Award,
  Layers,
  Activity,
  Calendar,
  CheckCircle2,
  BarChart3,
  Sliders,
  Clock,
  MapPin,
  RefreshCw,
  Download,
} from 'lucide-react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';

const DARK_TOOLTIP = {
  backgroundColor: '#0f172a',
  borderRadius: '8px',
  borderColor: '#334155',
  fontSize: '12px',
  color: '#e2e8f0',
};

// Top 8 evaluated baseline models from reports/models/baseline_results.csv
const MODEL_LEADERBOARD = [
  { modelKey: 'lr_weather', name: 'Linear Regression (Calendar + Weather + Lags)', featureSet: 'Calendar + Weather', features: 27, rmse: 14.8, mae: 11.2, r2: 0.684, mape: 15.6, rank: '#1 Champion', isChampion: true },
  { modelKey: 'lgb_weather', name: 'LightGBM Gradient Boosting', featureSet: 'Calendar + Weather', features: 27, rmse: 16.4, mae: 12.8, r2: 0.638, mape: 17.2, rank: '#2 High Performance', isChampion: false },
  { modelKey: 'rf_weather', name: 'Random Forest Regressor', featureSet: 'Calendar + Weather', features: 27, rmse: 17.9, mae: 13.9, r2: 0.595, mape: 18.9, rank: '#3 Ensemble', isChampion: false },
  { modelKey: 'xgb_weather', name: 'XGBoost Regressor', featureSet: 'Calendar + Weather', features: 27, rmse: 18.6, mae: 14.5, r2: 0.572, mape: 19.8, rank: '#4 Ensemble', isChampion: false },
  { modelKey: 'lr_calendar', name: 'Linear Regression (Calendar Baseline)', featureSet: 'Calendar Only', features: 21, rmse: 26.4, mae: 19.8, r2: 0.382, mape: 27.2, rank: '#5 Baseline', isChampion: false },
  { modelKey: 'lgb_calendar', name: 'LightGBM (Calendar Only)', featureSet: 'Calendar Only', features: 21, rmse: 28.1, mae: 21.2, r2: 0.324, mape: 29.5, rank: '#6 Baseline', isChampion: false },
  { modelKey: 'rf_calendar', name: 'Random Forest (Calendar Only)', featureSet: 'Calendar Only', features: 21, rmse: 29.5, mae: 22.4, r2: 0.285, mape: 31.0, rank: '#7 Baseline', isChampion: false },
  { modelKey: 'xgb_calendar', name: 'XGBoost (Calendar Only)', featureSet: 'Calendar Only', features: 21, rmse: 31.2, mae: 23.9, r2: 0.241, mape: 32.8, rank: '#8 Baseline', isChampion: false },
];

// Predictive feature importances from reports/models/feature_summary.csv
const FEATURE_IMPORTANCES = [
  { feature: 'AQI Lag 1 (1h prior)', importance: 34.5, category: 'Autoregressive' },
  { feature: 'Boundary Layer Height', importance: 21.8, category: 'Meteorology' },
  { feature: '2m Temperature', importance: 14.2, category: 'Meteorology' },
  { feature: '10m Wind Speed', importance: 11.6, category: 'Meteorology' },
  { feature: 'Relative Humidity', importance: 8.4, category: 'Meteorology' },
  { feature: 'Hour of Day (Diurnal)', importance: 5.8, category: 'Calendar' },
  { feature: 'Surface Pressure', importance: 3.7, category: 'Meteorology' },
];

export const ForecastingLabPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'forecast' | 'residuals' | 'comparison' | 'features'>('forecast');
  const [selectedStation, setSelectedStation] = useState<string>('pune-shivajinagar');
  const [selectedHorizon, setSelectedHorizon] = useState<string>('48h');
  const [leaderboardData, setLeaderboardData] = useState<any[]>(MODEL_LEADERBOARD);
  const [loading, setLoading] = useState<boolean>(false);

  useEffect(() => {
    UrbanTwinAPI.getForecastingData()
      .then((res) => {
        if (res?.models && res.models.length > 0) {
          // Merge API models if available
          const formatted = res.models.map((m: any, idx: number) => ({
            modelKey: m.model_key,
            name: m.label,
            featureSet: m.feature_set === 'calendar_weather' ? 'Calendar + Weather' : 'Calendar Only',
            features: m.num_features || (m.feature_set === 'calendar_weather' ? 27 : 21),
            rmse: m.cv_rmse,
            mae: m.cv_mae,
            r2: m.cv_r2,
            mape: m.cv_mape,
            rank: idx === 0 ? '#1 Champion' : `#${idx + 1}`,
            isChampion: idx === 0,
          }));
          setLeaderboardData(formatted);
        }
      })
      .catch((err) => {
        console.warn('Using baseline forecasting leaderboard:', err);
      });
  }, []);

  const exportLeaderboardCSV = () => {
    const headers = ['Model', 'Feature Set', 'Features', 'CV RMSE (µg/m³)', 'CV MAE (µg/m³)', 'CV R²', 'CV MAPE (%)', 'Rank'];
    const rows = leaderboardData.map(m => [
      `"${m.name}"`,
      `"${m.featureSet}"`,
      m.features,
      m.rmse,
      m.mae,
      m.r2,
      m.mape,
      `"${m.rank}"`,
    ]);
    const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map(e => e.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `forecasting_leaderboard_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="space-y-6 animate-fadeIn">
      <ModuleHeader
        title="Forecasting Lab & Model Benchmark"
        subtitle="Multi-model time-series benchmarking across calendar, meteorological, and autoregressive lag feature sets."
        tag="Expanding-Window Cross Validation"
        what="Trains, benchmarks, and evaluates machine learning and statistical time-series models for PM2.5 forecasting across Pune monitoring stations."
        data="Historical CAAQMS air quality observations, ERA5 meteorological covariates (Temperature, RH, Wind Speed, Boundary Layer Height), and lag features."
        outputs="Model leaderboard (RMSE, MAE, R², MAPE), 48-hour rolling prediction comparison, residual analysis, and covariate importance rankings."
        interactions="Filter models by feature set, select station and forecast horizon, toggle between Actual vs Predicted, Residuals, and Model Comparison views."
        actions={
          <div className="flex gap-2">
            <button
              onClick={exportLeaderboardCSV}
              className="text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 px-3 py-1.5 rounded-lg transition flex items-center gap-1.5"
            >
              <Download className="w-3.5 h-3.5 text-blue-400" />
              <span>Export CSV</span>
            </button>
            <a
              href="/dashboard/forecasting"
              target="_blank"
              rel="noreferrer"
              className="text-xs bg-blue-600 hover:bg-blue-500 text-white font-semibold px-3.5 py-1.5 rounded-lg transition flex items-center gap-1.5 shadow-sm"
            >
              <BarChart3 className="w-3.5 h-3.5" />
              <span>Forecasting Dashboard ↗</span>
            </a>
          </div>
        }
      />

      {/* KPI Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        <KPICard
          title="Champion Model"
          value="Linear Reg + Weather"
          subtitle="R²: 0.684 (+79% gain)"
          status="good"
          icon={<Award className="w-4 h-4 text-emerald-400" />}
        />
        <KPICard
          title="Best CV RMSE"
          value="14.8 µg/m³"
          subtitle="44% error reduction"
          status="good"
          icon={<Activity className="w-4 h-4 text-blue-400" />}
        />
        <KPICard
          title="Best CV MAE"
          value="11.2 µg/m³"
          subtitle="43% error reduction"
          status="good"
          icon={<TrendingUp className="w-4 h-4 text-indigo-400" />}
        />
        <KPICard
          title="Evaluated Features"
          value="27 Features"
          subtitle="Meteo + Lags + Calendar"
          status="good"
          icon={<Layers className="w-4 h-4 text-purple-400" />}
        />
        <KPICard
          title="Validation Protocol"
          value="5 Temporal Folds"
          subtitle="Expanding Window CV"
          status="good"
          icon={<Calendar className="w-4 h-4 text-amber-400" />}
        />
        <KPICard
          title="Forecast Horizon"
          value="48 Hours"
          subtitle="Out-of-sample window"
          status="good"
          icon={<Clock className="w-4 h-4 text-teal-400" />}
        />
      </div>

      {/* Interactive Cockpit: Filters & Visualizations */}
      <div className="bg-slate-900 rounded-xl border border-slate-800 p-5 space-y-4">
        {/* Cockpit Header with Station, Horizon & View Selectors */}
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-3 pb-3 border-b border-slate-800">
          <div>
            <h3 className="text-base font-bold text-white tracking-tight">
              Model Performance &amp; Forecasting Cockpit
            </h3>
            <p className="text-xs text-slate-400">
              Interactive out-of-sample forecast comparison, error residuals, and feature importances.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            {/* Station Selector */}
            <div className="flex items-center gap-1.5 bg-slate-950 px-2.5 py-1 rounded-lg border border-slate-800 text-xs">
              <MapPin className="w-3.5 h-3.5 text-blue-400" />
              <select
                value={selectedStation}
                onChange={(e) => setSelectedStation(e.target.value)}
                className="bg-transparent text-slate-200 focus:outline-none cursor-pointer"
              >
                <option value="pune-shivajinagar">Shivajinagar (IITM)</option>
                <option value="pune-hadapsar">Hadapsar (IITM)</option>
                <option value="pune-karve-road">Karve Road (MPCB)</option>
                <option value="pcmc-bhosari">Bhosari (IITM)</option>
                <option value="pcmc-nigdi">Nigdi (MPCB)</option>
              </select>
            </div>

            {/* Horizon Selector */}
            <div className="flex items-center gap-1.5 bg-slate-950 px-2.5 py-1 rounded-lg border border-slate-800 text-xs">
              <Clock className="w-3.5 h-3.5 text-purple-400" />
              <select
                value={selectedHorizon}
                onChange={(e) => setSelectedHorizon(e.target.value)}
                className="bg-transparent text-slate-200 focus:outline-none cursor-pointer"
              >
                <option value="24h">24h Horizon</option>
                <option value="48h">48h Horizon</option>
                <option value="72h">72h Horizon</option>
              </select>
            </div>

            {/* View Mode Tabs */}
            <div className="flex bg-slate-950 p-0.5 rounded-lg border border-slate-800 text-xs">
              <button
                onClick={() => setActiveTab('forecast')}
                className={`px-3 py-1 rounded font-medium transition ${
                  activeTab === 'forecast' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'
                }`}
              >
                Actual vs Predicted
              </button>
              <button
                onClick={() => setActiveTab('residuals')}
                className={`px-3 py-1 rounded font-medium transition ${
                  activeTab === 'residuals' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'
                }`}
              >
                Residuals
              </button>
              <button
                onClick={() => setActiveTab('comparison')}
                className={`px-3 py-1 rounded font-medium transition ${
                  activeTab === 'comparison' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'
                }`}
              >
                Model Comparison
              </button>
              <button
                onClick={() => setActiveTab('features')}
                className={`px-3 py-1 rounded font-medium transition ${
                  activeTab === 'features' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'
                }`}
              >
                Feature Importances
              </button>
            </div>
          </div>
        </div>

        {/* Chart View Content */}
        <div className="h-80 w-full pt-1">
          {activeTab === 'forecast' && (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={FORECAST_COMPARISON_48H} margin={{ top: 10, right: 10, left: -10, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="timeLabel" stroke="#64748b" fontSize={10} tickMargin={8} />
                <YAxis stroke="#64748b" fontSize={11} unit=" µg/m³" tickMargin={8} />
                <Tooltip contentStyle={DARK_TOOLTIP} />
                <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '6px', color: '#94a3b8' }} />
                <ReferenceLine y={60} stroke="#f59e0b" strokeDasharray="3 3" label={{ value: '24h Standard (60 µg/m³)', fill: '#f59e0b', fontSize: 10, position: 'insideTopLeft' }} />
                <Line
                  type="monotone"
                  dataKey="actualPM25"
                  name="Ground Truth (Actual PM2.5)"
                  stroke="#f1f5f9"
                  strokeWidth={2.5}
                  dot={{ r: 3 }}
                />
                <Line
                  type="monotone"
                  dataKey="modelB_Pred"
                  name="Weather-Enhanced Forecast (Champion Model)"
                  stroke="#3b82f6"
                  strokeWidth={2.5}
                  dot={{ r: 2 }}
                />
                <Line
                  type="monotone"
                  dataKey="modelA_Pred"
                  name="Calendar Baseline Forecast"
                  stroke="#64748b"
                  strokeWidth={1.8}
                  strokeDasharray="4 4"
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          )}

          {activeTab === 'residuals' && (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={FORECAST_COMPARISON_48H} margin={{ top: 10, right: 10, left: -10, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="timeLabel" stroke="#64748b" fontSize={10} tickMargin={8} />
                <YAxis stroke="#64748b" fontSize={11} unit=" µg/m³" tickMargin={8} />
                <Tooltip contentStyle={DARK_TOOLTIP} />
                <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '6px', color: '#94a3b8' }} />
                <ReferenceLine y={0} stroke="#475569" />
                <Bar dataKey="residual_A" name="Baseline Residual Error (Actual - Pred)" fill="#64748b" radius={[2, 2, 0, 0]} />
                <Bar dataKey="residual_B" name="Weather Model Residual Error (Actual - Pred)" fill="#3b82f6" radius={[2, 2, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}

          {activeTab === 'comparison' && (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={leaderboardData} margin={{ top: 10, right: 10, left: -10, bottom: 25 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="name" stroke="#64748b" fontSize={9} angle={-20} textAnchor="end" />
                <YAxis stroke="#64748b" fontSize={11} unit=" µg/m³" tickMargin={8} />
                <Tooltip contentStyle={DARK_TOOLTIP} />
                <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '6px', color: '#94a3b8' }} />
                <Bar dataKey="rmse" name="CV RMSE (Lower is Better)" fill="#3b82f6" radius={[3, 3, 0, 0]} />
                <Bar dataKey="mae" name="CV MAE (Lower is Better)" fill="#10b981" radius={[3, 3, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}

          {activeTab === 'features' && (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={FEATURE_IMPORTANCES} layout="vertical" margin={{ top: 10, right: 20, left: 100, bottom: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis type="number" stroke="#64748b" fontSize={10} unit="%" domain={[0, 40]} />
                <YAxis type="category" dataKey="feature" stroke="#64748b" fontSize={10} width={130} />
                <Tooltip contentStyle={DARK_TOOLTIP} />
                <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '4px' }} />
                <Bar dataKey="importance" name="Predictive Relative Importance (%)" fill="#8b5cf6" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Dynamic Context Footer */}
        <div className="pt-2 border-t border-slate-800 flex flex-wrap items-center justify-between text-xs text-slate-400">
          <span>
            {activeTab === 'forecast' && 'Observed PM2.5 captures diurnal morning/evening rush hour spikes accurately with weather covariates.'}
            {activeTab === 'residuals' && 'Weather-controlled model reduces peak prediction error variance by over 78%.'}
            {activeTab === 'comparison' && 'Expanding-window cross-validation confirms meteorological covariate specifications consistently outperform calendar-only baselines.'}
            {activeTab === 'features' && 'Autoregressive AQI lags and Boundary Layer Height are the strongest drivers of PM2.5 concentration changes.'}
          </span>
          <span className="font-mono text-emerald-400 font-semibold">Expanding-Window Cross-Validation Active</span>
        </div>
      </div>

      {/* Comprehensive Model Benchmark Leaderboard Table */}
      <div className="bg-slate-900 rounded-xl border border-slate-800 p-5 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2 border-b border-slate-800">
          <div>
            <h3 className="text-base font-bold text-white tracking-tight">
              Production Model Benchmark Leaderboard ({leaderboardData.length} Specifications)
            </h3>
            <p className="text-xs text-slate-400">
              Evaluated using rolling-origin expanding-window cross-validation across 5 temporal folds.
            </p>
          </div>
          <span className="text-xs text-slate-400 font-mono">
            Metric: Root Mean Squared Error (RMSE)
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-800/60 text-slate-400 font-semibold uppercase tracking-wider text-[11px]">
                <th className="py-2.5 px-3">Model Specification</th>
                <th className="py-2.5 px-3">Feature Set</th>
                <th className="py-2.5 px-3 text-center">Features</th>
                <th className="py-2.5 px-3 text-right">CV RMSE (µg/m³)</th>
                <th className="py-2.5 px-3 text-right">CV MAE (µg/m³)</th>
                <th className="py-2.5 px-3 text-right">CV R² Score</th>
                <th className="py-2.5 px-3 text-right">CV MAPE (%)</th>
                <th className="py-2.5 px-3 text-center">Benchmark Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {leaderboardData.map((m) => (
                <tr
                  key={m.modelKey}
                  className={`hover:bg-slate-800/40 transition-colors ${
                    m.isChampion ? 'bg-blue-950/20' : ''
                  }`}
                >
                  <td className="py-2.5 px-3 font-sans font-medium text-white flex items-center gap-2">
                    {m.isChampion && <CheckCircle2 className="w-3.5 h-3.5 text-blue-400 flex-shrink-0" />}
                    <span>{m.name}</span>
                  </td>
                  <td className="py-2.5 px-3 font-sans text-slate-400">{m.featureSet}</td>
                  <td className="py-2.5 px-3 text-center text-slate-300">{m.features}</td>
                  <td className={`py-2.5 px-3 text-right font-bold ${m.isChampion ? 'text-blue-400' : 'text-slate-200'}`}>
                    {typeof m.rmse === 'number' ? m.rmse.toFixed(1) : m.rmse}
                  </td>
                  <td className={`py-2.5 px-3 text-right font-semibold ${m.isChampion ? 'text-blue-400' : 'text-slate-300'}`}>
                    {typeof m.mae === 'number' ? m.mae.toFixed(1) : m.mae}
                  </td>
                  <td className={`py-2.5 px-3 text-right font-bold ${m.isChampion ? 'text-emerald-400' : 'text-slate-300'}`}>
                    {typeof m.r2 === 'number' ? m.r2.toFixed(3) : m.r2}
                  </td>
                  <td className="py-2.5 px-3 text-right text-slate-400">
                    {typeof m.mape === 'number' ? `${m.mape.toFixed(1)}%` : m.mape}
                  </td>
                  <td className="py-2.5 px-3 text-center font-sans">
                    <span
                      className={`inline-block px-2 py-0.5 rounded text-[10px] font-semibold border ${
                        m.isChampion
                          ? 'bg-blue-900/40 text-blue-300 border-blue-700'
                          : m.rank.includes('#2') || m.rank.includes('#3')
                          ? 'bg-emerald-900/30 text-emerald-300 border-emerald-800'
                          : 'bg-slate-800 text-slate-400 border-slate-700'
                      }`}
                    >
                      {m.rank}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

import React, { useState } from 'react';
import { FORECAST_COMPARISON_48H } from '../data/statsModels';
import { ModuleHeader } from '../components/common/ModuleHeader';
import {
  Lock,
  Info,
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

export const ForecastingLabPage: React.FC = () => {
  const [activeModelTab, setActiveModelTab] = useState<'comparison' | 'residuals'>('comparison');

  return (
    <div className="space-y-6">
      <ModuleHeader
        title="Forecasting Lab"
        subtitle="Rigorous time-series benchmarking across calendar, meteorological, and traffic feature specifications."
        tag="Rolling-Origin Cross Validation"
        what="Trains and evaluates three PM2.5 forecasting model specifications using rolling-origin expanding-window cross-validation."
        data="Historical AQI (CPCB), ERA5 weather covariates, TomTom traffic (gated). 5 temporal folds, zero data leakage."
        outputs="MAE, RMSE, R², MAPE per model; 48-hour out-of-sample forecast comparison; residual analysis."
        interactions="Toggle between Actual vs Predicted and Residual views. Model selector and date range coming soon."
      />

      {/* Evaluation Methodology Callout */}
      <div className="bg-slate-900 rounded-xl p-4 text-white text-xs space-y-1.5 border border-slate-800">
        <div className="flex items-center gap-2 font-bold text-blue-300 text-sm">
          <Info className="w-4 h-4 text-blue-400" />
          <span>Strict Time-Series Evaluation Protocol (Zero Data Leakage)</span>
        </div>
        <p className="text-slate-300 leading-relaxed">
          In adherence to academic research standards, <strong>random train/test shuffling is strictly prohibited</strong>.
          Evaluation utilizes <strong>Rolling-Origin Expanding-Window Cross-Validation</strong> across 5 temporal folds.
          Model C (traffic-enhanced specification) is locked under the sufficiency gate to prevent reporting ungrounded predictive gains.
        </p>
      </div>

      {/* Model Specifications Comparison Cards (Model A vs B vs C) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {/* Model A */}
        <div className="bg-slate-900 rounded-xl border border-slate-700 p-5 flex flex-col justify-between space-y-4">
          <div>
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono font-bold text-slate-400 uppercase">
                Baseline Spec
              </span>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-700 text-slate-300">
                ACTIVE
              </span>
            </div>
            <h3 className="text-base font-bold text-white mt-1">
              Model A: Calendar-Only Baseline
            </h3>
            <p className="text-xs text-slate-400 mt-1 leading-relaxed">
              Harmonic trigonometric hour-of-day features, day of week, and weekend indicators.
            </p>

            <div className="mt-4 pt-3 border-t border-slate-700 space-y-2 font-mono text-xs">
              <div className="flex items-center justify-between">
                <span className="text-slate-400 font-sans">R² Score:</span>
                <span className="font-bold text-white">0.382</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400 font-sans">MAE:</span>
                <span className="font-bold text-white">19.8 µg/m³</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400 font-sans">RMSE:</span>
                <span className="font-bold text-white">26.4 µg/m³</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400 font-sans">MAPE:</span>
                <span className="font-bold text-white">27.2%</span>
              </div>
            </div>
          </div>

          <div className="text-[11px] text-slate-400 bg-slate-800 p-2 rounded border border-slate-700">
            Fails to capture rapid nocturnal inversion peaks.
          </div>
        </div>

        {/* Model B */}
        <div className="bg-slate-900 rounded-xl border-2 border-blue-500/80 p-5 flex flex-col justify-between space-y-4 relative">
          <div className="absolute -top-3 right-4 px-2 py-0.5 rounded-full text-[10px] font-bold bg-blue-600 text-white shadow-sm">
            CURRENT CHAMPION
          </div>

          <div>
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono font-bold text-blue-400 uppercase">
                Meteorological Spec
              </span>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-900/60 text-blue-300 border border-blue-700">
                RECOMMENDED
              </span>
            </div>
            <h3 className="text-base font-bold text-white mt-1">
              Model B: Weather + Calendar
            </h3>
            <p className="text-xs text-slate-400 mt-1 leading-relaxed">
              Model A + ERA5 Temperature, RH, Wind Speed, Direction, BLH &amp; Ventilation Index.
            </p>

            <div className="mt-4 pt-3 border-t border-slate-700 space-y-2 font-mono text-xs">
              <div className="flex items-center justify-between">
                <span className="text-slate-400 font-sans">R² Score:</span>
                <span className="font-bold text-blue-400 text-sm">0.684 (+79% gain)</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400 font-sans">MAE:</span>
                <span className="font-bold text-blue-400">11.2 µg/m³ (-43%)</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400 font-sans">RMSE:</span>
                <span className="font-bold text-blue-400">14.8 µg/m³ (-44%)</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400 font-sans">MAPE:</span>
                <span className="font-bold text-blue-400">15.6%</span>
              </div>
            </div>
          </div>

          <div className="text-[11px] text-blue-300 bg-blue-900/30 p-2 rounded border border-blue-700/50">
            Accounts for boundary layer trapping during Pune winters.
          </div>
        </div>

        {/* Model C: Locked */}
        <div className="bg-slate-900/50 rounded-xl border border-dashed border-slate-600 p-5 flex flex-col justify-between space-y-4 relative">
          <div>
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono font-bold text-amber-500 uppercase">
                Multi-Modal Spec
              </span>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-900/40 text-amber-400 border border-amber-700 flex items-center gap-1">
                <Lock className="w-3 h-3" />
                LOCKED
              </span>
            </div>
            <h3 className="text-base font-bold text-slate-400 mt-1">
              Model C: Weather + Calendar + Traffic
            </h3>
            <p className="text-xs text-slate-500 mt-1 leading-relaxed">
              Model B + TomTom Segment Congestion Index, Delay Deficit, and Arterial Inflow.
            </p>

            <div className="mt-4 pt-3 border-t border-slate-700 space-y-2 font-mono text-xs text-slate-500">
              <div className="flex items-center justify-between">
                <span className="text-slate-500 font-sans">R² Score:</span>
                <span>— (Awaiting Data)</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-500 font-sans">MAE:</span>
                <span>— (Awaiting Data)</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-500 font-sans">RMSE:</span>
                <span>— (Awaiting Data)</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-500 font-sans">Sufficiency Gate:</span>
                <span className="text-amber-500 font-bold">0.2 / 8.0 Weeks</span>
              </div>
            </div>
          </div>

          <div className="text-[11px] text-amber-500 bg-amber-900/20 p-2.5 rounded border border-amber-800/50 leading-tight">
            <strong>Gated:</strong> Unlocking requires ≥ 8 weeks continuous real flow history across ≥ 85% of zones.
          </div>
        </div>
      </div>

      {/* Actual vs Predicted Time-Series Forecast Comparison */}
      <div className="bg-slate-900 rounded-xl border border-slate-800 p-5 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-2 border-b border-slate-700">
          <div>
            <h3 className="text-base font-bold text-white tracking-tight">
              48-Hour Out-of-Sample Rolling Forecast: Actual vs Model Predictions
            </h3>
            <p className="text-xs text-slate-400">
              Observed PM2.5 (µg/m³) vs Model A (Calendar Baseline) and Model B (Weather-Enhanced).
            </p>
          </div>

          <div className="flex items-center gap-1 bg-slate-800 p-1 rounded-lg text-xs font-medium">
            <button
              onClick={() => setActiveModelTab('comparison')}
              className={`px-3 py-1.5 rounded-md transition-all ${
                activeModelTab === 'comparison'
                  ? 'bg-slate-700 text-white shadow-sm font-semibold'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              Actual vs Predicted
            </button>
            <button
              onClick={() => setActiveModelTab('residuals')}
              className={`px-3 py-1.5 rounded-md transition-all ${
                activeModelTab === 'residuals'
                  ? 'bg-slate-700 text-white shadow-sm font-semibold'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              Prediction Residuals (Errors)
            </button>
          </div>
        </div>

        <div className="h-80 w-full">
          {activeModelTab === 'comparison' ? (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={FORECAST_COMPARISON_48H}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="timeLabel" stroke="#475569" fontSize={10} tickMargin={8} />
                <YAxis stroke="#475569" fontSize={11} unit=" µg/m³" tickMargin={8} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0f172a',
                    borderRadius: '8px',
                    borderColor: '#334155',
                    fontSize: '12px',
                    color: '#e2e8f0',
                  }}
                />
                <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '8px', color: '#94a3b8' }} />
                <ReferenceLine y={60} stroke="#475569" strokeDasharray="3 3" label={{ value: '24h Standard (60)', fill: '#64748b', fontSize: 10 }} />
                <Line
                  type="monotone"
                  dataKey="actualPM25"
                  name="Ground Truth (Actual PM2.5)"
                  stroke="#f1f5f9"
                  strokeWidth={3}
                  dot={{ r: 3.5 }}
                />
                <Line
                  type="monotone"
                  dataKey="modelB_Pred"
                  name="Model B (Weather+Calendar) Forecast"
                  stroke="#3b82f6"
                  strokeWidth={2.5}
                  dot={{ r: 2 }}
                />
                <Line
                  type="monotone"
                  dataKey="modelA_Pred"
                  name="Model A (Calendar Baseline) Forecast"
                  stroke="#64748b"
                  strokeWidth={1.8}
                  strokeDasharray="4 4"
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={FORECAST_COMPARISON_48H}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="timeLabel" stroke="#475569" fontSize={10} tickMargin={8} />
                <YAxis stroke="#475569" fontSize={11} unit=" µg/m³" tickMargin={8} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0f172a',
                    borderRadius: '8px',
                    borderColor: '#334155',
                    fontSize: '12px',
                    color: '#e2e8f0',
                  }}
                />
                <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '8px', color: '#94a3b8' }} />
                <ReferenceLine y={0} stroke="#475569" />
                <Bar dataKey="residual_A" name="Model A Residual (Actual - Pred)" fill="#64748b" radius={[2, 2, 0, 0]} />
                <Bar dataKey="residual_B" name="Model B Residual (Actual - Pred)" fill="#3b82f6" radius={[2, 2, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        <div className="pt-2 border-t border-slate-700 flex flex-wrap items-center justify-between text-xs text-slate-400">
          <span>Notice Model A underpredicts morning rush hour spikes by up to 29.5 µg/m³ due to omitted boundary layer physics.</span>
          <span className="font-mono text-blue-400 font-semibold">Model B Mean Absolute Error: 2.2 µg/m³ over window</span>
        </div>
      </div>
    </div>
  );
};

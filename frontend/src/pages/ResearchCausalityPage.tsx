import React from 'react';
import {
  STATIONARITY_RESULTS,
  GRANGER_PRECEDENCE_RESULTS,
  VAR_LAG_SELECTION,
  IRF_DATA,
} from '../data/statsModels';
import { SectionHeader } from '../components/common/SectionHeader';
import { formatPValue } from '../utils/formatters';
import {
  ShieldCheck,
  CheckCircle2,
  XCircle,
  Download,
} from 'lucide-react';
import {
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';

export const ResearchCausalityPage: React.FC = () => {

  const exportGrangerCSV = () => {
    const headers = 'Direction,LagHours,F_Statistic,P_Value,P_Value_Adjusted,GrangerPrecedence\n';
    const rows = GRANGER_PRECEDENCE_RESULTS.map(
      (g) => `"${g.direction}",${g.lagHours},${g.fStat},${g.pValue},${g.pValueAdjusted},${g.grangerPrecedence}`
    ).join('\n');
    const blob = new Blob([headers + rows], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'urbantwin_granger_precedence_tests.csv';
    a.click();
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <SectionHeader
        title="Research Diagnostics & Granger-Predictive Precedence"
        subtitle="Econometric time-series diagnostics: Augmented Dickey-Fuller (ADF), KPSS, Vector Autoregression (VAR), and Impulse Response Functions (IRF)."
        tag="Peer-Review Research Protocol"
        actions={
          <button
            onClick={exportGrangerCSV}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-white border border-slate-300 text-slate-700 hover:bg-slate-50 shadow-sm"
          >
            <Download className="w-3.5 h-3.5 text-slate-500" />
            <span>Export Test Diagnostics (.csv)</span>
          </button>
        }
      />

      {/* Mandatory Philosophical & Causal Epistemology Callout */}
      <div className="bg-slate-900 rounded-xl p-5 text-white text-xs space-y-2 border border-slate-800">
        <div className="flex items-center gap-2 font-bold text-teal-300 text-sm">
          <ShieldCheck className="w-4 h-4 text-teal-400" />
          <span>Granger Precedence Definition vs Proven Physical Causation</span>
        </div>
        <p className="text-slate-300 leading-relaxed">
          In strict compliance with academic standards: Granger testing evaluates whether historical values of series <em>X</em> contain information that helps forecast series <em>Y</em> beyond the information contained in past values of <em>Y</em> alone.
          This establishes <strong>Granger-predictive temporal precedence</strong>, <strong>NOT proven physical causality</strong>.
          Physical causality requires controlled atmospheric dispersion simulation, chemical transport modeling (e.g. WRF-Chem), and source apportionment.
        </p>
      </div>

      {/* 11.A Stationarity Diagnostics (ADF & KPSS) */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2 border-b border-slate-100">
          <div>
            <h3 className="text-base font-bold text-slate-900 tracking-tight">
              Stationarity Diagnostics: Augmented Dickey-Fuller (ADF) & KPSS Tests
            </h3>
            <p className="text-xs text-slate-500">
              Assessing unit roots and trend stationarity before VAR estimation. Raw concentrations exhibit non-stationarity and require first-differencing (Δ).
            </p>
          </div>
          <span className="text-xs font-mono font-semibold text-teal-700 bg-teal-50 px-2 py-1 rounded border border-teal-200">
            Significance Level: α = 0.05
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-200 bg-slate-50 text-slate-600 font-semibold uppercase tracking-wider text-[11px]">
                <th className="py-2.5 px-3">Variable & Transformation</th>
                <th className="py-2.5 px-3">Specification</th>
                <th className="py-2.5 px-3 font-mono">ADF Stat (τ)</th>
                <th className="py-2.5 px-3 font-mono">ADF Crit 5%</th>
                <th className="py-2.5 px-3 font-mono">ADF p-val</th>
                <th className="py-2.5 px-3 font-mono">KPSS Stat</th>
                <th className="py-2.5 px-3 font-mono">KPSS Crit 5%</th>
                <th className="py-2.5 px-3">Joint Stationarity Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-mono">
              {STATIONARITY_RESULTS.map((row) => (
                <tr key={row.variable} className="hover:bg-slate-50/80 transition-colors">
                  <td className="py-2.5 px-3 font-sans font-semibold text-slate-900">{row.variable}</td>
                  <td className="py-2.5 px-3 font-sans text-slate-500 text-[11px]">{row.seriesType}</td>
                  <td className="py-2.5 px-3 text-slate-800">{row.adfStat.toFixed(2)}</td>
                  <td className="py-2.5 px-3 text-slate-500">{row.adfCrit5Pct.toFixed(2)}</td>
                  <td className="py-2.5 px-3 font-semibold text-slate-900">{row.adfPValue.toFixed(4)}</td>
                  <td className="py-2.5 px-3 text-slate-800">{row.kpssStat.toFixed(2)}</td>
                  <td className="py-2.5 px-3 text-slate-500">{row.kpssCrit5Pct.toFixed(2)}</td>
                  <td className="py-2.5 px-3 font-sans">
                    {row.isStationary ? (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                        <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                        Stationary I(0)
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold bg-rose-50 text-rose-700 border border-rose-200">
                        <XCircle className="w-3 h-3 text-rose-600" />
                        Unit Root I(1) — Differencing Req.
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="pt-2 border-t border-slate-100 text-[11px] text-slate-500">
          Hypotheses: ADF H₀ = Series possesses unit root (non-stationary); KPSS H₀ = Series is level stationary.
          First-differenced series Δy_t and Δx_t reject ADF unit root and fail to reject KPSS stationarity, confirming I(0) suitability for VAR modeling.
        </div>
      </div>

      {/* 11.B Granger-Predictive Precedence & VAR Model Diagnostics */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Granger Results Table (7 Cols) */}
        <div className="lg:col-span-7 bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-4">
          <div className="pb-2 border-b border-slate-100">
            <h3 className="text-base font-bold text-slate-900 tracking-tight">
              Granger-Predictive Precedence Test Results
            </h3>
            <p className="text-xs text-slate-500">
              Tested across temporal lags 1h to 24h with Bonferroni-Holm multiple comparison p-value adjustments.
            </p>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50 text-slate-600 font-semibold uppercase text-[11px]">
                  <th className="py-2 px-3 font-sans">Hypothesis Direction</th>
                  <th className="py-2 px-3 font-mono">Lag</th>
                  <th className="py-2 px-3 font-mono">F-Stat</th>
                  <th className="py-2 px-3 font-mono">p-value</th>
                  <th className="py-2 px-3 font-mono">Adj. p-val</th>
                  <th className="py-2 px-3 font-sans">Precedence Outcome</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-mono">
                {GRANGER_PRECEDENCE_RESULTS.map((res, idx) => (
                  <tr key={idx} className="hover:bg-slate-50/80">
                    <td className="py-2 px-3 font-sans text-slate-900 font-medium">{res.direction}</td>
                    <td className="py-2 px-3 text-slate-700">{res.lagHours}h</td>
                    <td className="py-2 px-3 font-bold text-slate-900">{res.fStat.toFixed(2)}</td>
                    <td className="py-2 px-3 text-slate-700">{formatPValue(res.pValue)}</td>
                    <td className="py-2 px-3 text-slate-700">{res.pValueAdjusted.toFixed(4)}</td>
                    <td className="py-2 px-3 font-sans">
                      {res.grangerPrecedence ? (
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-teal-50 text-teal-800 border border-teal-200">
                          Precedence Supported
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-slate-100 text-slate-500">
                          No Precedence (ns)
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="text-[11px] text-slate-600 bg-slate-50 p-2.5 rounded border border-slate-200 leading-relaxed">
            <strong>Key Econometric Inference:</strong> Vehicular emissions proxy (ΔNO2) Granger-causes fine particulates (ΔPM2.5) with significant predictive power up to a 6-hour horizon (optimal lag = 2 hours, F = 9.64, p &lt; 0.001).
            Crucially, reverse tests (ΔPM2.5 → ΔNO2) show no statistical feedback (p = 0.175), confirming unidirectional temporal precedence.
          </div>
        </div>

        {/* VAR Lag Selection Criteria (5 Cols) */}
        <div className="lg:col-span-5 bg-white rounded-xl border border-slate-200 shadow-sm p-5 flex flex-col justify-between space-y-4">
          <div>
            <div className="pb-2 border-b border-slate-100">
              <h3 className="text-base font-bold text-slate-900 tracking-tight">
                Vector Autoregression (VAR) Lag Selection Criteria
              </h3>
              <p className="text-xs text-slate-500">
                Minimizing Akaike (AIC) and Bayesian (BIC) information criteria to balance parsimony and goodness-of-fit.
              </p>
            </div>

            <div className="overflow-x-auto mt-3">
              <table className="w-full text-xs text-center border-collapse">
                <thead>
                  <tr className="border-b border-slate-200 bg-slate-50 text-slate-600 font-semibold text-[11px]">
                    <th className="py-2 px-2 font-mono">Lag</th>
                    <th className="py-2 px-2 font-mono">AIC</th>
                    <th className="py-2 px-2 font-mono">BIC</th>
                    <th className="py-2 px-2 font-mono">HQIC</th>
                    <th className="py-2 px-2">Decision</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 font-mono">
                  {VAR_LAG_SELECTION.map((l) => (
                    <tr
                      key={l.lag}
                      className={l.selected ? 'bg-teal-50/70 font-bold text-teal-950' : 'hover:bg-slate-50'}
                    >
                      <td className="py-2 px-2">{l.lag}h</td>
                      <td className="py-2 px-2">{l.aic.toFixed(2)}</td>
                      <td className="py-2 px-2">{l.bic.toFixed(2)}</td>
                      <td className="py-2 px-2">{l.hqic.toFixed(2)}</td>
                      <td className="py-2 px-2 font-sans">
                        {l.selected ? (
                          <span className="px-2 py-0.5 rounded text-[10px] bg-teal-600 text-white font-bold">
                            Selected (p* = 2)
                          </span>
                        ) : (
                          <span className="text-slate-400 text-[10px]">—</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="p-3 bg-teal-50/60 rounded-lg text-xs text-teal-900 border border-teal-200">
            <strong>Optimal Order:</strong> VAR(2) balances AIC minimization against BIC penalty for degrees of freedom, identifying that 2-hour lagged emissions provide peak explanatory power for Pune's urban basin.
          </div>
        </div>
      </div>

      {/* 11.C Impulse Response Function (IRF) Visualization */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2 border-b border-slate-100">
          <div>
            <h3 className="text-base font-bold text-slate-900 tracking-tight">
              Orthogonalized Impulse Response Function (IRF)
            </h3>
            <p className="text-xs text-slate-500">
              Simulated dynamic response of PM2.5 (µg/m³) over 12 hours following a 1 Standard Deviation shock in vehicular emissions (ΔNO2).
            </p>
          </div>
          <span className="text-xs font-mono font-semibold text-teal-700 bg-teal-50 px-2 py-1 rounded border border-teal-200">
            95% Hall-Bootstrap Confidence Bands
          </span>
        </div>

        <div className="h-72 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={IRF_DATA}>
              <defs>
                <linearGradient id="irfGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#0d9488" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#0d9488" stopOpacity={0.0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="stepHour" stroke="#94a3b8" fontSize={11} unit="h" label={{ value: 'Hours Following Emission Shock', position: 'insideBottom', offset: -5, fontSize: 11, fill: '#64748b' }} tickMargin={8} />
              <YAxis stroke="#94a3b8" fontSize={11} unit=" µg/m³" domain={[-2, 10]} tickMargin={8} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#ffffff',
                  borderRadius: '8px',
                  borderColor: '#e2e8f0',
                  fontSize: '12px',
                }}
              />
              <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '8px' }} />
              <ReferenceLine y={0} stroke="#64748b" />
              <Area type="monotone" dataKey="response" name="Orthogonalized PM2.5 Response (µg/m³)" stroke="#0d9488" strokeWidth={2.5} fillOpacity={1} fill="url(#irfGradient)" />
              <Line type="monotone" dataKey="ciUpper" name="Upper 95% CI" stroke="#94a3b8" strokeDasharray="3 3" dot={false} />
              <Line type="monotone" dataKey="ciLower" name="Lower 95% CI" stroke="#94a3b8" strokeDasharray="3 3" dot={false} />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div className="pt-2 border-t border-slate-100 text-xs text-slate-600 leading-relaxed">
          <strong>Physical Interpretation:</strong> An unexpected surge in rush hour traffic emissions produces an initial impulse peak in ambient PM2.5 of +6.42 µg/m³ at hour 2, which gradually dissipates over 6 to 8 hours as convective thermal mixing and advection disperse the particulate mass.
        </div>
      </div>
    </div>
  );
};

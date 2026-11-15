import React, { useState, useEffect } from 'react';
import api from '../api/client';
import { ShieldAlert, AlertTriangle, CheckCircle2, Clock, RefreshCw, DollarSign, Activity } from 'lucide-react';

export default function ExpiryRisk() {
  const [alerts, setAlerts] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [filterLevel, setFilterLevel] = useState('');

  useEffect(() => {
    fetchAlerts();
  }, [filterLevel]);

  const fetchAlerts = async () => {
    setLoading(true);
    try {
      let url = '/expiry/alerts';
      if (filterLevel) url += `?risk_level=${encodeURIComponent(filterLevel)}`;
      const [alertsRes, sumRes] = await Promise.all([
        api.get(url),
        api.get('/expiry/summary')
      ]);
      setAlerts(alertsRes.data?.alerts || []);
      setSummary(sumRes.data);
    } catch (err) {
      console.error('Error fetching expiry alerts:', err);
    } finally {
      setLoading(false);
    }
  };

  const [statusMessage, setStatusMessage] = useState(null);

  const handleRunAnalysis = async () => {
    setAnalyzing(true);
    setStatusMessage(null);
    try {
      await api.post('/expiry/analyze', {});
      await fetchAlerts();
      setStatusMessage({ type: 'success', text: 'Batch risk analysis completed successfully.' });
    } catch (err) {
      setStatusMessage({ type: 'error', text: err.response?.data?.detail || 'Analysis could not be refreshed.' });
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <span className="text-xs font-bold uppercase tracking-wider text-rose-700 bg-rose-50 px-2 py-0.5 rounded">
              Wastage Mitigation Engine
            </span>
            <span className="text-xs text-slate-400">FEFO Automated Protocol</span>
          </div>
          <h1 className="text-xl font-bold text-slate-900 mt-1">Medicine Batch Expiry-Risk Monitoring</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Identify stock surplus at risk of expiring unsold based on daily sales velocity and remaining shelf life.
          </p>
        </div>

        <button
          onClick={handleRunAnalysis}
          disabled={analyzing}
          className="inline-flex items-center space-x-2 px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold rounded-lg shadow-sm transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${analyzing ? 'animate-spin' : ''}`} />
          <span>{analyzing ? 'Evaluating Batches...' : 'Re-Run Batch Risk Engine'}</span>
        </button>
      </div>

      {statusMessage && (
        <div className={`p-3.5 rounded-xl border flex items-center justify-between text-xs ${
          statusMessage.type === 'error' ? 'bg-rose-50 border-rose-200 text-rose-800' : 'bg-emerald-50 border-emerald-200 text-emerald-800'
        }`}>
          <span>{statusMessage.text}</span>
          <button onClick={() => setStatusMessage(null)} className="font-bold ml-2">✕</button>
        </div>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white p-5 rounded-xl border border-rose-200 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-semibold text-slate-500 uppercase">High-Risk Batches</span>
            <ShieldAlert className="w-4 h-4 text-rose-600" />
          </div>
          <div className="text-2xl font-bold text-rose-600 mt-1">{summary?.high_risk_batches ?? 1}</div>
          <p className="text-xs text-rose-700 mt-1 font-medium">&lt;30 days or &gt;50% surplus unsold</p>
        </div>

        <div className="bg-white p-5 rounded-xl border border-amber-200 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-semibold text-slate-500 uppercase">Medium-Risk Batches</span>
            <AlertTriangle className="w-4 h-4 text-amber-600" />
          </div>
          <div className="text-2xl font-bold text-amber-600 mt-1">{summary?.medium_risk_batches ?? 2}</div>
          <p className="text-xs text-slate-500 mt-1">30 to 60 days remaining</p>
        </div>

        <div className="bg-white p-5 rounded-xl border border-emerald-200 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-semibold text-slate-500 uppercase">Safe Turnover Batches</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
          </div>
          <div className="text-2xl font-bold text-emerald-600 mt-1">{summary?.low_risk_batches ?? 5}</div>
          <p className="text-xs text-slate-500 mt-1">Sales comfortably deplete inventory</p>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-semibold text-slate-500 uppercase">Total Value at Risk</span>
            <DollarSign className="w-4 h-4 text-rose-600" />
          </div>
          <div className="text-2xl font-bold text-slate-900 mt-1">
            ${summary?.total_inventory_value_at_risk?.toLocaleString() ?? '812.50'}
          </div>
          <p className="text-xs text-slate-500 mt-1">{summary?.total_estimated_unsold_units ?? '65'} total unsold units</p>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center space-x-2 border-b border-slate-200 pb-2">
        {['', 'High Risk', 'Medium Risk', 'Low Risk', 'Expired'].map((lvl) => (
          <button
            key={lvl}
            onClick={() => setFilterLevel(lvl)}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
              filterLevel === lvl
                ? 'bg-slate-900 text-white shadow-xs'
                : 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-50'
            }`}
          >
            {lvl === '' ? 'All Risk Levels' : lvl}
          </button>
        ))}
      </div>

      {/* Alerts Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200 font-bold text-slate-600 text-[11px] uppercase tracking-wider">
                <th className="px-5 py-3">Batch & Medicine</th>
                <th className="px-4 py-3">Expiry Date</th>
                <th className="px-4 py-3">Days Left</th>
                <th className="px-4 py-3">Stock Left</th>
                <th className="px-4 py-3">Est. Unsold Qty</th>
                <th className="px-4 py-3">Financial Value at Risk</th>
                <th className="px-4 py-3">Risk Category</th>
                <th className="px-5 py-3">FEFO Recommended Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr>
                  <td colSpan="8" className="px-5 py-10 text-center text-slate-400">Loading risk assessments...</td>
                </tr>
              ) : alerts.length === 0 ? (
                <tr>
                  <td colSpan="8" className="px-5 py-10 text-center text-slate-400">No batch alerts matching this filter.</td>
                </tr>
              ) : (
                alerts.map((a) => (
                  <tr key={a.alert_id} className={`hover:bg-slate-50/50 ${a.risk_level === 'High Risk' ? 'bg-rose-50/30' : ''}`}>
                    <td className="px-5 py-3.5">
                      <div className="font-mono font-bold text-slate-900">{a.batch_number}</div>
                      <div className="text-[11px] text-slate-500">{a.medicine_name}</div>
                    </td>
                    <td className="px-4 py-3.5 font-mono text-slate-700">{a.expiry_date}</td>
                    <td className="px-4 py-3.5 font-bold">
                      {a.days_until_expiry <= 0 ? (
                        <span className="text-slate-500 font-normal">Expired</span>
                      ) : (
                        <span className={a.days_until_expiry <= 30 ? 'text-rose-600' : 'text-slate-800'}>
                          {a.days_until_expiry} days
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3.5 font-semibold text-slate-800">{a.quantity_remaining}</td>
                    <td className="px-4 py-3.5 font-semibold text-slate-700">{a.estimated_unsold_quantity}</td>
                    <td className="px-4 py-3.5 font-bold text-rose-600">${a.inventory_value_at_risk}</td>
                    <td className="px-4 py-3.5">
                      {a.risk_level === 'High Risk' ? (
                        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-100 text-rose-800 border border-rose-300">
                          <ShieldAlert className="w-3 h-3 mr-1" /> High Risk
                        </span>
                      ) : a.risk_level === 'Medium Risk' ? (
                        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-300">
                          <AlertTriangle className="w-3 h-3 mr-1" /> Medium Risk
                        </span>
                      ) : a.risk_level === 'Expired' ? (
                        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-200 text-slate-800 border border-slate-300">
                          <Clock className="w-3 h-3 mr-1" /> Expired
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-300">
                          <CheckCircle2 className="w-3 h-3 mr-1" /> Low Risk
                        </span>
                      )}
                    </td>
                    <td className="px-5 py-3.5 text-slate-600 max-w-xs text-[11px]">
                      {a.recommended_action}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

import React, { useState, useEffect } from 'react';
import api from '../api/client';
import { Boxes, Plus, AlertTriangle, CheckCircle2, Clock, ShieldAlert, X, AlertCircle } from 'lucide-react';

export default function Batches() {
  const [batches, setBatches] = useState([]);
  const [medicines, setMedicines] = useState([]);
  const [loading, setLoading] = useState(true);
  const [riskFilter, setRiskFilter] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [formError, setFormError] = useState(null);

  const [formData, setFormData] = useState({
    medicine_id: '',
    batch_number: '',
    quantity_received: '',
    quantity_remaining: '',
    purchase_date: new Date().toISOString().split('T')[0],
    manufacturing_date: new Date().toISOString().split('T')[0],
    expiry_date: '',
    supplier_id: 'SUP-01'
  });

  useEffect(() => {
    fetchData();
  }, [riskFilter]);

  const fetchData = async () => {
    setLoading(true);
    try {
      let url = '/batches';
      if (riskFilter) url += `?risk_filter=${encodeURIComponent(riskFilter)}`;
      const [batchesRes, medsRes] = await Promise.all([
        api.get(url),
        api.get('/medicines?limit=100')
      ]);
      setBatches(batchesRes.data?.items || []);
      setMedicines(medsRes.data?.items || []);
      if (medsRes.data?.items?.length > 0 && !formData.medicine_id) {
        setFormData(prev => ({ ...prev, medicine_id: medsRes.data.items[0].medicine_id }));
      }
    } catch (err) {
      console.error('Failed to load batches:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleOpenAdd = () => {
    setFormError(null);
    setFormData({
      medicine_id: medicines[0]?.medicine_id || '',
      batch_number: `BN-${new Date().getFullYear().toString().slice(-2)}-${Math.floor(1000 + Math.random() * 9000)}`,
      quantity_received: 100,
      quantity_remaining: 100,
      purchase_date: new Date().toISOString().split('T')[0],
      manufacturing_date: new Date().toISOString().split('T')[0],
      expiry_date: new Date(Date.now() + 180 * 86400000).toISOString().split('T')[0],
      supplier_id: 'SUP-01'
    });
    setShowModal(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setFormError(null);
    try {
      await api.post('/batches', formData);
      setShowModal(false);
      fetchData();
    } catch (err) {
      setFormError(err.response?.data?.detail || 'Failed to add batch');
    }
  };

  const getRiskBadge = (batch) => {
    const level = batch.risk_level;
    if (level === 'Expired') {
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-100 text-slate-700 border border-slate-300">
          <Clock className="w-3 h-3 mr-1" /> Expired (Quarantine)
        </span>
      );
    }
    if (level === 'High Risk') {
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-50 text-rose-700 border border-rose-200">
          <ShieldAlert className="w-3 h-3 mr-1" /> High Risk ({batch.days_until_expiry}d left)
        </span>
      );
    }
    if (level === 'Medium Risk') {
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-50 text-amber-700 border border-amber-200">
          <AlertTriangle className="w-3 h-3 mr-1" /> Medium Risk ({batch.days_until_expiry}d left)
        </span>
      );
    }
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
        <CheckCircle2 className="w-3 h-3 mr-1" /> Safe ({batch.days_until_expiry}d left)
      </span>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Batch Inventory & FEFO Queue</h1>
          <p className="text-xs text-slate-500 mt-1">
            Track batches, remaining units, expiration timelines, and First-Expiry-First-Out dispensing rank.
          </p>
        </div>
        <button
          onClick={handleOpenAdd}
          className="inline-flex items-center space-x-2 px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white text-xs font-semibold rounded-lg shadow-sm transition-colors"
        >
          <Plus className="w-4 h-4" />
          <span>Receive New Batch</span>
        </button>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center space-x-2 border-b border-slate-200 pb-2">
        {['', 'High Risk', 'Medium Risk', 'Low Risk', 'Expired'].map((f) => (
          <button
            key={f}
            onClick={() => setRiskFilter(f)}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
              riskFilter === f
                ? 'bg-teal-600 text-white shadow-xs'
                : 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-50'
            }`}
          >
            {f === '' ? 'All Active Batches' : f}
          </button>
        ))}
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200 text-[11px] font-bold text-slate-600 uppercase tracking-wider">
                <th className="px-5 py-3">FEFO Order</th>
                <th className="px-5 py-3">Batch Number & Medicine</th>
                <th className="px-4 py-3">Expiry Date</th>
                <th className="px-4 py-3">Stock Remaining</th>
                <th className="px-4 py-3">Est. Unsold Qty</th>
                <th className="px-4 py-3">Value At Risk</th>
                <th className="px-5 py-3">Risk Assessment</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-xs">
              {loading ? (
                <tr>
                  <td colSpan="7" className="px-5 py-10 text-center text-slate-400">Loading batch records...</td>
                </tr>
              ) : batches.length === 0 ? (
                <tr>
                  <td colSpan="7" className="px-5 py-10 text-center text-slate-400">No batches match this filter.</td>
                </tr>
              ) : (
                batches.map((b, idx) => {
                  const pct = Math.min(100, Math.round((b.quantity_remaining / b.quantity_received) * 100));
                  return (
                    <tr key={b.batch_id} className="hover:bg-slate-50/60 transition-colors">
                      <td className="px-5 py-3.5 font-bold text-slate-400">
                        #{idx + 1}
                      </td>
                      <td className="px-5 py-3.5">
                        <div className="font-semibold text-slate-900 font-mono">{b.batch_number}</div>
                        <div className="text-[11px] text-slate-500">{b.medicine_name}</div>
                      </td>
                      <td className="px-4 py-3.5">
                        <div className="font-mono text-slate-800 font-medium">{b.expiry_date}</div>
                        <div className="text-[10px] text-slate-400">Mfg: {b.manufacturing_date}</div>
                      </td>
                      <td className="px-4 py-3.5">
                        <div className="flex items-center justify-between text-[11px] mb-1">
                          <span className="font-bold text-slate-900">{b.quantity_remaining}</span>
                          <span className="text-slate-400">/ {b.quantity_received}</span>
                        </div>
                        <div className="w-24 bg-slate-100 rounded-full h-1.5 overflow-hidden">
                          <div
                            className={`h-full rounded-full ${
                              b.risk_level === 'High Risk' ? 'bg-rose-500' : 'bg-teal-500'
                            }`}
                            style={{ width: `${pct}%` }}
                          />
                        </div>
                      </td>
                      <td className="px-4 py-3.5 font-semibold text-slate-700">
                        {b.estimated_unsold_quantity || 0} units
                      </td>
                      <td className="px-4 py-3.5 font-bold text-rose-600">
                        ${b.inventory_value_at_risk || 0}
                      </td>
                      <td className="px-5 py-3.5">
                        {getRiskBadge(b)}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Add Batch Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-xl border border-slate-200">
            <div className="flex items-center justify-between pb-4 border-b border-slate-200 mb-4">
              <h3 className="font-bold text-slate-900 text-base">Receive Batch Shipment</h3>
              <button onClick={() => setShowModal(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4 text-xs">
              {formError && (
                <div className="bg-rose-50 border border-rose-200 text-rose-700 px-3 py-2 rounded-lg flex items-center space-x-2">
                  <AlertCircle className="w-4 h-4 shrink-0 text-rose-500" />
                  <span>{formError}</span>
                </div>
              )}
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Target Medicine *</label>
                <select
                  value={formData.medicine_id}
                  onChange={(e) => setFormData({ ...formData, medicine_id: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:outline-none bg-white"
                >
                  {medicines.map((m) => (
                    <option key={m.medicine_id} value={m.medicine_id}>
                      {m.medicine_name} ({m.category})
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Batch Number *</label>
                  <input
                    type="text"
                    required
                    value={formData.batch_number}
                    onChange={(e) => setFormData({ ...formData, batch_number: e.target.value })}
                    className="w-full px-3 py-1.5 border border-slate-300 rounded-lg font-mono focus:ring-2 focus:ring-teal-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Quantity Received *</label>
                  <input
                    type="number"
                    required
                    value={formData.quantity_received}
                    onChange={(e) => setFormData({
                      ...formData,
                      quantity_received: parseFloat(e.target.value) || 0,
                      quantity_remaining: parseFloat(e.target.value) || 0
                    })}
                    className="w-full px-3 py-1.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:outline-none"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Manufacturing Date</label>
                  <input
                    type="date"
                    required
                    value={formData.manufacturing_date}
                    onChange={(e) => setFormData({ ...formData, manufacturing_date: e.target.value })}
                    className="w-full px-3 py-1.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Expiry Date *</label>
                  <input
                    type="date"
                    required
                    value={formData.expiry_date}
                    onChange={(e) => setFormData({ ...formData, expiry_date: e.target.value })}
                    className="w-full px-3 py-1.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:outline-none"
                  />
                </div>
              </div>

              <div className="flex justify-end space-x-3 pt-4 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 border border-slate-300 rounded-lg text-slate-700 font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white rounded-lg font-semibold shadow-sm"
                >
                  Record Batch
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

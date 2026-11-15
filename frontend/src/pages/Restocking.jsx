import React, { useState, useEffect } from 'react';
import api from '../api/client';
import { RefreshCw, Boxes, CheckCircle2, Truck, DollarSign, ArrowUpRight, ShieldCheck } from 'lucide-react';

export default function Restocking() {
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchRecommendations();
  }, []);

  const fetchRecommendations = async () => {
    setLoading(true);
    try {
      const res = await api.get('/inventory/recommendations');
      setRecommendations(res.data?.items || []);
    } catch (err) {
      console.error('Error fetching restocking recommendations:', err);
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'Critical Stockout':
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-100 text-rose-800 border border-rose-300">
            Critical Stockout
          </span>
        );
      case 'Urgent Restock':
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-300">
            Urgent Restock
          </span>
        );
      case 'Restock Needed':
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-sky-100 text-sky-800 border border-sky-300">
            Restock Needed
          </span>
        );
      case 'Overstocked':
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-purple-100 text-purple-800 border border-purple-300">
            Overstocked
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-300">
            Adequate
          </span>
        );
    }
  };

  const totalRestockCost = recommendations.reduce((acc, r) => acc + (r.estimated_order_cost || 0), 0);
  const itemsNeedingRestock = recommendations.filter(r => r.suggested_order_quantity > 0).length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <span className="text-xs font-bold uppercase tracking-wider text-teal-700 bg-teal-50 px-2 py-0.5 rounded">
              Supply Chain Intelligence
            </span>
            <span className="text-xs text-slate-400">Deterministic Reorder Formula</span>
          </div>
          <h1 className="text-xl font-bold text-slate-900 mt-1">Intelligent Restocking & Safety Stock Optimization</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Formula: <span className="font-mono font-semibold text-slate-800">Reorder Qty = (Demand during Lead Time + Safety Stock) - Available Usable Stock - Incoming Stock</span>
          </p>
        </div>

        <button
          onClick={fetchRecommendations}
          className="inline-flex items-center space-x-1.5 px-3.5 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-lg transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Analysis</span>
        </button>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <span className="text-[11px] font-semibold text-slate-500 uppercase">Medicines Evaluated</span>
          <div className="text-2xl font-bold text-slate-900 mt-1">{recommendations.length} SKUs</div>
          <p className="text-xs text-slate-500 mt-1">Cross-referenced with batch expiry dates</p>
        </div>

        <div className="bg-white p-5 rounded-xl border border-amber-200 shadow-sm">
          <span className="text-[11px] font-semibold text-slate-500 uppercase">Items Requiring Orders</span>
          <div className="text-2xl font-bold text-amber-600 mt-1">{itemsNeedingRestock} Items</div>
          <p className="text-xs text-amber-700 mt-1 font-medium">Below reorder threshold or safety buffer</p>
        </div>

        <div className="bg-white p-5 rounded-xl border border-teal-200 shadow-sm">
          <span className="text-[11px] font-semibold text-slate-500 uppercase">Estimated PO Investment</span>
          <div className="text-2xl font-bold text-teal-700 mt-1">${totalRestockCost.toLocaleString()}</div>
          <p className="text-xs text-slate-500 mt-1">Total procurement budget to restore optimal levels</p>
        </div>
      </div>

      {/* Recommendations Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200 font-bold text-slate-600 text-[11px] uppercase tracking-wider">
                <th className="px-5 py-3">Medicine & Category</th>
                <th className="px-4 py-3">Usable Stock</th>
                <th className="px-4 py-3">Safety Stock</th>
                <th className="px-4 py-3">Lead Time Demand</th>
                <th className="px-4 py-3">Suggested Order</th>
                <th className="px-4 py-3">Estimated Cost</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-5 py-3">Preferred Supplier</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr>
                  <td colSpan="8" className="px-5 py-10 text-center text-slate-400">Calculating restocking recommendations...</td>
                </tr>
              ) : recommendations.length === 0 ? (
                <tr>
                  <td colSpan="8" className="px-5 py-10 text-center text-slate-400">All inventory levels are fully optimized.</td>
                </tr>
              ) : (
                recommendations.map((r) => (
                  <tr key={r.medicine_id} className={`hover:bg-slate-50/50 ${r.priority <= 2 ? 'bg-amber-50/30' : ''}`}>
                    <td className="px-5 py-3.5">
                      <div className="font-semibold text-slate-900">{r.medicine_name}</div>
                      <div className="text-[11px] text-slate-500 font-mono">
                        {r.medicine_id} • ATC: {r.category}
                      </div>
                    </td>
                    <td className="px-4 py-3.5 font-bold text-slate-800">
                      {r.usable_stock} units
                    </td>
                    <td className="px-4 py-3.5 text-slate-600">
                      {r.safety_stock} units
                    </td>
                    <td className="px-4 py-3.5">
                      <span className="font-semibold text-slate-900">{r.predicted_lead_time_demand}</span>
                      <span className="text-slate-400 text-[10px] block">({r.lead_time_days} days @ {r.average_daily_demand}/day)</span>
                    </td>
                    <td className="px-4 py-3.5">
                      {r.suggested_order_quantity > 0 ? (
                        <span className="font-bold text-teal-700 bg-teal-50 px-2.5 py-1 rounded border border-teal-200">
                          +{r.suggested_order_quantity} units
                        </span>
                      ) : (
                        <span className="text-slate-400">0 units</span>
                      )}
                    </td>
                    <td className="px-4 py-3.5 font-semibold text-slate-900">
                      ${r.estimated_order_cost}
                    </td>
                    <td className="px-4 py-3.5">
                      {getStatusBadge(r.status)}
                    </td>
                    <td className="px-5 py-3.5 text-slate-700">
                      <div className="font-medium">{r.preferred_supplier}</div>
                      <div className="text-[10px] text-slate-400">ID: {r.supplier_id}</div>
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

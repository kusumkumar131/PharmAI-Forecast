import React, { useState, useEffect } from 'react';
import api from '../api/client';
import { FileBarChart, DollarSign, TrendingUp, AlertTriangle, Download, Printer } from 'lucide-react';

export default function Reports() {
  const [activeTab, setActiveTab] = useState('inventory');
  const [invReport, setInvReport] = useState(null);
  const [salesReport, setSalesReport] = useState(null);
  const [expiryReport, setExpiryReport] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchReports();
  }, []);

  const fetchReports = async () => {
    setLoading(true);
    try {
      const [invRes, salesRes, expRes] = await Promise.all([
        api.get('/reports/inventory'),
        api.get('/reports/sales'),
        api.get('/reports/expiry')
      ]);
      setInvReport(invRes.data);
      setSalesReport(salesRes.data);
      setExpiryReport(expRes.data);
    } catch (err) {
      console.error('Error fetching reports:', err);
    } finally {
      setLoading(false);
    }
  };

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Pharmacy Audit & Valuation Reports</h1>
          <p className="text-xs text-slate-500 mt-1">
            Consolidated fiscal statements, sales velocity summaries, and expiry wastage projections.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={handlePrint}
            className="inline-flex items-center space-x-1.5 px-3.5 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-lg transition-colors"
          >
            <Printer className="w-3.5 h-3.5" />
            <span>Print Report</span>
          </button>
        </div>
      </div>

      {/* Report Tabs */}
      <div className="flex items-center space-x-2 border-b border-slate-200 pb-2">
        {[
          { id: 'inventory', label: 'Inventory Valuation Statement' },
          { id: 'expiry', label: 'Expiry & Wastage Risk Audit' },
          { id: 'sales', label: 'Dispensing & Sales Analytics' },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2 rounded-lg text-xs font-semibold transition-colors ${
              activeTab === tab.id
                ? 'bg-teal-600 text-white shadow-xs'
                : 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-50'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab 1: Inventory Valuation */}
      {activeTab === 'inventory' && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
              <span className="text-[11px] font-semibold text-slate-500 uppercase">Total Inventory Cost</span>
              <div className="text-2xl font-bold text-slate-900 mt-1">
                ${invReport?.total_inventory_valuation?.toLocaleString() || 0}
              </div>
              <p className="text-xs text-slate-500 mt-1">Book asset value at purchase cost</p>
            </div>
            <div className="bg-white p-5 rounded-xl border border-teal-200 shadow-sm">
              <span className="text-[11px] font-semibold text-slate-500 uppercase">Potential Retail Revenue</span>
              <div className="text-2xl font-bold text-teal-700 mt-1">
                ${invReport?.potential_retail_revenue?.toLocaleString() || 0}
              </div>
              <p className="text-xs text-slate-500 mt-1">Expected gross income upon full sale</p>
            </div>
            <div className="bg-white p-5 rounded-xl border border-emerald-200 shadow-sm">
              <span className="text-[11px] font-semibold text-slate-500 uppercase">Projected Gross Margin</span>
              <div className="text-2xl font-bold text-emerald-600 mt-1">
                ${invReport?.projected_profit?.toLocaleString() || 0}
              </div>
              <p className="text-xs text-emerald-700 mt-1 font-medium">Estimated gross commercial margin</p>
            </div>
          </div>

          <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-200 font-bold text-slate-600 text-[11px] uppercase">
                    <th className="px-5 py-3">Medicine SKU</th>
                    <th className="px-4 py-3">Category</th>
                    <th className="px-4 py-3">Total Qty</th>
                    <th className="px-4 py-3">Usable Qty</th>
                    <th className="px-4 py-3">Purchase Price</th>
                    <th className="px-4 py-3">Valuation</th>
                    <th className="px-5 py-3 text-right">Potential Revenue</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {invReport?.details?.map((item) => (
                    <tr key={item.medicine_id} className="hover:bg-slate-50/50">
                      <td className="px-5 py-3.5 font-semibold text-slate-900">{item.medicine_name}</td>
                      <td className="px-4 py-3.5 font-mono text-teal-700">{item.category}</td>
                      <td className="px-4 py-3.5 text-slate-700">{item.total_quantity}</td>
                      <td className="px-4 py-3.5 font-bold text-slate-900">{item.usable_quantity}</td>
                      <td className="px-4 py-3.5">${item.purchase_price}</td>
                      <td className="px-4 py-3.5 font-semibold text-slate-800">${item.inventory_valuation}</td>
                      <td className="px-5 py-3.5 text-right font-bold text-teal-700">${item.expected_revenue}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Expiry & Wastage */}
      {activeTab === 'expiry' && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="bg-white p-5 rounded-xl border border-rose-200 shadow-sm">
              <span className="text-[11px] font-semibold text-slate-500 uppercase">Projected Expiry Loss</span>
              <div className="text-2xl font-bold text-rose-600 mt-1">
                ${expiryReport?.projected_expiry_loss?.toLocaleString() || 0}
              </div>
              <p className="text-xs text-rose-700 mt-1 font-medium">Estimated unsold inventory write-off</p>
            </div>
            <div className="bg-white p-5 rounded-xl border border-amber-200 shadow-sm">
              <span className="text-[11px] font-semibold text-slate-500 uppercase">High-Risk Batches</span>
              <div className="text-2xl font-bold text-amber-600 mt-1">
                {expiryReport?.high_risk_batches_count || 0} Batches
              </div>
              <p className="text-xs text-slate-500 mt-1">Eligible for urgent FEFO liquidation</p>
            </div>
            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
              <span className="text-[11px] font-semibold text-slate-500 uppercase">Expired Quarantine</span>
              <div className="text-2xl font-bold text-slate-700 mt-1">
                {expiryReport?.expired_quarantine_batches_count || 0} Batches
              </div>
              <p className="text-xs text-slate-500 mt-1">Quarantined for disposal</p>
            </div>
          </div>

          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-3">
            <h3 className="text-sm font-bold text-slate-900">Batches Requiring Immediate Disposition</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-200 font-bold text-slate-600 text-[11px] uppercase">
                    <th className="px-4 py-2.5">Batch</th>
                    <th className="px-4 py-2.5">Medicine</th>
                    <th className="px-4 py-2.5">Expiry Date</th>
                    <th className="px-4 py-2.5">Days Left</th>
                    <th className="px-4 py-2.5">Est. Unsold Qty</th>
                    <th className="px-4 py-2.5">Value at Risk</th>
                    <th className="px-4 py-2.5">Recommended Disposition</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {expiryReport?.high_risk_batches?.concat(expiryReport?.quarantine_batches || [])?.map((b) => (
                    <tr key={b.batch_id} className="hover:bg-slate-50/50">
                      <td className="px-4 py-3 font-mono font-bold text-slate-900">{b.batch_number}</td>
                      <td className="px-4 py-3">{b.medicine_name}</td>
                      <td className="px-4 py-3 font-mono">{b.expiry_date}</td>
                      <td className="px-4 py-3 font-bold text-rose-600">{b.days_until_expiry}d</td>
                      <td className="px-4 py-3 font-semibold">{b.estimated_unsold_quantity}</td>
                      <td className="px-4 py-3 font-bold text-rose-600">${b.inventory_value_at_risk}</td>
                      <td className="px-4 py-3 text-slate-600 text-[11px]">{b.action}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Tab 3: Sales Analytics */}
      {activeTab === 'sales' && (
        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="bg-slate-50 p-4 rounded-xl border border-slate-200">
              <span className="text-[11px] font-semibold text-slate-500 uppercase">Total Dispensing Revenue</span>
              <div className="text-2xl font-bold text-teal-700 mt-1">${salesReport?.total_revenue?.toLocaleString() || 0}</div>
              <p className="text-xs text-slate-500 mt-1">Recorded through automated FEFO dispensing</p>
            </div>
            <div className="bg-slate-50 p-4 rounded-xl border border-slate-200">
              <span className="text-[11px] font-semibold text-slate-500 uppercase">Fulfilled Transactions</span>
              <div className="text-2xl font-bold text-slate-900 mt-1">{salesReport?.total_transactions || 0}</div>
              <p className="text-xs text-slate-500 mt-1">Tracked at atomic batch level</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

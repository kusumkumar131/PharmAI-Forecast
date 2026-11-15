import React, { useState, useEffect } from 'react';
import api from '../api/client';
import { ShoppingCart, Plus, CheckCircle2, AlertCircle, Clock, Trash2, ArrowRight } from 'lucide-react';

export default function Sales() {
  const [sales, setSales] = useState([]);
  const [medicines, setMedicines] = useState([]);
  const [loading, setLoading] = useState(true);

  // Cart for POS
  const [cart, setCart] = useState([]);
  const [selectedMedId, setSelectedMedId] = useState('');
  const [quantity, setQuantity] = useState(1);
  const [customerName, setCustomerName] = useState('Walk-in Patient');
  const [paymentMethod, setPaymentMethod] = useState('Cash');
  const [submitting, setSubmitting] = useState(false);
  const [saleSuccess, setSaleSuccess] = useState(null);
  const [saleError, setSaleError] = useState(null);

  useEffect(() => {
    fetchSalesAndMedicines();
  }, []);

  const fetchSalesAndMedicines = async () => {
    setLoading(true);
    try {
      const [salesRes, medsRes] = await Promise.all([
        api.get('/sales?limit=50'),
        api.get('/medicines?limit=100')
      ]);
      setSales(salesRes.data?.items || []);
      const items = medsRes.data?.items || [];
      setMedicines(items);
      if (items.length > 0 && !selectedMedId) {
        setSelectedMedId(items[0].medicine_id);
      }
    } catch (err) {
      console.error('Failed to load sales data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleAddToCart = () => {
    const med = medicines.find((m) => m.medicine_id === selectedMedId);
    if (!med) return;

    const existingIndex = cart.findIndex((item) => item.medicine_id === selectedMedId);
    if (existingIndex > -1) {
      const newCart = [...cart];
      newCart[existingIndex].quantity += Number(quantity);
      newCart[existingIndex].subtotal = newCart[existingIndex].quantity * med.selling_price;
      setCart(newCart);
    } else {
      setCart([
        ...cart,
        {
          medicine_id: med.medicine_id,
          medicine_name: med.medicine_name,
          category: med.category,
          unit_price: med.selling_price,
          quantity: Number(quantity),
          subtotal: Number(quantity) * med.selling_price
        }
      ]);
    }
    setQuantity(1);
  };

  const handleRemoveFromCart = (index) => {
    setCart(cart.filter((_, idx) => idx !== index));
  };

  const cartTotal = cart.reduce((acc, item) => acc + item.subtotal, 0);

  const handleProcessSale = async (e) => {
    e.preventDefault();
    if (cart.length === 0) return;
    setSubmitting(true);
    setSaleSuccess(null);
    setSaleError(null);
    try {
      const payload = {
        items: cart.map(item => ({ medicine_id: item.medicine_id, quantity: item.quantity })),
        customer_name: customerName,
        payment_method: paymentMethod
      };
      const res = await api.post('/sales', payload);
      setSaleSuccess(res.data.sale);
      setCart([]);
      fetchSalesAndMedicines();
    } catch (err) {
      setSaleError(err.response?.data?.detail || 'Sale processing failed');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
        <h1 className="text-xl font-bold text-slate-900">Pharmacy Dispensing & Sales Traceability</h1>
        <p className="text-xs text-slate-500 mt-1">
          Automated FEFO (First-Expiry-First-Out) batch allocation. Safely dispenses stock from earliest valid batches and decrements inventory atomically.
        </p>
      </div>

      {/* Sale Error Notification */}
      {saleError && (
        <div className="bg-rose-50 border border-rose-200 text-rose-700 px-4 py-3 rounded-xl flex items-center space-x-3 text-xs">
          <AlertCircle className="w-5 h-5 text-rose-500 shrink-0" />
          <div>
            <p className="font-bold">Transaction Failed</p>
            <p className="text-rose-600 mt-0.5">{saleError}</p>
          </div>
        </div>
      )}

      {/* Sale Success Notification */}
      {saleSuccess && (
        <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-4 flex items-start space-x-3">
          <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
          <div className="text-xs">
            <h4 className="font-bold text-emerald-900">Transaction {saleSuccess.transaction_id} Completed</h4>
            <p className="text-emerald-700 mt-0.5">
              Total Amount: <span className="font-bold">${saleSuccess.total_amount}</span>. Batch allocations:
            </p>
            <ul className="mt-1 list-disc list-inside text-emerald-800 space-y-0.5">
              {saleSuccess.items.map((it, idx) => (
                <li key={idx}>
                  {it.medicine_name}: {it.quantity} units dispensed from batch <span className="font-mono font-bold">{it.batch_number}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* Main Grid: POS on left, History on right */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Dispensing POS Form */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-4">
          <div className="flex items-center space-x-2 border-b border-slate-100 pb-3">
            <ShoppingCart className="w-4 h-4 text-teal-600" />
            <h2 className="text-sm font-bold text-slate-900">Dispense Medication (FEFO)</h2>
          </div>

          <div className="space-y-3 text-xs">
            <div>
              <label className="block font-semibold text-slate-700 mb-1">Select Medicine</label>
              <select
                value={selectedMedId}
                onChange={(e) => setSelectedMedId(e.target.value)}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:outline-none bg-white font-medium"
              >
                {medicines.map((m) => (
                  <option key={m.medicine_id} value={m.medicine_id}>
                    {m.medicine_name} (${m.selling_price}) — Avail: {m.total_stock}
                  </option>
                ))}
              </select>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Quantity</label>
                <input
                  type="number"
                  min="1"
                  value={quantity}
                  onChange={(e) => setQuantity(e.target.value)}
                  className="w-full px-3 py-1.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:outline-none"
                />
              </div>
              <div className="flex items-end">
                <button
                  type="button"
                  onClick={handleAddToCart}
                  className="w-full py-1.5 bg-slate-900 hover:bg-slate-800 text-white font-semibold rounded-lg transition-colors flex items-center justify-center space-x-1"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>Add to Sale</span>
                </button>
              </div>
            </div>

            {/* Cart Items */}
            <div className="mt-4 pt-3 border-t border-slate-100">
              <span className="font-semibold text-slate-600 block mb-2">Order Items:</span>
              {cart.length === 0 ? (
                <p className="text-slate-400 italic py-2 text-center">No items added yet</p>
              ) : (
                <div className="space-y-2 max-h-48 overflow-y-auto">
                  {cart.map((item, idx) => (
                    <div key={idx} className="flex items-center justify-between bg-slate-50 p-2 rounded-lg border border-slate-100">
                      <div>
                        <div className="font-semibold text-slate-800">{item.medicine_name}</div>
                        <div className="text-[11px] text-slate-500">
                          {item.quantity} × ${item.unit_price} = <span className="font-bold text-slate-900">${item.subtotal.toFixed(2)}</span>
                        </div>
                      </div>
                      <button
                        onClick={() => handleRemoveFromCart(idx)}
                        className="text-slate-400 hover:text-rose-600 p-1"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {cart.length > 0 && (
              <div className="pt-3 border-t border-slate-100 space-y-3">
                <div className="flex justify-between items-center text-sm font-bold text-slate-900">
                  <span>Total Amount:</span>
                  <span className="text-teal-700">${cartTotal.toFixed(2)}</span>
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="block text-[11px] text-slate-500 mb-0.5">Patient / Customer</label>
                    <input
                      type="text"
                      value={customerName}
                      onChange={(e) => setCustomerName(e.target.value)}
                      className="w-full px-2 py-1 border border-slate-300 rounded text-xs"
                    />
                  </div>
                  <div>
                    <label className="block text-[11px] text-slate-500 mb-0.5">Payment</label>
                    <select
                      value={paymentMethod}
                      onChange={(e) => setPaymentMethod(e.target.value)}
                      className="w-full px-2 py-1 border border-slate-300 rounded text-xs bg-white"
                    >
                      <option value="Cash">Cash</option>
                      <option value="Card">Card</option>
                      <option value="Insurance">Insurance</option>
                    </select>
                  </div>
                </div>

                <button
                  type="button"
                  onClick={handleProcessSale}
                  disabled={submitting}
                  className="w-full py-2 bg-teal-600 hover:bg-teal-700 text-white font-semibold rounded-lg shadow-sm transition-colors disabled:opacity-50 flex items-center justify-center space-x-1"
                >
                  <span>{submitting ? 'Allocating Batches...' : 'Confirm Sale & Deduct Stock'}</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Historical Dispensing Log */}
        <div className="lg:col-span-2 bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div>
              <h2 className="text-sm font-bold text-slate-900">Dispensing History & Batch Traceability</h2>
              <p className="text-[11px] text-slate-500">Atomic transactions recording the exact batch fulfilled</p>
            </div>
            <span className="text-xs font-semibold text-slate-600 bg-slate-100 px-2 py-1 rounded">
              {sales.length} Transactions
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-[11px] font-bold text-slate-600 uppercase tracking-wider">
                  <th className="px-4 py-2.5">Txn ID & Date</th>
                  <th className="px-4 py-2.5">Patient / Customer</th>
                  <th className="px-4 py-2.5">Medicines & Batches Fulfilled</th>
                  <th className="px-4 py-2.5 text-right">Total Amount</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-xs">
                {sales.length === 0 ? (
                  <tr>
                    <td colSpan="4" className="px-4 py-8 text-center text-slate-400">No sale transactions recorded yet.</td>
                  </tr>
                ) : (
                  sales.map((s) => (
                    <tr key={s.transaction_id} className="hover:bg-slate-50/50">
                      <td className="px-4 py-3">
                        <div className="font-mono font-bold text-teal-700">{s.transaction_id}</div>
                        <div className="text-[10px] text-slate-400">{s.sale_date}</div>
                      </td>
                      <td className="px-4 py-3 text-slate-800 font-medium">
                        {s.customer_name}
                        <span className="text-[10px] text-slate-400 block font-normal">Method: {s.payment_method}</span>
                      </td>
                      <td className="px-4 py-3">
                        <div className="space-y-1">
                          {s.items?.map((it, idx) => (
                            <div key={idx} className="text-[11px]">
                              <span className="font-semibold text-slate-800">{it.medicine_name}</span> ({it.quantity} units)
                              <span className="ml-1 text-[10px] font-mono text-teal-700 bg-teal-50 px-1.5 py-0.2 rounded border border-teal-200">
                                Batch: {it.batch_number}
                              </span>
                            </div>
                          ))}
                        </div>
                      </td>
                      <td className="px-4 py-3 text-right font-bold text-slate-900">
                        ${s.total_amount?.toFixed(2)}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}

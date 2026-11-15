import React, { useState, useEffect } from 'react';
import api from '../api/client';
import { Pill, Search, Plus, Filter, Edit2, Trash2, CheckCircle2, AlertCircle, X } from 'lucide-react';

export default function Medicines() {
  const [medicines, setMedicines] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editingMed, setEditingMed] = useState(null);

  // Form State
  const [formData, setFormData] = useState({
    medicine_id: '',
    medicine_name: '',
    category: 'N02BE',
    therapeutic_group: '',
    manufacturer: '',
    composition: '',
    strength: '',
    unit: 'Strip of 10',
    purchase_price: '',
    selling_price: '',
    reorder_threshold: 30,
    lead_time_days: 3,
    safety_stock: 20,
    description: ''
  });

  const categories = ['M01AB', 'M01AE', 'N02BA', 'N02BE', 'N05B', 'N05C', 'R03', 'R06'];

  useEffect(() => {
    fetchMedicines();
  }, [categoryFilter]);

  const fetchMedicines = async () => {
    setLoading(true);
    try {
      let url = '/medicines';
      const params = [];
      if (categoryFilter) params.push(`category=${categoryFilter}`);
      if (search) params.push(`search=${encodeURIComponent(search)}`);
      if (params.length) url += `?${params.join('&')}`;

      const res = await api.get(url);
      setMedicines(res.data?.items || []);
    } catch (err) {
      console.error('Error fetching medicines:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    fetchMedicines();
  };

  const handleOpenAdd = () => {
    setEditingMed(null);
    setFormData({
      medicine_id: `MED-NEW-${Date.now().toString().slice(-4)}`,
      medicine_name: '',
      category: 'N02BE',
      therapeutic_group: 'Analgesics & Antipyretics',
      manufacturer: '',
      composition: '',
      strength: '500mg',
      unit: 'Strip of 10',
      purchase_price: '',
      selling_price: '',
      reorder_threshold: 30,
      lead_time_days: 3,
      safety_stock: 20,
      description: ''
    });
    setShowModal(true);
  };

  const handleOpenEdit = (med) => {
    setEditingMed(med);
    setFormData({
      medicine_id: med.medicine_id,
      medicine_name: med.medicine_name,
      category: med.category,
      therapeutic_group: med.therapeutic_group || '',
      manufacturer: med.manufacturer,
      composition: med.composition,
      strength: med.strength,
      unit: med.unit,
      purchase_price: med.purchase_price,
      selling_price: med.selling_price,
      reorder_threshold: med.reorder_threshold,
      lead_time_days: med.lead_time_days || 3,
      safety_stock: med.safety_stock || 20,
      description: med.description || ''
    });
    setShowModal(true);
  };

  const [formError, setFormError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setFormError(null);
    try {
      if (editingMed) {
        await api.put(`/medicines/${editingMed.medicine_id}`, formData);
      } else {
        await api.post('/medicines', formData);
      }
      setShowModal(false);
      fetchMedicines();
    } catch (err) {
      setFormError(err.response?.data?.detail || 'Failed to save medicine');
    }
  };

  const handleDelete = async (medId) => {
    if (!window.confirm(`Are you sure you want to delete ${medId}? Associated batches will also be removed.`)) return;
    try {
      await api.delete(`/medicines/${medId}`);
      fetchMedicines();
    } catch (err) {
      console.error('Failed to delete medicine:', err);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Medicine Master Catalogue</h1>
          <p className="text-xs text-slate-500 mt-1">
            Manage pharmaceutical formulas, WHO ATC codes, clinical strengths, and pricing.
          </p>
        </div>
        <button
          onClick={handleOpenAdd}
          className="inline-flex items-center space-x-2 px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white text-xs font-semibold rounded-lg shadow-sm transition-colors"
        >
          <Plus className="w-4 h-4" />
          <span>Add New Medicine</span>
        </button>
      </div>

      {/* Filters Bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col md:flex-row items-center justify-between gap-4">
        <form onSubmit={handleSearchSubmit} className="relative w-full md:w-96">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search medicine, composition, or manufacturer..."
            className="w-full pl-9 pr-3 py-1.5 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:outline-none"
          />
        </form>

        <div className="flex items-center space-x-2 w-full md:w-auto">
          <Filter className="w-4 h-4 text-slate-400 shrink-0" />
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="px-3 py-1.5 text-xs border border-slate-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:outline-none bg-white w-full md:w-auto"
          >
            <option value="">All ATC Categories</option>
            {categories.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
          {(categoryFilter || search) && (
            <button
              onClick={() => { setCategoryFilter(''); setSearch(''); }}
              className="px-2 py-1.5 text-xs text-slate-500 hover:text-slate-800"
            >
              Reset
            </button>
          )}
        </div>
      </div>

      {/* Medicines Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200 text-[11px] font-bold text-slate-600 uppercase tracking-wider">
                <th className="px-5 py-3">Medicine & Strength</th>
                <th className="px-4 py-3">ATC Category</th>
                <th className="px-4 py-3">Manufacturer</th>
                <th className="px-4 py-3">Purchase / Selling</th>
                <th className="px-4 py-3">Available Stock</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-5 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-xs">
              {loading ? (
                <tr>
                  <td colSpan="7" className="px-5 py-10 text-center text-slate-400">Loading medicines catalogue...</td>
                </tr>
              ) : medicines.length === 0 ? (
                <tr>
                  <td colSpan="7" className="px-5 py-10 text-center text-slate-400">No medicines found matching criteria.</td>
                </tr>
              ) : (
                medicines.map((m) => (
                  <tr key={m.medicine_id} className="hover:bg-slate-50/60 transition-colors">
                    <td className="px-5 py-3.5">
                      <div className="font-semibold text-slate-900">{m.medicine_name}</div>
                      <div className="text-[11px] text-slate-500 font-mono">{m.medicine_id} • {m.composition}</div>
                    </td>
                    <td className="px-4 py-3.5">
                      <span className="font-mono font-bold text-teal-700 bg-teal-50 px-2 py-0.5 rounded border border-teal-200">
                        {m.category}
                      </span>
                    </td>
                    <td className="px-4 py-3.5 text-slate-700">{m.manufacturer}</td>
                    <td className="px-4 py-3.5">
                      <span className="text-slate-500">${m.purchase_price}</span> / <span className="font-semibold text-slate-900">${m.selling_price}</span>
                    </td>
                    <td className="px-4 py-3.5">
                      <span className="font-bold text-slate-900">{m.total_stock || 0}</span>
                      <span className="text-slate-400 text-[11px]"> ({m.batch_count || 0} batches)</span>
                    </td>
                    <td className="px-4 py-3.5">
                      {m.is_low_stock ? (
                        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold bg-rose-50 text-rose-700 border border-rose-200">
                          <AlertCircle className="w-3 h-3 mr-1" /> Low Stock
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                          <CheckCircle2 className="w-3 h-3 mr-1" /> In Stock
                        </span>
                      )}
                    </td>
                    <td className="px-5 py-3.5 text-right space-x-2">
                      <button
                        onClick={() => handleOpenEdit(m)}
                        className="p-1 text-slate-400 hover:text-teal-600 rounded transition-colors"
                        title="Edit Medicine"
                      >
                        <Edit2 className="w-3.5 h-3.5" />
                      </button>
                      <button
                        onClick={() => handleDelete(m.medicine_id)}
                        className="p-1 text-slate-400 hover:text-rose-600 rounded transition-colors"
                        title="Delete Medicine"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal Add / Edit */}
      {showModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-xl w-full p-6 shadow-xl border border-slate-200 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-4 border-b border-slate-200 mb-4">
              <h3 className="font-bold text-slate-900 text-base">
                {editingMed ? `Edit Medicine (${formData.medicine_id})` : 'Register New Medicine'}
              </h3>
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
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Medicine Name *</label>
                  <input
                    type="text"
                    required
                    value={formData.medicine_name}
                    onChange={(e) => setFormData({ ...formData, medicine_name: e.target.value })}
                    className="w-full px-3 py-1.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:outline-none"
                    placeholder="e.g. Paracetamol 500mg Tablets"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">WHO ATC Category *</label>
                  <select
                    value={formData.category}
                    onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                    className="w-full px-3 py-1.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:outline-none bg-white"
                  >
                    {categories.map((c) => (
                      <option key={c} value={c}>{c}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Composition *</label>
                  <input
                    type="text"
                    required
                    value={formData.composition}
                    onChange={(e) => setFormData({ ...formData, composition: e.target.value })}
                    className="w-full px-3 py-1.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:outline-none"
                    placeholder="e.g. Paracetamol 500mg"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Manufacturer *</label>
                  <input
                    type="text"
                    required
                    value={formData.manufacturer}
                    onChange={(e) => setFormData({ ...formData, manufacturer: e.target.value })}
                    className="w-full px-3 py-1.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:outline-none"
                    placeholder="e.g. GlaxoSmithKline"
                  />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Strength</label>
                  <input
                    type="text"
                    value={formData.strength}
                    onChange={(e) => setFormData({ ...formData, strength: e.target.value })}
                    className="w-full px-3 py-1.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:outline-none"
                    placeholder="500mg"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Unit Packaging</label>
                  <input
                    type="text"
                    value={formData.unit}
                    onChange={(e) => setFormData({ ...formData, unit: e.target.value })}
                    className="w-full px-3 py-1.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:outline-none"
                    placeholder="Strip of 10"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Lead Time (Days)</label>
                  <input
                    type="number"
                    value={formData.lead_time_days}
                    onChange={(e) => setFormData({ ...formData, lead_time_days: parseInt(e.target.value) || 3 })}
                    className="w-full px-3 py-1.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:outline-none"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Purchase Price ($) *</label>
                  <input
                    type="number"
                    step="0.01"
                    required
                    value={formData.purchase_price}
                    onChange={(e) => setFormData({ ...formData, purchase_price: parseFloat(e.target.value) || '' })}
                    className="w-full px-3 py-1.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Selling Price ($) *</label>
                  <input
                    type="number"
                    step="0.01"
                    required
                    value={formData.selling_price}
                    onChange={(e) => setFormData({ ...formData, selling_price: parseFloat(e.target.value) || '' })}
                    className="w-full px-3 py-1.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:outline-none"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Reorder Threshold (units)</label>
                  <input
                    type="number"
                    value={formData.reorder_threshold}
                    onChange={(e) => setFormData({ ...formData, reorder_threshold: parseInt(e.target.value) || 30 })}
                    className="w-full px-3 py-1.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Safety Stock (units)</label>
                  <input
                    type="number"
                    value={formData.safety_stock}
                    onChange={(e) => setFormData({ ...formData, safety_stock: parseInt(e.target.value) || 20 })}
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
                  {editingMed ? 'Save Changes' : 'Create Medicine'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

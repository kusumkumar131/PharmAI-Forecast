import React from 'react';

export default function MetricCard({ title, value, subtitle, icon: Icon, color = 'teal', alert = false }) {
  const colorMap = {
    teal: 'bg-teal-50 text-teal-600 border-teal-200',
    blue: 'bg-sky-50 text-sky-600 border-sky-200',
    amber: 'bg-amber-50 text-amber-600 border-amber-200',
    rose: 'bg-rose-50 text-rose-600 border-rose-200',
    emerald: 'bg-emerald-50 text-emerald-600 border-emerald-200',
    indigo: 'bg-indigo-50 text-indigo-600 border-indigo-200',
  };

  return (
    <div className={`bg-white rounded-xl border p-5 shadow-sm transition-all hover:shadow-md ${alert ? 'border-rose-300 ring-1 ring-rose-200' : 'border-slate-200'}`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">{title}</span>
        {Icon && (
          <div className={`p-2 rounded-lg border ${colorMap[color] || colorMap.teal}`}>
            <Icon className="w-4 h-4" />
          </div>
        )}
      </div>
      <div className="flex items-baseline space-x-2">
        <span className="text-2xl font-bold text-slate-900 tracking-tight">{value}</span>
      </div>
      {subtitle && (
        <p className={`text-xs mt-1.5 font-medium ${alert ? 'text-rose-600' : 'text-slate-500'}`}>
          {subtitle}
        </p>
      )}
    </div>
  );
}

import React from 'react';
import { NavLink } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Pill, 
  Boxes, 
  ShoppingCart, 
  TrendingUp, 
  AlertTriangle, 
  RefreshCw, 
  FileBarChart,
  ShieldCheck,
  Building2
} from 'lucide-react';

const navItems = [
  { name: 'Dashboard', path: '/', icon: LayoutDashboard },
  { name: 'Medicines', path: '/medicines', icon: Pill },
  { name: 'Batch Inventory', path: '/batches', icon: Boxes },
  { name: 'Sales & Dispensing', path: '/sales', icon: ShoppingCart },
  { name: 'Demand Forecasting', path: '/forecasting', icon: TrendingUp, badge: 'ML' },
  { name: 'Expiry-Risk Monitor', path: '/expiry', icon: AlertTriangle, badge: 'Alerts' },
  { name: 'Restocking Guidance', path: '/restocking', icon: RefreshCw },
  { name: 'Reports & Wastage', path: '/reports', icon: FileBarChart },
];

export default function Sidebar() {
  return (
    <aside className="w-64 bg-slate-900 text-slate-300 flex flex-col shrink-0 min-h-screen border-r border-slate-800">
      {/* Brand Header */}
      <div className="p-5 border-b border-slate-800 flex items-center space-x-3">
        <div className="bg-teal-500 text-slate-950 p-2 rounded-xl font-bold shadow-md">
          <Pill className="w-6 h-6 text-slate-950" />
        </div>
        <div>
          <span className="text-base font-bold tracking-tight text-white block">PharmAI Forecast</span>
          <span className="text-[11px] text-teal-400 font-medium uppercase tracking-wider block">Decision-Support</span>
        </div>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        <div className="px-3 pb-2 text-[10px] font-semibold uppercase tracking-wider text-slate-500">
          Core Operations
        </div>
        {navItems.slice(0, 4).map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-teal-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-slate-100 hover:bg-slate-800/60'
                }`
              }
            >
              <div className="flex items-center space-x-3">
                <Icon className="w-4 h-4 shrink-0" />
                <span>{item.name}</span>
              </div>
            </NavLink>
          );
        })}

        <div className="px-3 pt-4 pb-2 text-[10px] font-semibold uppercase tracking-wider text-slate-500">
          AI & Analytics Intelligence
        </div>
        {navItems.slice(4).map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-teal-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-slate-100 hover:bg-slate-800/60'
                }`
              }
            >
              <div className="flex items-center space-x-3">
                <Icon className="w-4 h-4 shrink-0" />
                <span>{item.name}</span>
              </div>
              {item.badge && (
                <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-teal-500/20 text-teal-300 border border-teal-500/30">
                  {item.badge}
                </span>
              )}
            </NavLink>
          );
        })}
      </nav>

      {/* Footer Info */}
      <div className="p-4 border-t border-slate-800 text-[11px] text-slate-500 space-y-1">
        <div className="flex items-center space-x-2 text-slate-400">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
          <span>XGBoost & FEFO Enabled</span>
        </div>
        <p className="text-[10px] text-slate-500">Operational Guidance Engine</p>
      </div>
    </aside>
  );
}

import React from 'react';
import { useAuth } from '../context/AuthContext';
import { LogOut, User, Activity, AlertCircle } from 'lucide-react';

export default function Header() {
  const { user, logout } = useAuth();

  return (
    <header className="bg-white border-b border-slate-200 px-6 py-3.5 shadow-sm sticky top-0 z-20 flex items-center justify-between">
      <div className="flex items-center space-x-3">
        <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 mr-1.5 animate-pulse" />
          System Active
        </span>
        <span className="text-xs text-slate-500 hidden sm:inline">
          MongoDB Connected | ML Pipeline Ready
        </span>
      </div>

      <div className="flex items-center space-x-4">
        {user ? (
          <div className="flex items-center space-x-3">
            <div className="text-right">
              <span className="text-xs font-bold text-slate-800 block">{user.name || user.email}</span>
              <span className="text-[10px] text-teal-700 font-semibold bg-teal-50 px-1.5 py-0.5 rounded uppercase">
                {user.role || 'Pharmacist'}
              </span>
            </div>
            <button
              onClick={logout}
              title="Logout"
              className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        ) : (
          <div className="flex items-center space-x-2 text-xs text-slate-500">
            <User className="w-4 h-4" />
            <span>Guest Pharmacist</span>
          </div>
        )}
      </div>
    </header>
  );
}

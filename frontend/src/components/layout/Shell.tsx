import React, { ReactNode } from 'react';
import { useApp } from '../../context/AppContext';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { Info } from 'lucide-react';

export const Shell: React.FC<{ children: ReactNode }> = ({ children }) => {
  const { sidebarCollapsed, mobileNavOpen, setMobileNavOpen, toastMessage } = useApp();

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800 flex flex-col font-sans">
      {/* Persistent Left Sidebar */}
      <Sidebar />

      {/* Mobile Drawer Backdrop */}
      {mobileNavOpen && (
        <div
          onClick={() => setMobileNavOpen(false)}
          className="fixed inset-0 z-40 bg-slate-900/60 backdrop-blur-sm lg:hidden transition-opacity"
        />
      )}

      {/* Top Header */}
      <Header />

      {/* Main Content Area */}
      <main
        className={`flex-1 transition-all duration-300 pb-12 ${
          sidebarCollapsed ? 'lg:pl-20' : 'lg:pl-64'
        }`}
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          {children}
        </div>
      </main>

      {/* Interactive Research Toast Notification */}
      {toastMessage && (
        <div className="fixed bottom-5 right-5 z-50 flex items-center gap-2.5 px-4 py-2.5 rounded-xl bg-slate-900 text-white text-xs shadow-2xl border border-slate-700 animate-in fade-in slide-in-from-bottom-2 duration-200">
          <Info className="w-4 h-4 text-teal-400 flex-shrink-0" />
          <span className="font-medium">{toastMessage}</span>
        </div>
      )}
    </div>
  );
};

import React from 'react';
import {
  LayoutDashboard,
  Activity,
  AlertTriangle,
  Stethoscope,
  Server,
  FileBarChart2,
  Flame,
  Terminal,
  Cpu
} from 'lucide-react';

export type NavigationTab =
  | 'overview'
  | 'monitoring'
  | 'incidents'
  | 'diagnostics'
  | 'servers'
  | 'reports'
  | 'simulator';

interface SidebarProps {
  currentTab: NavigationTab;
  onSelectTab: (tab: NavigationTab) => void;
  openIncidentsCount: number;
}

export const Sidebar: React.FC<SidebarProps> = ({ currentTab, onSelectTab, openIncidentsCount }) => {
  const navItems = [
    {
      id: 'overview' as NavigationTab,
      label: 'Overview',
      icon: LayoutDashboard,
      badge: null
    },
    {
      id: 'monitoring' as NavigationTab,
      label: 'Infrastructure',
      icon: Activity,
      badge: 'Live'
    },
    {
      id: 'incidents' as NavigationTab,
      label: 'Incidents',
      icon: AlertTriangle,
      badge: openIncidentsCount > 0 ? openIncidentsCount.toString() : null,
      badgeColor: 'bg-rose-500/20 text-rose-300 border-rose-500/30'
    },
    {
      id: 'diagnostics' as NavigationTab,
      label: 'Troubleshooting',
      icon: Stethoscope,
      badge: null
    },
    {
      id: 'servers' as NavigationTab,
      label: 'Server Fleet',
      icon: Server,
      badge: null
    },
    {
      id: 'reports' as NavigationTab,
      label: 'Reports & MTTR',
      icon: FileBarChart2,
      badge: null
    },
    {
      id: 'simulator' as NavigationTab,
      label: 'Failure Simulator',
      icon: Flame,
      badge: 'Test Lab',
      badgeColor: 'bg-amber-500/20 text-amber-300 border-amber-500/30'
    }
  ];

  return (
    <aside className="w-64 border-r border-navy-700/60 bg-navy-900/60 flex flex-col justify-between py-4 select-none shrink-0">
      <div className="space-y-6">
        <div className="px-5">
          <p className="text-[10px] font-semibold tracking-wider text-slate-400 uppercase font-mono">
            Navigation
          </p>
        </div>

        <nav className="space-y-1 px-3">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onSelectTab(item.id)}
                className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium transition group ${
                  isActive
                    ? 'bg-gradient-to-r from-cyan-600/20 to-blue-600/10 text-cyan-300 border border-cyan-500/30 shadow-sm'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-navy-800/60'
                }`}
              >
                <div className="flex items-center space-x-3">
                  <Icon
                    className={`h-4 w-4 transition ${
                      isActive ? 'text-cyan-400' : 'text-slate-400 group-hover:text-slate-300'
                    }`}
                  />
                  <span>{item.label}</span>
                </div>

                {item.badge && (
                  <span
                    className={`text-[11px] px-2 py-0.5 rounded-full font-mono font-medium border ${
                      item.badgeColor || 'bg-navy-800 text-slate-400 border-navy-700'
                    }`}
                  >
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Footer system details */}
      <div className="px-4">
        <div className="p-3 rounded-lg bg-navy-800/50 border border-navy-700/50 space-y-1.5">
          <div className="flex items-center justify-between text-[11px]">
            <span className="text-slate-400">Agent Status</span>
            <span className="flex items-center text-emerald-400 font-mono">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse mr-1.5"></span>
              ACTIVE
            </span>
          </div>
          <div className="flex items-center justify-between text-[11px]">
            <span className="text-slate-400">Engine API</span>
            <span className="text-slate-300 font-mono text-[10px]">REST / JSON</span>
          </div>
        </div>
      </div>
    </aside>
  );
};

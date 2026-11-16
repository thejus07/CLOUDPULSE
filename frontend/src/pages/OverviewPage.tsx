import React from 'react';
import {
  Server as ServerIcon,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  AlertCircle,
  Clock,
  ArrowUpRight,
  TrendingUp,
  Cpu,
  HardDrive,
  Zap,
  Activity
} from 'lucide-react';
import { FleetSummary, Incident, Server } from '../types';

interface OverviewPageProps {
  summary: FleetSummary | null;
  servers: Server[];
  incidents: Incident[];
  onSelectServer: (serverId: string) => void;
  onSelectIncident: (incident: Incident) => void;
  onNavigateTab: (tab: any) => void;
}

export const OverviewPage: React.FC<OverviewPageProps> = ({
  summary,
  servers,
  incidents,
  onSelectServer,
  onSelectIncident,
  onNavigateTab
}) => {
  const fleet = summary?.fleet || {
    total_servers: servers.length,
    healthy_servers: servers.filter(s => s.status === 'HEALTHY').length,
    warning_servers: servers.filter(s => s.status === 'WARNING').length,
    critical_servers: servers.filter(s => s.status === 'CRITICAL').length
  };

  const openIncidents = incidents.filter(i => i.status !== 'RESOLVED');
  const recentIncidents = incidents.slice(0, 5);

  return (
    <div className="space-y-6">
      {/* Page Title & Quick Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Operations Center Overview</h1>
          <p className="text-sm text-slate-400">
            Real-time fleet telemetry, active incident management, and MTTR health analytics
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={() => onNavigateTab('simulator')}
            className="flex items-center space-x-2 px-3.5 py-2 rounded-lg bg-gradient-to-r from-amber-600 to-amber-500 hover:from-amber-500 hover:to-amber-400 text-white text-xs font-semibold shadow-lg shadow-amber-500/20 transition"
          >
            <Zap className="h-3.5 w-3.5" />
            <span>Launch Failure Scenario</span>
          </button>
          <button
            onClick={() => onNavigateTab('diagnostics')}
            className="flex items-center space-x-2 px-3.5 py-2 rounded-lg bg-navy-800 hover:bg-navy-700 text-cyan-300 border border-cyan-500/30 text-xs font-medium transition"
          >
            <Activity className="h-3.5 w-3.5" />
            <span>Run Diagnostics</span>
          </button>
        </div>
      </div>

      {/* Top Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Monitored Servers */}
        <div className="p-5 rounded-xl bg-navy-900/80 border border-navy-700/60 shadow-lg relative overflow-hidden group hover:border-cyan-500/40 transition">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider font-mono">
              Monitored Fleet
            </span>
            <div className="p-2 rounded-lg bg-navy-800 text-cyan-400">
              <ServerIcon className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline space-x-2">
            <span className="text-3xl font-bold text-white font-mono">{fleet.total_servers}</span>
            <span className="text-xs text-slate-400">active hosts</span>
          </div>
          <div className="mt-3 flex items-center space-x-3 text-xs">
            <span className="text-emerald-400 flex items-center">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 mr-1.5"></span>
              {fleet.healthy_servers} Healthy
            </span>
            {fleet.warning_servers > 0 && (
              <span className="text-amber-400 flex items-center">
                <span className="h-1.5 w-1.5 rounded-full bg-amber-400 mr-1.5"></span>
                {fleet.warning_servers} Warning
              </span>
            )}
            {fleet.critical_servers > 0 && (
              <span className="text-rose-400 flex items-center">
                <span className="h-1.5 w-1.5 rounded-full bg-rose-400 mr-1.5"></span>
                {fleet.critical_servers} Critical
              </span>
            )}
          </div>
        </div>

        {/* Active Incidents */}
        <div className="p-5 rounded-xl bg-navy-900/80 border border-navy-700/60 shadow-lg relative overflow-hidden group hover:border-rose-500/40 transition">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider font-mono">
              Active Incidents
            </span>
            <div className="p-2 rounded-lg bg-navy-800 text-rose-400">
              <AlertTriangle className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline space-x-2">
            <span className="text-3xl font-bold text-white font-mono">{openIncidents.length}</span>
            <span className="text-xs text-slate-400">open tickets</span>
          </div>
          <div className="mt-3 flex items-center text-xs text-slate-400">
            {openIncidents.filter(i => i.severity === 'CRITICAL').length > 0 ? (
              <span className="text-rose-400 font-semibold">
                {openIncidents.filter(i => i.severity === 'CRITICAL').length} Critical severity requiring triage
              </span>
            ) : (
              <span className="text-emerald-400">Zero critical severity outages</span>
            )}
          </div>
        </div>

        {/* Resolved Incidents */}
        <div className="p-5 rounded-xl bg-navy-900/80 border border-navy-700/60 shadow-lg relative overflow-hidden group hover:border-emerald-500/40 transition">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider font-mono">
              Resolved Incidents
            </span>
            <div className="p-2 rounded-lg bg-navy-800 text-emerald-400">
              <CheckCircle2 className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline space-x-2">
            <span className="text-3xl font-bold text-white font-mono">
              {summary?.incidents.resolved || incidents.filter(i => i.status === 'RESOLVED').length}
            </span>
            <span className="text-xs text-slate-400">recovered</span>
          </div>
          <div className="mt-3 text-xs text-slate-400">
            Total incidents: <span className="font-mono text-slate-200">{summary?.incidents.total || incidents.length}</span>
          </div>
        </div>

        {/* Mean Time To Recovery (MTTR) */}
        <div className="p-5 rounded-xl bg-navy-900/80 border border-navy-700/60 shadow-lg relative overflow-hidden group hover:border-cyan-500/40 transition">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider font-mono">
              Mean Time to Recovery
            </span>
            <div className="p-2 rounded-lg bg-navy-800 text-cyan-400">
              <Clock className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline space-x-2">
            <span className="text-3xl font-bold text-white font-mono">
              {summary?.incidents.mttr_minutes || 0.0}
            </span>
            <span className="text-xs text-slate-400">minutes MTTR</span>
          </div>
          <div className="mt-3 text-xs text-emerald-400 flex items-center">
            <TrendingUp className="h-3.5 w-3.5 mr-1" />
            <span>Autonomous remediation enabled</span>
          </div>
        </div>
      </div>

      {/* Main Split: Monitored Servers Grid & Recent Incident Stream */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Monitored Servers Health View */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-semibold text-white flex items-center space-x-2">
              <ServerIcon className="h-4 w-4 text-cyan-400" />
              <span>Fleet Server Health</span>
            </h2>
            <button
              onClick={() => onNavigateTab('servers')}
              className="text-xs font-medium text-cyan-400 hover:text-cyan-300 flex items-center space-x-1 transition"
            >
              <span>View all ({servers.length})</span>
              <ArrowUpRight className="h-3.5 w-3.5" />
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {servers.slice(0, 4).map((server) => {
              const isHealthy = server.status === 'HEALTHY';
              const isCritical = server.status === 'CRITICAL';
              const isWarning = server.status === 'WARNING';

              return (
                <div
                  key={server.id}
                  onClick={() => onSelectServer(server.id)}
                  className="p-4 rounded-xl bg-navy-900/70 border border-navy-700/60 hover:border-cyan-500/50 hover:bg-navy-850 cursor-pointer transition shadow-md group"
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className="font-semibold text-white group-hover:text-cyan-300 transition text-sm">
                          {server.hostname}
                        </span>
                        {server.is_local && (
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-navy-800 text-slate-400 font-mono">
                            local
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-slate-400 font-mono mt-0.5">{server.id}</p>
                    </div>

                    <span
                      className={`text-[10px] px-2 py-0.5 rounded-full font-mono font-medium border ${
                        isCritical
                          ? 'bg-rose-950/80 text-rose-300 border-rose-800'
                          : isWarning
                          ? 'bg-amber-950/80 text-amber-300 border-amber-800'
                          : 'bg-emerald-950/80 text-emerald-300 border-emerald-800'
                      }`}
                    >
                      {server.status}
                    </span>
                  </div>

                  {/* Specs */}
                  <div className="mt-4 grid grid-cols-3 gap-2 text-center text-xs border-t border-navy-800/80 pt-3">
                    <div>
                      <span className="text-[10px] text-slate-400 block">CORES</span>
                      <span className="font-mono text-slate-200 font-medium">{server.cpu_cores}</span>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-400 block">MEMORY</span>
                      <span className="font-mono text-slate-200 font-medium">
                        {Math.round(server.total_memory_mb / 1024)} GB
                      </span>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-400 block">DISK</span>
                      <span className="font-mono text-slate-200 font-medium">
                        {Math.round(server.total_disk_gb)} GB
                      </span>
                    </div>
                  </div>

                  <div className="mt-3 flex items-center justify-between text-[11px] text-slate-400">
                    <span>OS: {server.os_name} {server.os_version?.slice(0, 14)}</span>
                    <span className="text-cyan-400 group-hover:translate-x-0.5 transition flex items-center">
                      Inspect &rarr;
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Live Incident Stream */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-semibold text-white flex items-center space-x-2">
              <AlertTriangle className="h-4 w-4 text-rose-400" />
              <span>Active Incidents</span>
            </h2>
            <button
              onClick={() => onNavigateTab('incidents')}
              className="text-xs font-medium text-cyan-400 hover:text-cyan-300 flex items-center space-x-1 transition"
            >
              <span>View all ({incidents.length})</span>
              <ArrowUpRight className="h-3.5 w-3.5" />
            </button>
          </div>

          <div className="space-y-3">
            {recentIncidents.length === 0 ? (
              <div className="p-6 rounded-xl bg-navy-900/50 border border-navy-700/60 text-center">
                <CheckCircle2 className="h-8 w-8 text-emerald-400 mx-auto mb-2 opacity-80" />
                <p className="text-sm font-medium text-slate-200">All systems operational</p>
                <p className="text-xs text-slate-400 mt-1">No active incidents detected across the fleet</p>
              </div>
            ) : (
              recentIncidents.map((incident) => {
                const isResolved = incident.status === 'RESOLVED';
                const isCritical = incident.severity === 'CRITICAL';
                const isHigh = incident.severity === 'HIGH';

                return (
                  <div
                    key={incident.id}
                    onClick={() => onSelectIncident(incident)}
                    className="p-3.5 rounded-xl bg-navy-900/80 border border-navy-700/60 hover:border-navy-600 cursor-pointer transition shadow-sm space-y-2"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-xs text-cyan-400 font-semibold">{incident.id}</span>
                      <div className="flex items-center space-x-1.5">
                        <span
                          className={`text-[10px] px-2 py-0.5 rounded-full font-mono font-medium border ${
                            isCritical
                              ? 'bg-rose-950 text-rose-300 border-rose-800'
                              : isHigh
                              ? 'bg-amber-950 text-amber-300 border-amber-800'
                              : 'bg-navy-800 text-slate-300 border-navy-700'
                          }`}
                        >
                          {incident.severity}
                        </span>
                        <span
                          className={`text-[10px] px-2 py-0.5 rounded-full font-mono font-medium ${
                            isResolved
                              ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                              : 'bg-blue-950 text-blue-400 border border-blue-800'
                          }`}
                        >
                          {incident.status}
                        </span>
                      </div>
                    </div>

                    <h3 className="text-xs font-semibold text-slate-200 line-clamp-1">{incident.title}</h3>
                    <p className="text-[11px] text-slate-400 line-clamp-1">{incident.description}</p>

                    <div className="flex items-center justify-between text-[10px] text-slate-400 border-t border-navy-800 pt-2 font-mono">
                      <span>{incident.server_id}</span>
                      <span>{incident.detected_at?.slice(11, 19)} UTC</span>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

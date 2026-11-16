import React from 'react';
import {
  FileBarChart2,
  Download,
  Clock,
  CheckCircle2,
  AlertTriangle,
  TrendingDown,
  PieChart as PieChartIcon,
  ShieldCheck,
  FileText
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
  PieChart,
  Pie
} from 'recharts';
import { FleetSummary, Incident } from '../types';
import { api } from '../services/api';

interface ReportsPageProps {
  summary: FleetSummary | null;
  incidents: Incident[];
}

export const ReportsPage: React.FC<ReportsPageProps> = ({ summary, incidents }) => {
  const sevDist = summary?.incidents.severity_distribution || {
    CRITICAL: 0,
    HIGH: 0,
    MEDIUM: 0,
    LOW: 0,
    INFO: 0
  };

  const severityChartData = [
    { name: 'Critical', value: sevDist.CRITICAL, color: '#F43F5E' },
    { name: 'High', value: sevDist.HIGH, color: '#F59E0B' },
    { name: 'Medium', value: sevDist.MEDIUM, color: '#3B82F6' },
    { name: 'Low', value: sevDist.LOW, color: '#10B981' },
    { name: 'Info', value: sevDist.INFO, color: '#64748B' }
  ].filter(d => d.value > 0);

  const resolvedIncidents = incidents.filter(i => i.status === 'RESOLVED');

  const resolutionTimeData = resolvedIncidents.slice(0, 10).map((inc) => ({
    id: inc.id.slice(-4),
    title: inc.title.slice(0, 18),
    seconds: inc.resolution_time_seconds || 15
  }));

  const handleDownload = (format: 'json' | 'csv') => {
    window.open(api.getExportUrl(format), '_blank');
  };

  return (
    <div className="space-y-6">
      {/* Header & Export Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center space-x-2">
            <FileBarChart2 className="h-6 w-6 text-cyan-400" />
            <span>Infrastructure Reliability & MTTR Reports</span>
          </h1>
          <p className="text-sm text-slate-400">
            System uptime analysis, incident resolution efficiency, and audit reporting
          </p>
        </div>

        {/* Export Buttons */}
        <div className="flex items-center space-x-3">
          <button
            onClick={() => handleDownload('csv')}
            className="flex items-center space-x-2 px-3.5 py-2 rounded-lg bg-navy-800 hover:bg-navy-700 text-slate-200 border border-navy-700 text-xs font-semibold transition"
          >
            <Download className="h-3.5 w-3.5 text-cyan-400" />
            <span>Export CSV</span>
          </button>
          <button
            onClick={() => handleDownload('json')}
            className="flex items-center space-x-2 px-3.5 py-2 rounded-lg bg-navy-800 hover:bg-navy-700 text-slate-200 border border-navy-700 text-xs font-semibold transition"
          >
            <Download className="h-3.5 w-3.5 text-purple-400" />
            <span>Export JSON</span>
          </button>
        </div>
      </div>

      {/* KPI Highlight Strip */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {/* MTTR */}
        <div className="p-5 rounded-xl bg-navy-900/80 border border-navy-700/60 shadow-lg">
          <span className="text-xs font-mono uppercase text-slate-400">Mean Time to Recovery (MTTR)</span>
          <div className="mt-2 flex items-baseline space-x-2">
            <span className="text-3xl font-bold font-mono text-cyan-400">
              {summary?.incidents.mttr_minutes || 0.0}
            </span>
            <span className="text-xs text-slate-400">minutes</span>
          </div>
          <p className="text-xs text-slate-400 mt-2">Target SLA: &lt; 15.0 minutes</p>
        </div>

        {/* Total Incidents */}
        <div className="p-5 rounded-xl bg-navy-900/80 border border-navy-700/60 shadow-lg">
          <span className="text-xs font-mono uppercase text-slate-400">Total Recorded Outages</span>
          <div className="mt-2 flex items-baseline space-x-2">
            <span className="text-3xl font-bold font-mono text-white">
              {summary?.incidents.total || incidents.length}
            </span>
            <span className="text-xs text-slate-400">tickets</span>
          </div>
          <p className="text-xs text-slate-400 mt-2">
            {summary?.incidents.resolved || resolvedIncidents.length} successfully mitigated
          </p>
        </div>

        {/* Resolution Rate */}
        <div className="p-5 rounded-xl bg-navy-900/80 border border-navy-700/60 shadow-lg">
          <span className="text-xs font-mono uppercase text-slate-400">Autonomous Mitigation Rate</span>
          <div className="mt-2 flex items-baseline space-x-2">
            <span className="text-3xl font-bold font-mono text-emerald-400">
              {incidents.length > 0
                ? `${Math.round((resolvedIncidents.length / incidents.length) * 100)}%`
                : '100%'}
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-2">Zero human intervention for allowlisted recovery</p>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Resolution Time Per Incident */}
        <div className="p-5 rounded-xl bg-navy-900/80 border border-navy-700/60 shadow-lg space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white flex items-center space-x-2">
              <Clock className="h-4 w-4 text-cyan-400" />
              <span>Incident Recovery Duration (Seconds)</span>
            </h3>
            <span className="text-[11px] font-mono text-slate-400">Recent 10 resolved</span>
          </div>

          <div className="h-64 w-full pt-2">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={resolutionTimeData}>
                <XAxis dataKey="id" stroke="#64748B" fontSize={10} tickLine={false} />
                <YAxis stroke="#64748B" fontSize={10} tickLine={false} unit="s" />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0B0F19', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }}
                />
                <Bar dataKey="seconds" fill="#06B6D4" radius={[4, 4, 0, 0]} name="Recovery Time (s)" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Severity Distribution */}
        <div className="p-5 rounded-xl bg-navy-900/80 border border-navy-700/60 shadow-lg space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white flex items-center space-x-2">
              <PieChartIcon className="h-4 w-4 text-purple-400" />
              <span>Incident Severity Distribution</span>
            </h3>
            <span className="text-[11px] font-mono text-slate-400">By impact level</span>
          </div>

          <div className="h-64 w-full flex items-center justify-center">
            {severityChartData.length === 0 ? (
              <span className="text-xs text-slate-400">No incident severity data yet</span>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={severityChartData}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    innerRadius={50}
                    label={(entry) => `${entry.name}: ${entry.value}`}
                  >
                    {severityChartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0B0F19', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }}
                  />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

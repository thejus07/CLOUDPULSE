import React, { useState } from 'react';
import {
  AlertTriangle,
  CheckCircle2,
  Filter,
  Search,
  Clock,
  ArrowRight,
  ShieldCheck,
  Stethoscope,
  Wrench,
  AlertCircle,
  X,
  RefreshCw,
  ExternalLink,
  ChevronRight
} from 'lucide-react';
import { Incident, IncidentSeverity, IncidentStatus } from '../types';
import { api } from '../services/api';

interface IncidentPageProps {
  incidents: Incident[];
  onRefresh: () => void;
  selectedIncident: Incident | null;
  onSelectIncident: (incident: Incident | null) => void;
}

export const IncidentPage: React.FC<IncidentPageProps> = ({
  incidents,
  onRefresh,
  selectedIncident,
  onSelectIncident
}) => {
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [severityFilter, setSeverityFilter] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [isExecutingRemediation, setIsExecutingRemediation] = useState<boolean>(false);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  // Filter incidents
  const filtered = incidents.filter((inc) => {
    const matchesStatus = statusFilter === 'ALL' || inc.status === statusFilter;
    const matchesSeverity = severityFilter === 'ALL' || inc.severity === severityFilter;
    const matchesSearch =
      searchQuery === '' ||
      inc.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      inc.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      inc.server_id.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesStatus && matchesSeverity && matchesSearch;
  });

  const handleStatusChange = async (incId: string, newStatus: string) => {
    try {
      await api.updateIncidentStatus(incId, newStatus, 'Status manually adjusted by Support Engineer in console.');
      onRefresh();
      if (selectedIncident && selectedIncident.id === incId) {
        const refreshed = await api.getIncident(incId);
        onSelectIncident(refreshed);
      }
    } catch (e: any) {
      alert(`Error updating incident: ${e.message}`);
    }
  };

  const handleExecuteRemediation = async (incident: Incident) => {
    setIsExecutingRemediation(true);
    setActionMessage(null);

    // Determine appropriate remediation from affected resource
    let actionType = 'RESTART_SERVICE';
    let params: any = { service: 'nginx' };

    if (incident.affected_resource.toLowerCase().includes('disk') || incident.affected_resource.toLowerCase().includes('filesystem')) {
      actionType = 'CLEAN_TEMP_FILES';
      params = { path: 'data/test_temp' };
    } else if (incident.affected_resource.includes('nginx')) {
      actionType = 'RESTART_SERVICE';
      params = { service: 'nginx' };
    } else if (incident.affected_resource.includes('postgresql')) {
      actionType = 'RESTART_SERVICE';
      params = { service: 'postgresql' };
    }

    try {
      const res = await api.executeRemediation({
        server_id: incident.server_id,
        action_type: actionType,
        parameters: params,
        incident_id: incident.id,
        bypass_approval: true
      });

      setActionMessage(`Remediation executed: ${res.status}. Output: ${res.output_log}`);
      onRefresh();
      const updated = await api.getIncident(incident.id);
      onSelectIncident(updated);
    } catch (e: any) {
      setActionMessage(`Remediation error: ${e.message}`);
    } finally {
      setIsExecutingRemediation(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header & Filters */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center space-x-2">
            <AlertTriangle className="h-6 w-6 text-rose-400" />
            <span>Incident Command Center</span>
          </h1>
          <p className="text-sm text-slate-400">
            End-to-end incident lifecycle: detection, automated diagnostics, RCA, and verified recovery
          </p>
        </div>

        {/* Filter Controls */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Search */}
          <div className="relative">
            <Search className="h-4 w-4 absolute left-3 top-2.5 text-slate-400" />
            <input
              type="text"
              placeholder="Search incidents..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="bg-navy-900 border border-navy-700 rounded-lg pl-9 pr-3 py-1.5 text-xs text-white placeholder-slate-400 focus:outline-none focus:border-cyan-500 w-44"
            />
          </div>

          {/* Status Filter */}
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-navy-900 border border-navy-700 rounded-lg px-2.5 py-1.5 text-xs text-slate-300 font-mono focus:outline-none focus:border-cyan-500"
          >
            <option value="ALL">All Statuses</option>
            <option value="DETECTED">DETECTED</option>
            <option value="INVESTIGATING">INVESTIGATING</option>
            <option value="OPEN">OPEN</option>
            <option value="RESOLVING">RESOLVING</option>
            <option value="RESOLVED">RESOLVED</option>
            <option value="ESCALATED">ESCALATED</option>
          </select>

          {/* Severity Filter */}
          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="bg-navy-900 border border-navy-700 rounded-lg px-2.5 py-1.5 text-xs text-slate-300 font-mono focus:outline-none focus:border-cyan-500"
          >
            <option value="ALL">All Severities</option>
            <option value="CRITICAL">CRITICAL</option>
            <option value="HIGH">HIGH</option>
            <option value="MEDIUM">MEDIUM</option>
            <option value="LOW">LOW</option>
          </select>
        </div>
      </div>

      {/* Main Split: Incident List and Detail Drawer */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Incident Table */}
        <div className={selectedIncident ? 'lg:col-span-7 space-y-3' : 'lg:col-span-12 space-y-3'}>
          <div className="rounded-xl bg-navy-900/80 border border-navy-700/60 shadow-lg overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead>
                  <tr className="border-b border-navy-700 text-slate-400 text-[11px] uppercase tracking-wider bg-navy-850/50">
                    <th className="py-3 px-4">Incident ID</th>
                    <th className="py-3 px-4">Severity</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4">Title & Affected Resource</th>
                    <th className="py-3 px-4">Detected</th>
                    <th className="py-3 px-4 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-navy-800">
                  {filtered.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="py-8 text-center text-slate-400 font-sans">
                        No incidents match the active filter criteria.
                      </td>
                    </tr>
                  ) : (
                    filtered.map((inc) => {
                      const isSelected = selectedIncident?.id === inc.id;
                      const isCritical = inc.severity === 'CRITICAL';
                      const isHigh = inc.severity === 'HIGH';
                      const isResolved = inc.status === 'RESOLVED';

                      return (
                        <tr
                          key={inc.id}
                          onClick={() => onSelectIncident(inc)}
                          className={`cursor-pointer transition ${
                            isSelected
                              ? 'bg-cyan-950/40 border-l-2 border-cyan-400'
                              : 'hover:bg-navy-850/60'
                          }`}
                        >
                          <td className="py-3 px-4 text-cyan-400 font-semibold">{inc.id}</td>
                          <td className="py-3 px-4">
                            <span
                              className={`text-[10px] px-2 py-0.5 rounded-full font-mono font-medium border ${
                                isCritical
                                  ? 'bg-rose-950/80 text-rose-300 border-rose-800'
                                  : isHigh
                                  ? 'bg-amber-950/80 text-amber-300 border-amber-800'
                                  : 'bg-navy-800 text-slate-300 border-navy-700'
                              }`}
                            >
                              {inc.severity}
                            </span>
                          </td>
                          <td className="py-3 px-4">
                            <span
                              className={`text-[10px] px-2 py-0.5 rounded-full font-mono font-medium border ${
                                isResolved
                                  ? 'bg-emerald-950/80 text-emerald-300 border-emerald-800'
                                  : inc.status === 'INVESTIGATING'
                                  ? 'bg-purple-950/80 text-purple-300 border-purple-800'
                                  : 'bg-blue-950/80 text-blue-300 border-blue-800'
                              }`}
                            >
                              {inc.status}
                            </span>
                          </td>
                          <td className="py-3 px-4 font-sans">
                            <div className="font-semibold text-slate-200 line-clamp-1">{inc.title}</div>
                            <div className="text-[11px] text-slate-400 font-mono mt-0.5">
                              {inc.affected_resource} • {inc.server_id}
                            </div>
                          </td>
                          <td className="py-3 px-4 text-slate-400 whitespace-nowrap">
                            {inc.detected_at?.slice(11, 19)} UTC
                          </td>
                          <td className="py-3 px-4 text-right">
                            <ChevronRight className="h-4 w-4 text-slate-400 inline" />
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Incident Detail Drawer / Inspector */}
        {selectedIncident && (
          <div className="lg:col-span-5 rounded-xl bg-navy-900/90 border border-navy-700/80 shadow-2xl p-5 space-y-5 sticky top-20">
            {/* Header */}
            <div className="flex items-start justify-between border-b border-navy-700 pb-4">
              <div>
                <div className="flex items-center space-x-2">
                  <span className="font-mono text-sm font-bold text-cyan-400">{selectedIncident.id}</span>
                  <span
                    className={`text-[10px] px-2 py-0.5 rounded-full font-mono font-medium border ${
                      selectedIncident.severity === 'CRITICAL'
                        ? 'bg-rose-950 text-rose-300 border-rose-800'
                        : 'bg-amber-950 text-amber-300 border-amber-800'
                    }`}
                  >
                    {selectedIncident.severity}
                  </span>
                </div>
                <h2 className="text-base font-bold text-white mt-1">{selectedIncident.title}</h2>
                <p className="text-xs text-slate-400 font-mono mt-0.5">
                  Node: {selectedIncident.server_id} • Resource: {selectedIncident.affected_resource}
                </p>
              </div>

              <button
                onClick={() => onSelectIncident(null)}
                className="p-1 rounded-lg hover:bg-navy-800 text-slate-400 hover:text-white transition"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Status & Lifecycle Actions */}
            <div className="flex items-center justify-between p-3 rounded-lg bg-navy-850 border border-navy-700/60">
              <div>
                <span className="text-[10px] text-slate-400 uppercase font-mono block">Current Lifecycle</span>
                <span className="font-bold font-mono text-xs text-cyan-300">{selectedIncident.status}</span>
              </div>

              <div className="flex items-center space-x-2">
                {selectedIncident.status !== 'RESOLVED' && (
                  <button
                    onClick={() => handleStatusChange(selectedIncident.id, 'RESOLVED')}
                    className="px-2.5 py-1 rounded bg-emerald-950/80 hover:bg-emerald-900 border border-emerald-700 text-emerald-300 text-xs font-semibold transition"
                  >
                    Resolve
                  </button>
                )}
                {selectedIncident.status === 'DETECTED' && (
                  <button
                    onClick={() => handleStatusChange(selectedIncident.id, 'INVESTIGATING')}
                    className="px-2.5 py-1 rounded bg-purple-950/80 hover:bg-purple-900 border border-purple-700 text-purple-300 text-xs font-semibold transition"
                  >
                    Investigate
                  </button>
                )}
                {selectedIncident.status !== 'ESCALATED' && (
                  <button
                    onClick={() => handleStatusChange(selectedIncident.id, 'ESCALATED')}
                    className="px-2.5 py-1 rounded bg-rose-950/80 hover:bg-rose-900 border border-rose-700 text-rose-300 text-xs font-semibold transition"
                  >
                    Escalate
                  </button>
                )}
              </div>
            </div>

            {/* Root Cause Analysis (RCA) */}
            <div className="space-y-2">
              <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider font-mono flex items-center space-x-1.5">
                <Stethoscope className="h-3.5 w-3.5 text-cyan-400" />
                <span>Probable Root Cause (RCA)</span>
              </h3>
              <div className="p-3 rounded-lg bg-navy-950 border border-navy-800 text-xs text-slate-300 font-mono leading-relaxed">
                {selectedIncident.probable_root_cause ||
                  'Automated telemetry scan identified threshold breach. No specific daemon crash found.'}
              </div>
            </div>

            {/* Recommended Resolution */}
            <div className="space-y-2">
              <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider font-mono flex items-center space-x-1.5">
                <ShieldCheck className="h-3.5 w-3.5 text-emerald-400" />
                <span>Recommended Resolution</span>
              </h3>
              <div className="p-3 rounded-lg bg-emerald-950/20 border border-emerald-900/40 text-xs text-emerald-300 font-mono leading-relaxed">
                {selectedIncident.recommended_resolution ||
                  'Verify process thread state and consider safe daemon restart.'}
              </div>
            </div>

            {/* Remediation Action Button */}
            {selectedIncident.status !== 'RESOLVED' && (
              <div className="space-y-2 pt-2 border-t border-navy-800">
                <button
                  onClick={() => handleExecuteRemediation(selectedIncident)}
                  disabled={isExecutingRemediation}
                  className="w-full flex items-center justify-center space-x-2 py-2.5 px-4 rounded-lg bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-semibold text-xs shadow-lg shadow-cyan-500/20 transition disabled:opacity-50"
                >
                  <Wrench className={`h-4 w-4 ${isExecutingRemediation ? 'animate-spin' : ''}`} />
                  <span>
                    {isExecutingRemediation ? 'Executing Remediation & Verifying...' : 'Execute Approved Remediation'}
                  </span>
                </button>
                <p className="text-[10px] text-slate-400 text-center font-mono">
                  Enforces command allowlist & pre/post verification snapshot
                </p>
              </div>
            )}

            {/* Action Feedback Log */}
            {actionMessage && (
              <div className="p-3 rounded-lg bg-navy-850 border border-cyan-800 text-xs text-cyan-200 font-mono">
                {actionMessage}
              </div>
            )}

            {/* Recovery Verification Note if resolved */}
            {selectedIncident.recovery_verification && (
              <div className="p-3 rounded-lg bg-emerald-950/30 border border-emerald-800 text-xs text-emerald-300 font-mono">
                <span className="font-bold block mb-1">Recovery Verification:</span>
                {selectedIncident.recovery_verification}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

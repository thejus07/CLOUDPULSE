import React, { useState } from 'react';
import {
  Stethoscope,
  Cpu,
  Layers,
  HardDrive,
  Server,
  Network,
  Play,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Terminal,
  Activity,
  Code2
} from 'lucide-react';
import { Server as ServerType, DiagnosticReport } from '../types';
import { api } from '../services/api';

interface DiagnosticsPageProps {
  servers: ServerType[];
}

export const DiagnosticsPage: React.FC<DiagnosticsPageProps> = ({ servers }) => {
  const [selectedServerId, setSelectedServerId] = useState<string>(servers[0]?.id || 'srv-local-01');
  const [diagnosticType, setDiagnosticType] = useState<string>('COMPREHENSIVE');
  const [customPath, setCustomPath] = useState<string>('');
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [activeReport, setActiveReport] = useState<any | null>(null);
  const [error, setError] = useState<string | null>(null);

  const diagnosticModules = [
    {
      id: 'COMPREHENSIVE',
      name: 'Full Health Sweep',
      icon: Activity,
      desc: 'Orchestrates CPU, Memory, Disk, Services, and Network tests concurrently'
    },
    {
      id: 'CPU',
      name: 'CPU Saturation & Runaway Scan',
      icon: Cpu,
      desc: 'Inspects top CPU thread consumption, load averages, and core balancing'
    },
    {
      id: 'MEMORY',
      name: 'Memory Pressure & OOM Analysis',
      icon: Layers,
      desc: 'Diagnoses buffer cache, swap exhaustion, and process RSS leaks'
    },
    {
      id: 'DISK',
      name: 'Filesystem & Inode Exhaustion',
      icon: HardDrive,
      desc: 'Analyzes partition space, large directories, and inode table saturation'
    },
    {
      id: 'SERVICE',
      name: 'Systemd Unit & Journalctl Logs',
      icon: Server,
      desc: 'Queries systemctl unit states, failed services, and log exit code signatures'
    },
    {
      id: 'NETWORK',
      name: 'DNS & Connectivity Stack',
      icon: Network,
      desc: 'Validates DNS latency, socket handshake, and HTTP endpoint health'
    }
  ];

  const handleRunDiagnostic = async () => {
    setIsRunning(true);
    setError(null);
    setActiveReport(null);

    const params: any = {};
    if (diagnosticType === 'DISK' && customPath) {
      params.path = customPath;
    }

    try {
      const res = await api.runDiagnostic({
        diagnostic_type: diagnosticType,
        server_id: selectedServerId,
        params
      });
      setActiveReport(res);
    } catch (e: any) {
      setError(e.message || 'Diagnostic execution failed.');
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white flex items-center space-x-2">
          <Stethoscope className="h-6 w-6 text-cyan-400" />
          <span>Automated Troubleshooting Engine</span>
        </h1>
        <p className="text-sm text-slate-400">
          Independent diagnostic modules performing forensic root-cause analysis across Linux systems
        </p>
      </div>

      {/* Target Node & Module Selection Card */}
      <div className="p-5 rounded-xl bg-navy-900/80 border border-navy-700/60 shadow-lg space-y-5">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label htmlFor="diag-target-node" className="text-xs font-mono uppercase text-slate-400 block mb-1.5">
              1. Select Target Node
            </label>
            <select
              id="diag-target-node"
              value={selectedServerId}
              onChange={(e) => setSelectedServerId(e.target.value)}
              className="w-full bg-navy-800 border border-navy-700 rounded-lg p-2.5 text-sm font-semibold text-white focus:outline-none focus:border-cyan-500 font-mono"
            >
              {servers.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.hostname} ({s.id}) - {s.os_name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-xs font-mono uppercase text-slate-400 block mb-1.5">
              2. Optional Path / Scope Override
            </label>
            <input
              type="text"
              placeholder="e.g. data/test_temp or /var/log"
              value={customPath}
              onChange={(e) => setCustomPath(e.target.value)}
              className="w-full bg-navy-800 border border-navy-700 rounded-lg p-2.5 text-sm text-white placeholder-slate-400 focus:outline-none focus:border-cyan-500 font-mono"
            />
          </div>
        </div>

        {/* Diagnostic Module Grid */}
        <div>
          <label className="text-xs font-mono uppercase text-slate-400 block mb-3">
            3. Choose Diagnostic Routine
          </label>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {diagnosticModules.map((mod) => {
              const Icon = mod.icon;
              const isSelected = diagnosticType === mod.id;

              return (
                <div
                  key={mod.id}
                  onClick={() => setDiagnosticType(mod.id)}
                  className={`p-3.5 rounded-lg border cursor-pointer transition flex flex-col justify-between ${
                    isSelected
                      ? 'bg-cyan-950/40 border-cyan-500 shadow-md shadow-cyan-500/10'
                      : 'bg-navy-850/60 border-navy-700/70 hover:border-navy-600'
                  }`}
                >
                  <div className="flex items-center space-x-3 mb-2">
                    <div className={`p-2 rounded-lg ${isSelected ? 'bg-cyan-600 text-white' : 'bg-navy-800 text-slate-400'}`}>
                      <Icon className="h-4 w-4" />
                    </div>
                    <span className="font-semibold text-xs text-white">{mod.name}</span>
                  </div>
                  <p className="text-[11px] text-slate-400 leading-normal">{mod.desc}</p>
                </div>
              );
            })}
          </div>
        </div>

        {/* Run Button */}
        <div className="pt-2 flex justify-end">
          <button
            onClick={handleRunDiagnostic}
            disabled={isRunning}
            className="flex items-center space-x-2 px-5 py-2.5 rounded-lg bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-semibold text-sm shadow-lg shadow-cyan-500/25 transition disabled:opacity-50"
          >
            <Play className={`h-4 w-4 ${isRunning ? 'animate-spin' : ''}`} />
            <span>{isRunning ? 'Investigating Node...' : 'Run Diagnostics'}</span>
          </button>
        </div>
      </div>

      {/* Error state */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-800 text-rose-300 text-sm font-mono flex items-center space-x-2">
          <AlertTriangle className="h-4 w-4 text-rose-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Diagnostic Findings Output */}
      {activeReport && (
        <div className="p-5 rounded-xl bg-navy-900/90 border border-navy-700/80 shadow-2xl space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-navy-700 gap-2">
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-mono text-sm font-bold text-cyan-400">
                  {activeReport.id || 'SWEEP-COMPLETE'}
                </span>
                <span
                  className={`text-[10px] px-2 py-0.5 rounded-full font-mono font-bold border ${
                    activeReport.status === 'CRITICAL' || activeReport.overall_status === 'CRITICAL'
                      ? 'bg-rose-950 text-rose-300 border-rose-800'
                      : activeReport.status === 'WARNING' || activeReport.overall_status === 'WARNING'
                      ? 'bg-amber-950 text-amber-300 border-amber-800'
                      : 'bg-emerald-950 text-emerald-300 border-emerald-800'
                  }`}
                >
                  {activeReport.status || activeReport.overall_status || 'SUCCESS'}
                </span>
              </div>
              <p className="text-xs text-slate-400 font-mono mt-1">
                Target Node: {selectedServerId} • Execution Time:{' '}
                {activeReport.execution_duration_ms ? `${activeReport.execution_duration_ms} ms` : 'Nominal'}
              </p>
            </div>

            <div className="text-xs text-slate-400 font-mono flex items-center space-x-1.5">
              <Clock className="h-3.5 w-3.5 text-cyan-400" />
              <span>{new Date().toISOString().slice(11, 19)} UTC</span>
            </div>
          </div>

          {/* Probable Root Cause & Recommended Resolution */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 rounded-lg bg-navy-950 border border-navy-800 space-y-1.5">
              <h3 className="text-xs font-semibold text-cyan-300 uppercase tracking-wider font-mono flex items-center space-x-1.5">
                <AlertTriangle className="h-4 w-4 text-cyan-400" />
                <span>Identified Root Cause (RCA)</span>
              </h3>
              <p className="text-xs text-slate-200 font-mono leading-relaxed">
                {activeReport.probable_root_cause ||
                  'No critical anomalies found. Core metrics and system services are within acceptable thresholds.'}
              </p>
            </div>

            <div className="p-4 rounded-lg bg-emerald-950/20 border border-emerald-900/40 space-y-1.5">
              <h3 className="text-xs font-semibold text-emerald-300 uppercase tracking-wider font-mono flex items-center space-x-1.5">
                <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                <span>Recommended Engineering Action</span>
              </h3>
              <div className="text-xs text-emerald-300 font-mono leading-relaxed space-y-1">
                {activeReport.recommendations?.length ? (
                  activeReport.recommendations.map((rec: string, idx: number) => (
                    <div key={idx}>• {rec}</div>
                  ))
                ) : (
                  <div>• No immediate action required. Keep routine monitoring active.</div>
                )}
              </div>
            </div>
          </div>

          {/* Structured Findings JSON Tree */}
          <div className="space-y-2">
            <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider font-mono flex items-center space-x-1.5">
              <Code2 className="h-3.5 w-3.5 text-slate-400" />
              <span>Structured Diagnostic Payload (JSON)</span>
            </h3>
            <pre className="p-4 rounded-lg bg-navy-950 border border-navy-800 text-xs text-cyan-300 font-mono overflow-x-auto max-h-96">
              {JSON.stringify(activeReport.findings || activeReport.diagnostics || activeReport, null, 2)}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
};

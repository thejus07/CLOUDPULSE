import React, { useState, useEffect } from 'react';
import {
  Flame,
  Play,
  Square,
  AlertTriangle,
  Cpu,
  Layers,
  HardDrive,
  Server,
  Network,
  ShieldCheck,
  CheckCircle2,
  RefreshCw,
  Terminal,
  Zap
} from 'lucide-react';
import { api } from '../services/api';

interface SimulatorPageProps {
  onRefreshTelemetry: () => void;
  onNavigateTab: (tab: any) => void;
}

export const SimulatorPage: React.FC<SimulatorPageProps> = ({ onRefreshTelemetry, onNavigateTab }) => {
  const [activeSimulations, setActiveSimulations] = useState<any[]>([]);
  const [durationSeconds, setDurationSeconds] = useState<number>(30);
  const [loadingScenario, setLoadingScenario] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  const scenarios = [
    {
      id: 'CPU_STRESS',
      name: 'High CPU Utilization Anomaly',
      icon: Cpu,
      severity: 'CRITICAL',
      color: 'border-rose-500/40 hover:border-rose-500',
      description: 'Spawns a bounded CPU stress thread loop pushing host CPU above the 90% threshold.',
      recovery: 'Automated thread termination and workload throttling verification.'
    },
    {
      id: 'MEMORY_PRESSURE',
      name: 'High Memory Pressure & Leak',
      icon: Layers,
      severity: 'HIGH',
      color: 'border-purple-500/40 hover:border-purple-500',
      description: 'Safely allocates a temporary 200MB byte buffer to test memory pressure alerts and OOM protection.',
      recovery: 'Autonomous buffer garbage collection and process memory release.'
    },
    {
      id: 'DISK_PRESSURE',
      name: 'Filesystem Disk Saturation',
      icon: HardDrive,
      severity: 'CRITICAL',
      color: 'border-amber-500/40 hover:border-amber-500',
      description: 'Creates a temporary 30MB log bloat file inside allowlisted path (data/test_temp).',
      recovery: 'Approved CLEAN_TEMP_FILES remediation with pre/post disk space calculation.'
    },
    {
      id: 'SERVICE_DOWN',
      name: 'Critical Daemon Outage',
      icon: Server,
      severity: 'HIGH',
      color: 'border-rose-500/40 hover:border-rose-500',
      description: 'Forces nginx/test-service into degraded failed state to test systemd watchdog.',
      recovery: 'Allowlisted RESTART_SERVICE action with post-check systemctl is-active verification.'
    },
    {
      id: 'DNS_FAILURE',
      name: 'DNS Resolution Failure',
      icon: Network,
      severity: 'WARNING',
      color: 'border-cyan-500/40 hover:border-cyan-500',
      description: 'Simulates unreachable upstream nameserver and DNS resolver query timeout.',
      recovery: 'Automated resolver cache flush and nameserver fallback probe.'
    }
  ];

  const fetchActive = async () => {
    try {
      const data = await api.getSimulationStatus();
      setActiveSimulations(data);
    } catch {
      // no-op
    }
  };

  useEffect(() => {
    fetchActive();
    const interval = setInterval(fetchActive, 3000);
    return () => clearInterval(interval);
  }, []);

  const handleStart = async (scenarioId: string) => {
    setLoadingScenario(scenarioId);
    setStatusMessage(null);
    try {
      await api.startSimulation(scenarioId, durationSeconds);
      setStatusMessage(`Simulation '${scenarioId}' started for ${durationSeconds} seconds.`);
      fetchActive();
      onRefreshTelemetry();
    } catch (e: any) {
      setStatusMessage(`Failed to start: ${e.message}`);
    } finally {
      setLoadingScenario(null);
    }
  };

  const handleStop = async (scenarioId: string) => {
    setLoadingScenario(scenarioId);
    try {
      await api.stopSimulation(scenarioId);
      setStatusMessage(`Simulation '${scenarioId}' stopped and safe cleanup executed.`);
      fetchActive();
      onRefreshTelemetry();
    } catch (e: any) {
      setStatusMessage(`Failed to stop: ${e.message}`);
    } finally {
      setLoadingScenario(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center space-x-2">
            <Flame className="h-6 w-6 text-amber-400" />
            <span>Controlled Failure Simulator</span>
          </h1>
          <p className="text-sm text-slate-400">
            Safely inject controlled infrastructure faults to demonstrate real-time detection, RCA, and recovery
          </p>
        </div>

        {/* Global duration slider */}
        <div className="flex items-center space-x-3 bg-navy-900 border border-navy-700/80 p-2.5 rounded-xl">
          <label htmlFor="sim-duration-slider" className="text-xs font-mono text-slate-400">
            Duration: <span className="font-bold text-white">{durationSeconds}s</span>
          </label>
          <input
            id="sim-duration-slider"
            type="range"
            min="10"
            max="120"
            step="5"
            value={durationSeconds}
            onChange={(e) => setDurationSeconds(parseInt(e.target.value))}
            className="w-28 accent-cyan-400 cursor-pointer"
          />
        </div>
      </div>

      {/* Safety Banner */}
      <div className="p-4 rounded-xl bg-gradient-to-r from-amber-950/40 to-navy-900/80 border border-amber-800/60 shadow-lg flex items-start space-x-3">
        <ShieldCheck className="h-5 w-5 text-amber-400 shrink-0 mt-0.5" />
        <div className="text-xs text-slate-300 space-y-1">
          <div className="font-bold text-amber-300">Sandbox Safety Guarantees:</div>
          <p>
            All simulations are non-destructive, strictly time-bounded (auto-stop timers), and confined to designated
            test folders. No kernel panics, system crashes, or data deletion can occur.
          </p>
        </div>
      </div>

      {/* Feedback Message */}
      {statusMessage && (
        <div className="p-3.5 rounded-lg bg-navy-850 border border-cyan-800 text-xs text-cyan-200 font-mono flex items-center justify-between">
          <span>{statusMessage}</span>
          <button
            onClick={() => onNavigateTab('incidents')}
            className="text-xs underline text-cyan-400 font-sans ml-4"
          >
            View Generated Incidents &rarr;
          </button>
        </div>
      )}

      {/* Scenario Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {scenarios.map((sc) => {
          const Icon = sc.icon;
          const isRunning = activeSimulations.some((a) => a.scenario === sc.id);
          const activeEntry = activeSimulations.find((a) => a.scenario === sc.id);
          const isLoading = loadingScenario === sc.id;

          return (
            <div
              key={sc.id}
              className={`p-5 rounded-xl bg-navy-900/80 border shadow-lg transition flex flex-col justify-between ${sc.color} ${
                isRunning ? 'ring-2 ring-rose-500/50 glow-rose' : ''
              }`}
            >
              <div>
                <div className="flex items-start justify-between mb-3">
                  <div className="p-2.5 rounded-lg bg-navy-800 text-white">
                    <Icon className="h-5 w-5 text-amber-400" />
                  </div>
                  <div className="flex items-center space-x-1.5">
                    {isRunning && (
                      <span className="flex items-center text-[10px] font-mono px-2 py-0.5 rounded-full bg-rose-950 text-rose-300 border border-rose-800 animate-pulse">
                        <span className="h-1.5 w-1.5 rounded-full bg-rose-500 mr-1.5"></span>
                        {activeEntry ? `${activeEntry.remaining_seconds}s left` : 'RUNNING'}
                      </span>
                    )}
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-navy-800 text-slate-300 border border-navy-700">
                      {sc.severity}
                    </span>
                  </div>
                </div>

                <h3 className="font-bold text-white text-base">{sc.name}</h3>
                <p className="text-xs text-slate-400 mt-2 leading-relaxed">{sc.description}</p>

                <div className="mt-4 p-2.5 rounded-lg bg-navy-950 border border-navy-800/80 text-[11px] text-slate-300 font-mono">
                  <span className="text-cyan-400 font-semibold block mb-0.5">Automated Recovery:</span>
                  {sc.recovery}
                </div>
              </div>

              {/* Start / Stop Toggle Button */}
              <div className="mt-5 pt-3 border-t border-navy-800">
                {isRunning ? (
                  <button
                    onClick={() => handleStop(sc.id)}
                    disabled={isLoading}
                    className="w-full flex items-center justify-center space-x-2 py-2 px-4 rounded-lg bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold shadow-lg shadow-rose-600/30 transition"
                  >
                    <Square className="h-3.5 w-3.5" />
                    <span>Stop & Clean Up</span>
                  </button>
                ) : (
                  <button
                    onClick={() => handleStart(sc.id)}
                    disabled={isLoading}
                    className="w-full flex items-center justify-center space-x-2 py-2 px-4 rounded-lg bg-navy-800 hover:bg-navy-700 text-amber-300 border border-amber-500/30 text-xs font-semibold transition"
                  >
                    <Play className="h-3.5 w-3.5 text-amber-400" />
                    <span>Simulate ({durationSeconds}s)</span>
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

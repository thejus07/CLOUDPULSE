import React, { useState, useEffect } from 'react';
import {
  AreaChart,
  Area,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid
} from 'recharts';
import {
  Activity,
  Cpu,
  HardDrive,
  Network,
  Layers,
  Server as ServerIcon,
  RefreshCw,
  Clock,
  Terminal,
  CheckCircle2,
  AlertTriangle
} from 'lucide-react';
import { Server, SystemMetric } from '../types';
import { api } from '../services/api';

interface InfrastructurePageProps {
  servers: Server[];
  selectedServerId: string;
  onSelectServer: (id: string) => void;
}

export const InfrastructurePage: React.FC<InfrastructurePageProps> = ({
  servers,
  selectedServerId,
  onSelectServer
}) => {
  const [metrics, setMetrics] = useState<SystemMetric[]>([]);
  const [latestMetric, setLatestMetric] = useState<SystemMetric | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [activeProcessTab, setActiveProcessTab] = useState<'cpu' | 'memory'>('cpu');

  const fetchTelemetry = async () => {
    if (!selectedServerId) return;
    try {
      const data = await api.getMetrics(selectedServerId, 40);
      setMetrics(data);
      if (data.length > 0) {
        setLatestMetric(data[data.length - 1]);
      }
    } catch (e) {
      console.error('Failed to fetch telemetry:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTelemetry();
    const interval = setInterval(fetchTelemetry, 6000);
    return () => clearInterval(interval);
  }, [selectedServerId]);

  const selectedServer = servers.find((s) => s.id === selectedServerId) || servers[0];

  // Chart data formatting
  const chartData = metrics.map((m) => ({
    time: m.timestamp ? new Date(m.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }) : '',
    cpu: m.cpu_percent,
    memory: m.memory_percent,
    disk: m.disk_percent,
    net_rx_kb: Math.round(m.network_recv_bytes / 1024),
    net_tx_kb: Math.round(m.network_sent_bytes / 1024)
  }));

  const currentCpu = latestMetric?.cpu_percent ?? 0;
  const currentMem = latestMetric?.memory_percent ?? 0;
  const currentDisk = latestMetric?.disk_percent ?? 0;

  const processes = activeProcessTab === 'cpu'
    ? latestMetric?.raw_metrics?.processes?.top_cpu || []
    : latestMetric?.raw_metrics?.processes?.top_memory || [];

  return (
    <div className="space-y-6">
      {/* Top Bar: Server Picker & Live Specs */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 rounded-xl bg-navy-900/80 border border-navy-700/60 shadow-lg">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 rounded-lg bg-navy-800 text-cyan-400">
            <ServerIcon className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <label htmlFor="server-select" className="text-xs text-slate-400 font-medium">
                Monitored Node:
              </label>
              <select
                id="server-select"
                value={selectedServerId}
                onChange={(e) => onSelectServer(e.target.value)}
                className="bg-navy-800 border border-navy-700 rounded-lg px-2.5 py-1 text-sm font-semibold text-white focus:outline-none focus:border-cyan-500 font-mono"
              >
                {servers.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.hostname} ({s.id})
                  </option>
                ))}
              </select>
            </div>
            <p className="text-xs text-slate-400 font-mono mt-0.5">
              {selectedServer?.os_name} • {selectedServer?.os_version} • {selectedServer?.architecture}
            </p>
          </div>
        </div>

        {/* Real-time Status Badges */}
        <div className="flex items-center space-x-4">
          <div className="text-right">
            <div className="text-[10px] uppercase font-mono text-slate-400">Node Status</div>
            <div className="flex items-center space-x-1.5 font-semibold text-xs">
              <span className={`h-2 w-2 rounded-full ${selectedServer?.status === 'HEALTHY' ? 'bg-emerald-400' : 'bg-rose-400'}`}></span>
              <span className={selectedServer?.status === 'HEALTHY' ? 'text-emerald-400' : 'text-rose-400'}>
                {selectedServer?.status || 'HEALTHY'}
              </span>
            </div>
          </div>

          <div className="h-8 w-px bg-navy-700/60"></div>

          <button
            onClick={fetchTelemetry}
            className="p-2 rounded-lg bg-navy-800 hover:bg-navy-700 text-slate-300 transition border border-navy-700"
            title="Poll Now"
          >
            <RefreshCw className="h-4 w-4 text-cyan-400" />
          </button>
        </div>
      </div>

      {/* Live Resource Stat Counters */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {/* CPU */}
        <div className="p-4 rounded-xl bg-navy-900/80 border border-navy-700/60 shadow-md">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
            <span className="flex items-center space-x-1.5 font-mono">
              <Cpu className="h-4 w-4 text-cyan-400" />
              <span>CPU UTILIZATION</span>
            </span>
            <span className="font-mono text-slate-300">
              {selectedServer?.cpu_cores} Cores • Load: {latestMetric?.load_1m || 0}
            </span>
          </div>
          <div className="flex items-baseline space-x-2">
            <span className="text-3xl font-bold font-mono text-white">{currentCpu.toFixed(1)}%</span>
            <span className={`text-xs font-semibold ${currentCpu > 80 ? 'text-rose-400' : 'text-slate-400'}`}>
              {currentCpu > 80 ? 'Critical' : currentCpu > 65 ? 'Elevated' : 'Nominal'}
            </span>
          </div>
          {/* Progress bar */}
          <div className="mt-3 w-full bg-navy-800 rounded-full h-1.5 overflow-hidden">
            <div
              className={`h-full transition-all duration-500 ${
                currentCpu > 85 ? 'bg-rose-500' : currentCpu > 70 ? 'bg-amber-400' : 'bg-cyan-400'
              }`}
              style={{ width: `${Math.min(currentCpu, 100)}%` }}
            ></div>
          </div>
        </div>

        {/* Memory */}
        <div className="p-4 rounded-xl bg-navy-900/80 border border-navy-700/60 shadow-md">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
            <span className="flex items-center space-x-1.5 font-mono">
              <Layers className="h-4 w-4 text-purple-400" />
              <span>MEMORY UTILIZATION</span>
            </span>
            <span className="font-mono text-slate-300">
              {latestMetric ? `${(latestMetric.memory_used_mb / 1024).toFixed(1)} GB used` : 'N/A'}
            </span>
          </div>
          <div className="flex items-baseline space-x-2">
            <span className="text-3xl font-bold font-mono text-white">{currentMem.toFixed(1)}%</span>
            <span className={`text-xs font-semibold ${currentMem > 85 ? 'text-rose-400' : 'text-slate-400'}`}>
              {currentMem > 85 ? 'High Pressure' : 'Available'}
            </span>
          </div>
          <div className="mt-3 w-full bg-navy-800 rounded-full h-1.5 overflow-hidden">
            <div
              className={`h-full transition-all duration-500 ${
                currentMem > 90 ? 'bg-rose-500' : currentMem > 80 ? 'bg-amber-400' : 'bg-purple-400'
              }`}
              style={{ width: `${Math.min(currentMem, 100)}%` }}
            ></div>
          </div>
        </div>

        {/* Disk */}
        <div className="p-4 rounded-xl bg-navy-900/80 border border-navy-700/60 shadow-md">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
            <span className="flex items-center space-x-1.5 font-mono">
              <HardDrive className="h-4 w-4 text-emerald-400" />
              <span>PRIMARY FILESYSTEM</span>
            </span>
            <span className="font-mono text-slate-300">
              {latestMetric ? `${latestMetric.disk_used_gb.toFixed(0)} / ${(latestMetric.disk_used_gb + latestMetric.disk_available_gb).toFixed(0)} GB` : 'N/A'}
            </span>
          </div>
          <div className="flex items-baseline space-x-2">
            <span className="text-3xl font-bold font-mono text-white">{currentDisk.toFixed(1)}%</span>
            <span className={`text-xs font-semibold ${currentDisk > 85 ? 'text-rose-400' : 'text-slate-400'}`}>
              {currentDisk > 85 ? 'Critical Bloat' : 'Healthy'}
            </span>
          </div>
          <div className="mt-3 w-full bg-navy-800 rounded-full h-1.5 overflow-hidden">
            <div
              className={`h-full transition-all duration-500 ${
                currentDisk > 90 ? 'bg-rose-500' : currentDisk > 80 ? 'bg-amber-400' : 'bg-emerald-400'
              }`}
              style={{ width: `${Math.min(currentDisk, 100)}%` }}
            ></div>
          </div>
        </div>
      </div>

      {/* Telemetry Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* CPU & Memory Trends */}
        <div className="p-5 rounded-xl bg-navy-900/80 border border-navy-700/60 shadow-lg space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white flex items-center space-x-2">
              <Cpu className="h-4 w-4 text-cyan-400" />
              <span>CPU & Memory Utilization History</span>
            </h3>
            <span className="text-[11px] font-mono text-slate-400">Live 6s Window</span>
          </div>

          <div className="h-64 w-full pt-2">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="cpuGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#06B6D4" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#06B6D4" stopOpacity={0.0} />
                  </linearGradient>
                  <linearGradient id="memGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#8B5CF6" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#8B5CF6" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" vertical={false} />
                <XAxis dataKey="time" stroke="#64748B" fontSize={10} tickLine={false} />
                <YAxis stroke="#64748B" fontSize={10} domain={[0, 100]} tickLine={false} unit="%" />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0B0F19', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }}
                />
                <Area type="monotone" dataKey="cpu" stroke="#06B6D4" strokeWidth={2} fillOpacity={1} fill="url(#cpuGradient)" name="CPU %" />
                <Area type="monotone" dataKey="memory" stroke="#8B5CF6" strokeWidth={2} fillOpacity={1} fill="url(#memGradient)" name="Memory %" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Network & Disk Activity */}
        <div className="p-5 rounded-xl bg-navy-900/80 border border-navy-700/60 shadow-lg space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white flex items-center space-x-2">
              <Network className="h-4 w-4 text-emerald-400" />
              <span>Network Traffic Rate</span>
            </h3>
            <span className="text-[11px] font-mono text-slate-400">KB / sec</span>
          </div>

          <div className="h-64 w-full pt-2">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" vertical={false} />
                <XAxis dataKey="time" stroke="#64748B" fontSize={10} tickLine={false} />
                <YAxis stroke="#64748B" fontSize={10} tickLine={false} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0B0F19', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }}
                />
                <Line type="monotone" dataKey="net_rx_kb" stroke="#10B981" strokeWidth={2} dot={false} name="Recv (KB)" />
                <Line type="monotone" dataKey="net_tx_kb" stroke="#3B82F6" strokeWidth={2} dot={false} name="Sent (KB)" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Bottom: Real Process Table Inspector */}
      <div className="p-5 rounded-xl bg-navy-900/80 border border-navy-700/60 shadow-lg space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h3 className="text-base font-semibold text-white flex items-center space-x-2">
              <Terminal className="h-4 w-4 text-cyan-400" />
              <span>Active Process Inspector</span>
            </h3>
            <p className="text-xs text-slate-400">
              Live psutil thread snapshot for deep-dive root cause analysis
            </p>
          </div>

          {/* Toggle Top CPU vs Top Memory */}
          <div className="flex items-center bg-navy-800 p-1 rounded-lg border border-navy-700">
            <button
              onClick={() => setActiveProcessTab('cpu')}
              className={`px-3 py-1 text-xs font-medium rounded-md transition ${
                activeProcessTab === 'cpu' ? 'bg-cyan-600 text-white shadow' : 'text-slate-400 hover:text-white'
              }`}
            >
              Top CPU Consuming
            </button>
            <button
              onClick={() => setActiveProcessTab('memory')}
              className={`px-3 py-1 text-xs font-medium rounded-md transition ${
                activeProcessTab === 'memory' ? 'bg-purple-600 text-white shadow' : 'text-slate-400 hover:text-white'
              }`}
            >
              Top Memory Consuming
            </button>
          </div>
        </div>

        {/* Process Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead>
              <tr className="border-b border-navy-700 text-slate-400 text-[11px] uppercase tracking-wider">
                <th className="py-2.5 px-3">PID</th>
                <th className="py-2.5 px-3">Process Name</th>
                <th className="py-2.5 px-3">User</th>
                <th className="py-2.5 px-3">CPU %</th>
                <th className="py-2.5 px-3">Memory %</th>
                <th className="py-2.5 px-3">RSS (MB)</th>
                <th className="py-2.5 px-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-navy-800/80">
              {processes.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-6 text-center text-slate-400">
                    No active process data available for node
                  </td>
                </tr>
              ) : (
                processes.map((p) => (
                  <tr key={p.pid} className="hover:bg-navy-800/40 transition">
                    <td className="py-2.5 px-3 text-cyan-400 font-semibold">{p.pid}</td>
                    <td className="py-2.5 px-3 text-slate-200 font-medium">{p.name}</td>
                    <td className="py-2.5 px-3 text-slate-400">{p.username}</td>
                    <td className="py-2.5 px-3 font-semibold text-slate-200">
                      <span className={p.cpu_percent > 40 ? 'text-rose-400' : 'text-slate-300'}>
                        {p.cpu_percent.toFixed(1)}%
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-slate-300">{p.memory_percent.toFixed(1)}%</td>
                    <td className="py-2.5 px-3 text-slate-300">{p.memory_rss_mb} MB</td>
                    <td className="py-2.5 px-3">
                      <span className="px-2 py-0.5 rounded bg-navy-800 text-slate-300 border border-navy-700 text-[10px]">
                        {p.status || 'running'}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

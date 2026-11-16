import React, { useState } from 'react';
import {
  Server as ServerIcon,
  Plus,
  Terminal,
  Cpu,
  Layers,
  HardDrive,
  Copy,
  Check,
  Globe,
  Cloud,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  RefreshCw
} from 'lucide-react';
import { Server } from '../types';
import { api } from '../services/api';

interface ServersPageProps {
  servers: Server[];
  onRefresh: () => void;
  onSelectServer: (serverId: string) => void;
}

export const ServersPage: React.FC<ServersPageProps> = ({ servers, onRefresh, onSelectServer }) => {
  const [showAddModal, setShowAddModal] = useState<boolean>(false);
  const [copiedSnippet, setCopiedSnippet] = useState<boolean>(false);
  const [formData, setFormData] = useState({
    id: '',
    hostname: '',
    ip_address: '',
    os_name: 'Linux',
    os_version: 'Ubuntu 22.04 LTS',
    cpu_cores: 4,
    total_memory_mb: 8192,
    total_disk_gb: 100
  });

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.hostname) return;

    try {
      await api.registerServer({
        ...formData,
        id: formData.id || `srv-${formData.hostname.toLowerCase().replace('.', '-')}`
      });
      setShowAddModal(false);
      onRefresh();
    } catch (err: any) {
      alert(`Registration failed: ${err.message}`);
    }
  };

  const agentInstallSnippet = `# CloudPulse Monitoring Agent Installation
git clone https://github.com/thejus07/CLOUDPULSE.git /opt/cloudpulse
cd /opt/cloudpulse
pip install -r backend/requirements.txt
python agent/main.py --daemon --server-id srv-production-01 --backend-url http://10.0.1.100:5000/api`;

  const copyToClipboard = () => {
    navigator.clipboard.writeText(agentInstallSnippet);
    setCopiedSnippet(true);
    setTimeout(() => setCopiedSnippet(false), 2000);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center space-x-2">
            <ServerIcon className="h-6 w-6 text-cyan-400" />
            <span>Monitored Server Fleet</span>
          </h1>
          <p className="text-sm text-slate-400">
            Registered Linux and hybrid cloud instances reporting telemetry and health status
          </p>
        </div>

        <button
          onClick={() => setShowAddModal(true)}
          className="flex items-center space-x-2 px-4 py-2 rounded-lg bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-semibold text-xs shadow-lg shadow-cyan-500/20 transition self-start sm:self-auto"
        >
          <Plus className="h-4 w-4" />
          <span>Add Monitored Server</span>
        </button>
      </div>

      {/* Server Fleet Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {servers.map((server) => {
          const isHealthy = server.status === 'HEALTHY';
          const isCritical = server.status === 'CRITICAL';
          const isWarning = server.status === 'WARNING';
          const isOffline = server.status === 'OFFLINE';

          return (
            <div
              key={server.id}
              className="p-5 rounded-xl bg-navy-900/80 border border-navy-700/60 shadow-lg hover:border-cyan-500/40 transition space-y-4 flex flex-col justify-between"
            >
              <div>
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="font-bold text-white text-base hover:text-cyan-300 transition">
                      {server.hostname}
                    </h3>
                    <p className="text-xs font-mono text-cyan-400 mt-0.5">{server.id}</p>
                  </div>

                  <span
                    className={`text-[10px] px-2 py-0.5 rounded-full font-mono font-bold border ${
                      isCritical
                        ? 'bg-rose-950 text-rose-300 border-rose-800'
                        : isWarning
                        ? 'bg-amber-950 text-amber-300 border-amber-800'
                        : isOffline
                        ? 'bg-slate-900 text-slate-400 border-slate-700'
                        : 'bg-emerald-950 text-emerald-300 border-emerald-800'
                    }`}
                  >
                    {server.status}
                  </span>
                </div>

                {/* Metadata List */}
                <div className="mt-4 space-y-2 text-xs font-mono text-slate-300 border-t border-navy-800 pt-3">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400">IP Address:</span>
                    <span>{server.ip_address || '127.0.0.1'}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400">Platform:</span>
                    <span>{server.os_name} {server.architecture}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400">Release:</span>
                    <span className="truncate max-w-[160px]">{server.os_version}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400">Last Telemetry:</span>
                    <span>
                      {server.last_heartbeat ? new Date(server.last_heartbeat).toLocaleTimeString() : 'Never'}
                    </span>
                  </div>
                </div>

                {/* Specs Box */}
                <div className="mt-4 grid grid-cols-3 gap-2 bg-navy-950/70 p-2.5 rounded-lg text-center text-xs font-mono border border-navy-800">
                  <div>
                    <div className="text-[10px] text-slate-400">CPU</div>
                    <div className="font-bold text-slate-200">{server.cpu_cores} Cores</div>
                  </div>
                  <div>
                    <div className="text-[10px] text-slate-400">RAM</div>
                    <div className="font-bold text-slate-200">{Math.round(server.total_memory_mb / 1024)} GB</div>
                  </div>
                  <div>
                    <div className="text-[10px] text-slate-400">DISK</div>
                    <div className="font-bold text-slate-200">{Math.round(server.total_disk_gb)} GB</div>
                  </div>
                </div>
              </div>

              {/* Action Button */}
              <button
                onClick={() => onSelectServer(server.id)}
                className="w-full py-2 px-3 rounded-lg bg-navy-800 hover:bg-navy-700 text-cyan-300 border border-cyan-500/20 text-xs font-semibold transition"
              >
                Inspect Telemetry &rarr;
              </button>
            </div>
          );
        })}
      </div>

      {/* Agent Bootstrap Guide Card */}
      <div className="p-5 rounded-xl bg-navy-900/80 border border-navy-700/60 shadow-lg space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Terminal className="h-5 w-5 text-cyan-400" />
            <h3 className="text-sm font-bold text-white">How to Install CloudPulse Agent on New Linux Hosts</h3>
          </div>
          <button
            onClick={copyToClipboard}
            className="flex items-center space-x-1.5 px-3 py-1 rounded bg-navy-800 hover:bg-navy-700 text-xs text-slate-300 font-mono transition border border-navy-700"
          >
            {copiedSnippet ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
            <span>{copiedSnippet ? 'Copied' : 'Copy'}</span>
          </button>
        </div>
        <p className="text-xs text-slate-400">
          Run this single command on any target Ubuntu/Debian/RHEL server to start autonomous metric ingestion:
        </p>
        <pre className="p-3.5 rounded-lg bg-navy-950 border border-navy-800 text-xs text-emerald-400 font-mono overflow-x-auto">
          {agentInstallSnippet}
        </pre>
      </div>

      {/* Add Server Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-navy-950/80 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-navy-900 border border-navy-700 rounded-xl p-6 max-w-md w-full shadow-2xl space-y-4">
            <h2 className="text-lg font-bold text-white">Register Monitored Server</h2>
            <form onSubmit={handleRegister} className="space-y-3 text-xs">
              <div>
                <label className="text-slate-400 block mb-1">Server Hostname</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. prod-web-01.infra"
                  value={formData.hostname}
                  onChange={(e) => setFormData({ ...formData, hostname: e.target.value })}
                  className="w-full bg-navy-800 border border-navy-700 rounded-lg p-2 text-white font-mono focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div>
                <label className="text-slate-400 block mb-1">Custom Server ID (Optional)</label>
                <input
                  type="text"
                  placeholder="e.g. srv-prod-web-01"
                  value={formData.id}
                  onChange={(e) => setFormData({ ...formData, id: e.target.value })}
                  className="w-full bg-navy-800 border border-navy-700 rounded-lg p-2 text-white font-mono focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div>
                <label className="text-slate-400 block mb-1">IP Address</label>
                <input
                  type="text"
                  placeholder="e.g. 10.0.1.55"
                  value={formData.ip_address}
                  onChange={(e) => setFormData({ ...formData, ip_address: e.target.value })}
                  className="w-full bg-navy-800 border border-navy-700 rounded-lg p-2 text-white font-mono focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-slate-400 block mb-1">CPU Cores</label>
                  <input
                    type="number"
                    value={formData.cpu_cores}
                    onChange={(e) => setFormData({ ...formData, cpu_cores: parseInt(e.target.value) || 1 })}
                    className="w-full bg-navy-800 border border-navy-700 rounded-lg p-2 text-white font-mono"
                  />
                </div>
                <div>
                  <label className="text-slate-400 block mb-1">Total RAM (MB)</label>
                  <input
                    type="number"
                    value={formData.total_memory_mb}
                    onChange={(e) => setFormData({ ...formData, total_memory_mb: parseFloat(e.target.value) || 1024 })}
                    className="w-full bg-navy-800 border border-navy-700 rounded-lg p-2 text-white font-mono"
                  />
                </div>
              </div>

              <div className="flex items-center justify-end space-x-2 pt-3 border-t border-navy-800">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-4 py-2 rounded-lg bg-navy-800 hover:bg-navy-700 text-slate-300 font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-semibold"
                >
                  Save Server
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

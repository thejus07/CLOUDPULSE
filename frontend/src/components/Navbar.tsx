import React, { useEffect, useState } from 'react';
import { Activity, ShieldCheck, Cloud, Server, Bell, RefreshCw, Cpu } from 'lucide-react';
import { api } from '../services/api';
import { AWSStatus } from '../types';

interface NavbarProps {
  onRefresh: () => void;
  isRefreshing: boolean;
  activeSimulationsCount: number;
}

export const Navbar: React.FC<NavbarProps> = ({ onRefresh, isRefreshing, activeSimulationsCount }) => {
  const [awsStatus, setAwsStatus] = useState<AWSStatus | null>(null);
  const [time, setTime] = useState<string>(new Date().toUTCString().slice(17, 25) + ' UTC');

  useEffect(() => {
    api.getAWSStatus().then(setAwsStatus).catch(() => {});
    const timer = setInterval(() => {
      setTime(new Date().toUTCString().slice(17, 25) + ' UTC');
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <header className="h-16 border-b border-navy-700/60 bg-navy-900/90 backdrop-blur-md px-6 flex items-center justify-between sticky top-0 z-40">
      {/* Brand */}
      <div className="flex items-center space-x-3">
        <div className="h-9 w-9 rounded-lg bg-gradient-to-tr from-cyan-600 to-blue-500 flex items-center justify-center shadow-lg shadow-cyan-500/20">
          <Activity className="h-5 w-5 text-white" />
        </div>
        <div>
          <div className="flex items-center space-x-2">
            <span className="font-bold text-lg tracking-tight bg-gradient-to-r from-white via-slate-200 to-cyan-300 bg-clip-text text-transparent">
              CloudPulse
            </span>
            <span className="text-[10px] font-semibold uppercase tracking-wider px-1.5 py-0.5 rounded bg-cyan-950/80 border border-cyan-800 text-cyan-400">
              v1.0
            </span>
          </div>
          <p className="text-[11px] text-slate-400 font-medium">Intelligent Observability & Incident Remediation</p>
        </div>
      </div>

      {/* Center Status Indicators */}
      <div className="hidden md:flex items-center space-x-4">
        {/* Active Simulation Pill */}
        {activeSimulationsCount > 0 && (
          <div className="flex items-center space-x-2 px-3 py-1 rounded-full bg-rose-950/70 border border-rose-800/80 text-rose-300 animate-pulse text-xs font-mono">
            <span className="h-2 w-2 rounded-full bg-rose-500"></span>
            <span>Simulation Active ({activeSimulationsCount})</span>
          </div>
        )}

        {/* AWS / Local Indicator */}
        <div className="flex items-center space-x-2 px-3 py-1 rounded-full bg-navy-800 border border-navy-700 text-slate-300 text-xs">
          <Cloud className={`h-3.5 w-3.5 ${awsStatus?.is_running_on_ec2 ? 'text-amber-400' : 'text-cyan-400'}`} />
          <span className="font-mono">
            {awsStatus?.is_running_on_ec2 ? `AWS EC2 (${awsStatus.region})` : 'Local Infrastructure Mode'}
          </span>
        </div>

        {/* Live Clock */}
        <div className="text-xs font-mono text-slate-400 bg-navy-800/60 px-2.5 py-1 rounded border border-navy-700/50">
          {time}
        </div>
      </div>

      {/* Right Controls */}
      <div className="flex items-center space-x-3">
        <button
          onClick={onRefresh}
          disabled={isRefreshing}
          className="flex items-center space-x-1.5 text-xs font-medium px-3 py-1.5 rounded-lg bg-navy-800 hover:bg-navy-700 text-slate-300 hover:text-white border border-navy-700 transition"
          title="Refresh All Telemetry"
        >
          <RefreshCw className={`h-3.5 w-3.5 text-cyan-400 ${isRefreshing ? 'animate-spin' : ''}`} />
          <span>Sync</span>
        </button>

        <div className="h-6 w-px bg-navy-700/60 mx-1"></div>

        <div className="flex items-center space-x-2">
          <div className="h-7 w-7 rounded-full bg-navy-800 border border-cyan-500/40 flex items-center justify-center text-xs font-semibold text-cyan-300">
            SE
          </div>
          <div className="hidden sm:block text-left">
            <div className="text-xs font-semibold text-slate-200">Support Engineer</div>
            <div className="text-[10px] text-emerald-400 font-mono">Operator</div>
          </div>
        </div>
      </div>
    </header>
  );
};

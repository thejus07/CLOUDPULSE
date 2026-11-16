"""
CPU Diagnostics Module
Identifies high CPU saturation, inspects top CPU-consuming processes, captures PIDs, and analyzes core load.
"""

import time
from datetime import datetime, timezone
import psutil


class CPUDiagnostics:
    """Investigates CPU anomalies, runaway processes, and high load averages."""

    def __init__(self, warning_threshold: float = 75.0, critical_threshold: float = 90.0):
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold

    def run(self) -> dict:
        start_time = time.time()
        
        # Measure CPU percent over sample window
        cpu_percent = psutil.cpu_percent(interval=0.2)
        per_core = psutil.cpu_percent(interval=None, percpu=True)
        
        # Load averages
        try:
            import os
            load_1, load_5, load_15 = os.getloadavg()
        except Exception:
            core_count = psutil.cpu_count() or 1
            load_1 = round(cpu_percent / 100.0 * core_count, 2)
            load_5 = load_1
            load_15 = load_1

        # Scan for high CPU processes
        top_procs = []
        for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent', 'cmdline', 'create_time']):
            try:
                pinfo = proc.info
                # Format cmdline safely
                cmdline = " ".join(pinfo.get('cmdline') or [])
                if len(cmdline) > 120:
                    cmdline = cmdline[:117] + "..."

                top_procs.append({
                    "pid": pinfo['pid'],
                    "name": pinfo['name'] or "unknown",
                    "username": pinfo.get('username') or "system",
                    "cpu_percent": round(pinfo.get('cpu_percent') or 0.0, 1),
                    "memory_percent": round(pinfo.get('memory_percent') or 0.0, 1),
                    "cmdline": cmdline or pinfo.get('name')
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        # Sort by CPU usage descending
        top_procs = sorted(top_procs, key=lambda x: x["cpu_percent"], reverse=True)[:10]

        # Determine diagnostic status and root causes
        status = "HEALTHY"
        root_causes = []
        recommendations = []

        if cpu_percent >= self.critical_threshold:
            status = "CRITICAL"
            primary_proc = top_procs[0] if top_procs else None
            if primary_proc and primary_proc["cpu_percent"] > 50:
                root_causes.append(f"Process '{primary_proc['name']}' (PID: {primary_proc['pid']}) is consuming {primary_proc['cpu_percent']}% CPU, causing CPU saturation.")
                recommendations.append(f"Investigate process PID {primary_proc['pid']} ({primary_proc['name']}). Inspect execution logs or consider graceful restart.")
            else:
                root_causes.append(f"Distributed CPU saturation across multiple tasks ({cpu_percent}% total utilization).")
                recommendations.append("Audit background cron jobs, scale compute instance type, or distribute worker queue load.")
        elif cpu_percent >= self.warning_threshold:
            status = "WARNING"
            root_causes.append(f"Elevated CPU utilization at {cpu_percent}%, approaching threshold ({self.warning_threshold}%).")
            recommendations.append("Monitor thread activity and profile application CPU hotspots.")
        else:
            root_causes.append(f"CPU utilization is nominal at {cpu_percent}%.")
            recommendations.append("No immediate action required.")

        execution_duration = (time.time() - start_time) * 1000

        return {
            "diagnostic_type": "CPU",
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "execution_duration_ms": round(execution_duration, 2),
            "findings": {
                "overall_cpu_percent": cpu_percent,
                "per_core_percent": per_core,
                "load_average": {"1m": load_1, "5m": load_5, "15m": load_15},
                "cpu_count_logical": psutil.cpu_count(logical=True) or 1,
                "top_cpu_processes": top_procs
            },
            "probable_root_cause": " | ".join(root_causes),
            "recommendations": recommendations,
            "raw_output": f"CPU Utilization: {cpu_percent}% | Load: 1m={load_1}, 5m={load_5}, 15m={load_15} | Top Process: {top_procs[0]['name'] if top_procs else 'None'}"
        }

"""
Process Collector
Gathers process lists, detects high CPU/memory consuming tasks, and captures process metrics safely.
"""

from typing import List, Dict, Any
import psutil


class ProcessCollector:
    """Safely collects running process details and identifies resource hogs."""

    def __init__(self, top_n: int = 10):
        self.top_n = top_n

    def get_processes(self) -> List[Dict[str, Any]]:
        """Collect all running processes with basic diagnostic fields."""
        processes = []
        # Query psutil process iterator safely
        for proc in psutil.process_iter(['pid', 'name', 'username', 'status', 'cpu_percent', 'memory_percent', 'memory_info']):
            try:
                pinfo = proc.info
                mem_info = pinfo.get('memory_info')
                rss_mb = round(mem_info.rss / (1024 * 1024), 2) if mem_info else 0.0

                processes.append({
                    "pid": pinfo['pid'],
                    "name": pinfo['name'] or "unknown",
                    "username": pinfo.get('username') or "system",
                    "status": pinfo.get('status') or "unknown",
                    "cpu_percent": round(pinfo.get('cpu_percent') or 0.0, 1),
                    "memory_percent": round(pinfo.get('memory_percent') or 0.0, 1),
                    "memory_rss_mb": rss_mb
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
            except Exception:
                continue

        return processes

    def get_top_cpu_processes(self, limit: int = None) -> List[Dict[str, Any]]:
        """Retrieve top CPU consuming processes."""
        limit = limit or self.top_n
        procs = self.get_processes()
        # Sort descending by cpu_percent
        return sorted(procs, key=lambda x: x["cpu_percent"], reverse=True)[:limit]

    def get_top_memory_processes(self, limit: int = None) -> List[Dict[str, Any]]:
        """Retrieve top Memory consuming processes."""
        limit = limit or self.top_n
        procs = self.get_processes()
        # Sort descending by memory_rss_mb
        return sorted(procs, key=lambda x: x["memory_rss_mb"], reverse=True)[:limit]

    def get_process_summary(self) -> Dict[str, Any]:
        """Summary of process counts by status."""
        total = 0
        running = 0
        sleeping = 0
        other = 0

        for proc in psutil.process_iter(['status']):
            try:
                total += 1
                status = proc.info.get('status')
                if status == psutil.STATUS_RUNNING:
                    running += 1
                elif status == psutil.STATUS_SLEEPING:
                    sleeping += 1
                else:
                    other += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        return {
            "total_processes": total,
            "running": running,
            "sleeping": sleeping,
            "other": other,
            "top_cpu": self.get_top_cpu_processes(5),
            "top_memory": self.get_top_memory_processes(5)
        }

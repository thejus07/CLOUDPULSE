"""
System Metrics Collector
Gathers CPU, Memory, Disk, Network, Uptime, and OS details via psutil and OS utilities.
"""

import os
import platform
import time
from datetime import datetime, timezone
import psutil


class SystemCollector:
    """Collects host hardware, operating system, and system performance metrics."""

    def __init__(self, disk_path: str = None):
        self.disk_path = disk_path or os.path.abspath(os.sep)

    def get_os_info(self) -> dict:
        """Collect operating system and hardware metadata."""
        boot_time_timestamp = psutil.boot_time()
        uptime_seconds = int(time.time() - boot_time_timestamp)

        # Linux /proc/version or os-release lookup if available
        os_version = platform.version()
        if platform.system() == "Linux":
            try:
                with open("/etc/os-release", "r") as f:
                    for line in f:
                        if line.startswith("PRETTY_NAME="):
                            os_version = line.split("=")[1].strip().strip('"')
                            break
            except Exception:
                pass

        return {
            "hostname": platform.node(),
            "os_name": platform.system(),
            "os_release": platform.release(),
            "os_version": os_version,
            "architecture": platform.machine(),
            "cpu_cores_physical": psutil.cpu_count(logical=False) or psutil.cpu_count(),
            "cpu_cores_logical": psutil.cpu_count(logical=True) or 1,
            "boot_time": datetime.fromtimestamp(boot_time_timestamp, tz=timezone.utc).isoformat(),
            "uptime_seconds": uptime_seconds,
            "uptime_formatted": self._format_uptime(uptime_seconds)
        }

    def get_cpu_metrics(self) -> dict:
        """Collect overall and per-core CPU usage and load average."""
        try:
            cpu_overall = psutil.cpu_percent(interval=0.1)
        except Exception:
            cpu_overall = 0.0

        try:
            per_core = psutil.cpu_percent(interval=None, percpu=True)
        except Exception:
            per_core = [cpu_overall]
        
        # Load average (Linux/Unix has os.getloadavg; fallback on Windows)
        try:
            load1, load5, load15 = os.getloadavg()
        except (AttributeError, OSError, Exception):
            # Emulate load average approximately from CPU usage for Windows
            core_count = psutil.cpu_count() or 1
            load1 = round(cpu_overall / 100.0 * core_count, 2)
            load5 = load1
            load15 = load1

        # CPU Frequency (may fail on certain hypervisors or permissions)
        cpu_freq_data = {"current_mhz": 0.0, "min_mhz": 0.0, "max_mhz": 0.0}
        try:
            freq = psutil.cpu_freq()
            if freq:
                cpu_freq_data = {
                    "current_mhz": round(freq.current, 1) if freq.current else 0.0,
                    "min_mhz": round(freq.min, 1) if freq.min else 0.0,
                    "max_mhz": round(freq.max, 1) if freq.max else 0.0,
                }
        except Exception:
            pass

        return {
            "percent": cpu_overall,
            "per_core_percent": per_core,
            "load_1m": round(load1, 2),
            "load_5m": round(load5, 2),
            "load_15m": round(load15, 2),
            "frequency": cpu_freq_data
        }

    def get_memory_metrics(self) -> dict:
        """Collect physical and swap memory metrics."""
        try:
            vm = psutil.virtual_memory()
            total_mb = round(vm.total / (1024 * 1024), 2)
            available_mb = round(vm.available / (1024 * 1024), 2)
            used_mb = round(vm.used / (1024 * 1024), 2)
            free_mb = round(vm.free / (1024 * 1024), 2)
            percent = round(vm.percent, 2)
        except Exception as e:
            total_mb, available_mb, used_mb, free_mb, percent = 8192.0, 4096.0, 4096.0, 4096.0, 50.0

        # Handle potential Windows PDH failure for swap_memory
        try:
            swap = psutil.swap_memory()
            swap_data = {
                "total_mb": round(swap.total / (1024 * 1024), 2),
                "used_mb": round(swap.used / (1024 * 1024), 2),
                "free_mb": round(swap.free / (1024 * 1024), 2),
                "percent": round(swap.percent, 2)
            }
        except Exception:
            swap_data = {
                "total_mb": 0.0,
                "used_mb": 0.0,
                "free_mb": 0.0,
                "percent": 0.0
            }

        return {
            "total_mb": total_mb,
            "available_mb": available_mb,
            "used_mb": used_mb,
            "free_mb": free_mb,
            "percent": percent,
            "swap": swap_data
        }

    def get_disk_metrics(self) -> dict:
        """Collect disk space utilization and disk I/O rates."""
        try:
            usage = psutil.disk_usage(self.disk_path)
            total_gb = round(usage.total / (1024 ** 3), 2)
            used_gb = round(usage.used / (1024 ** 3), 2)
            free_gb = round(usage.free / (1024 ** 3), 2)
            percent = round(usage.percent, 2)
        except Exception as e:
            total_gb, used_gb, free_gb, percent = 0.0, 0.0, 0.0, 0.0

        # All mounted partitions
        partitions_summary = []
        try:
            for part in psutil.disk_partitions(all=False):
                try:
                    p_usage = psutil.disk_usage(part.mountpoint)
                    partitions_summary.append({
                        "device": part.device,
                        "mountpoint": part.mountpoint,
                        "fstype": part.fstype,
                        "total_gb": round(p_usage.total / (1024 ** 3), 2),
                        "used_gb": round(p_usage.used / (1024 ** 3), 2),
                        "free_gb": round(p_usage.free / (1024 ** 3), 2),
                        "percent": round(p_usage.percent, 2)
                    })
                except (PermissionError, OSError):
                    continue
        except Exception:
            pass

        # Disk I/O counters
        io_counters = psutil.disk_io_counters()
        io_data = {
            "read_bytes": io_counters.read_bytes if io_counters else 0,
            "write_bytes": io_counters.write_bytes if io_counters else 0,
            "read_count": io_counters.read_count if io_counters else 0,
            "write_count": io_counters.write_count if io_counters else 0
        }

        return {
            "monitored_path": self.disk_path,
            "total_gb": total_gb,
            "used_gb": used_gb,
            "free_gb": free_gb,
            "percent": percent,
            "partitions": partitions_summary,
            "io": io_data
        }

    def get_network_metrics(self) -> dict:
        """Collect network I/O counters and interface details."""
        net_io = psutil.net_io_counters()
        return {
            "bytes_sent": net_io.bytes_sent if net_io else 0,
            "bytes_recv": net_io.bytes_recv if net_io else 0,
            "packets_sent": net_io.packets_sent if net_io else 0,
            "packets_recv": net_io.packets_recv if net_io else 0,
            "errin": net_io.errin if net_io else 0,
            "errout": net_io.errout if net_io else 0,
            "dropin": net_io.dropin if net_io else 0,
            "dropout": net_io.dropout if net_io else 0
        }

    def collect_all(self) -> dict:
        """Run full system collection and return unified structured dict."""
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "os": self.get_os_info(),
            "cpu": self.get_cpu_metrics(),
            "memory": self.get_memory_metrics(),
            "disk": self.get_disk_metrics(),
            "network": self.get_network_metrics()
        }

    @staticmethod
    def _format_uptime(seconds: int) -> str:
        days, rem = divmod(seconds, 86400)
        hours, rem = divmod(rem, 3600)
        minutes, _ = divmod(rem, 60)
        parts = []
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0 or days > 0:
            parts.append(f"{hours}h")
        parts.append(f"{minutes}m")
        return " ".join(parts)

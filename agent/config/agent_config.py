"""
Monitoring Agent Configuration
"""

import os
import socket
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")


class AgentConfig:
    def __init__(self):
        self.hostname = os.getenv("CLOUDPULSE_HOSTNAME", socket.gethostname())
        self.server_id = os.getenv("CLOUDPULSE_SERVER_ID", f"srv-{self.hostname.lower().replace('.', '-')}")
        self.backend_url = os.getenv("CLOUDPULSE_BACKEND_URL", "http://localhost:5000/api")
        self.api_key = os.getenv("API_KEY", "cloudpulse-internal-api-key-2026")
        self.interval = int(os.getenv("METRIC_COLLECTION_INTERVAL_SECONDS", 10))
        
        # Monitored disk path (default: root / on Linux, C:\ or current drive on Windows)
        self.monitored_disk_path = os.getenv("CLOUDPULSE_DISK_PATH", os.path.abspath(os.sep))

        # Critical & Warning thresholds for local agent alerting
        self.cpu_warning = float(os.getenv("THRESHOLD_CPU_WARNING", 75.0))
        self.cpu_critical = float(os.getenv("THRESHOLD_CPU_CRITICAL", 90.0))
        self.memory_warning = float(os.getenv("THRESHOLD_MEMORY_WARNING", 80.0))
        self.memory_critical = float(os.getenv("THRESHOLD_MEMORY_CRITICAL", 92.0))
        self.disk_warning = float(os.getenv("THRESHOLD_DISK_WARNING", 80.0))
        self.disk_critical = float(os.getenv("THRESHOLD_DISK_CRITICAL", 90.0))

        # Target systemd services / daemons to track
        self.monitored_services = [
            s.strip() for s in os.getenv(
                "MONITORED_SERVICES",
                "nginx,postgresql,redis,cloudpulse-worker,test-service"
            ).split(",") if s.strip()
        ]

    def to_dict(self):
        return {
            "server_id": self.server_id,
            "hostname": self.hostname,
            "backend_url": self.backend_url,
            "interval": self.interval,
            "monitored_disk_path": self.monitored_disk_path,
            "thresholds": {
                "cpu": {"warning": self.cpu_warning, "critical": self.cpu_critical},
                "memory": {"warning": self.memory_warning, "critical": self.memory_critical},
                "disk": {"warning": self.disk_warning, "critical": self.disk_critical}
            },
            "monitored_services": self.monitored_services
        }


agent_config = AgentConfig()

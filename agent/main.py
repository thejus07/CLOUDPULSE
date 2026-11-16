"""
CloudPulse Monitoring Agent Entrypoint
Can be executed as a standalone CLI probe (--once) or as a background monitoring daemon (--daemon).
"""

import sys
import os
import time
import argparse
import json
import logging
from datetime import datetime, timezone
import requests

# Ensure parent directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agent.config.agent_config import agent_config
from agent.collectors.system_collector import SystemCollector
from agent.collectors.process_collector import ProcessCollector
from agent.collectors.service_collector import ServiceCollector

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [Agent] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("CloudPulseAgent")


class CloudPulseAgent:
    """Orchestrates collectors, aggregates data, and transmits to CloudPulse backend."""

    def __init__(self, server_id=None, backend_url=None, interval=None):
        self.server_id = server_id or agent_config.server_id
        self.backend_url = (backend_url or agent_config.backend_url).rstrip("/")
        self.interval = interval or agent_config.interval
        
        self.system_collector = SystemCollector(disk_path=agent_config.monitored_disk_path)
        self.process_collector = ProcessCollector(top_n=10)
        self.service_collector = ServiceCollector(monitored_services=agent_config.monitored_services)

    def collect(self) -> dict:
        """Run all collectors and produce complete structured telemetry."""
        system_data = self.system_collector.collect_all()
        process_data = self.process_collector.get_process_summary()
        services_data = self.service_collector.check_all_services()
        failed_services = self.service_collector.get_failed_services()

        payload = {
            "server_id": self.server_id,
            "hostname": system_data["os"]["hostname"],
            "timestamp": system_data["timestamp"],
            "os": system_data["os"],
            "cpu": system_data["cpu"],
            "memory": system_data["memory"],
            "disk": system_data["disk"],
            "network": system_data["network"],
            "processes": process_data,
            "services": services_data,
            "failed_services": failed_services
        }
        return payload

    def register_server(self, system_data: dict) -> bool:
        """Ensure this host is registered in the CloudPulse server fleet."""
        url = f"{self.backend_url}/servers"
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": agent_config.api_key
        }
        os_info = system_data.get("os", {})
        mem_info = system_data.get("memory", {})
        disk_info = system_data.get("disk", {})

        body = {
            "id": self.server_id,
            "hostname": os_info.get("hostname", self.server_id),
            "os_name": os_info.get("os_name", "Linux"),
            "os_version": os_info.get("os_version", "Generic"),
            "architecture": os_info.get("architecture", "x86_64"),
            "cpu_cores": os_info.get("cpu_cores_logical", 1),
            "total_memory_mb": mem_info.get("total_mb", 0.0),
            "total_disk_gb": disk_info.get("total_gb", 0.0),
            "is_local": True
        }

        try:
            resp = requests.post(url, json=body, headers=headers, timeout=5)
            if resp.status_code in (200, 201):
                logger.info("Successfully registered/verified server %s with backend", self.server_id)
                return True
            else:
                logger.warning("Server registration returned status %d: %s", resp.status_code, resp.text)
                return False
        except Exception as e:
            logger.warning("Could not reach backend to register server: %s", e)
            return False

    def push_metrics(self, payload: dict) -> bool:
        """Send telemetry packet to CloudPulse backend."""
        url = f"{self.backend_url}/metrics"
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": agent_config.api_key
        }

        # Format metric ingestion payload matching backend expectations
        body = {
            "server_id": self.server_id,
            "timestamp": payload["timestamp"],
            "cpu_percent": payload["cpu"]["percent"],
            "load_1m": payload["cpu"]["load_1m"],
            "load_5m": payload["cpu"]["load_5m"],
            "load_15m": payload["cpu"]["load_15m"],
            "memory_percent": payload["memory"]["percent"],
            "memory_used_mb": payload["memory"]["used_mb"],
            "memory_available_mb": payload["memory"]["available_mb"],
            "disk_percent": payload["disk"]["percent"],
            "disk_used_gb": payload["disk"]["used_gb"],
            "disk_available_gb": payload["disk"]["free_gb"],
            "network_sent_bytes": payload["network"]["bytes_sent"],
            "network_recv_bytes": payload["network"]["bytes_recv"],
            "disk_read_bytes": payload["disk"]["io"]["read_bytes"],
            "disk_write_bytes": payload["disk"]["io"]["write_bytes"],
            "raw_metrics": payload
        }

        try:
            resp = requests.post(url, json=body, headers=headers, timeout=5)
            if resp.status_code in (200, 201):
                logger.info(
                    "Pushed telemetry to backend: CPU=%.1f%% Mem=%.1f%% Disk=%.1f%%",
                    body["cpu_percent"], body["memory_percent"], body["disk_percent"]
                )
                return True
            else:
                logger.error("Failed to push telemetry, status %d: %s", resp.status_code, resp.text)
                return False
        except Exception as e:
            logger.error("Backend connection error during metrics push: %s", e)
            return False

    def run_daemon(self):
        """Continuously collect and push metrics at the configured interval."""
        logger.info("Starting CloudPulse agent daemon for %s (interval=%ds)...", self.server_id, self.interval)
        
        # Initial collection to register host
        first_payload = self.collect()
        self.register_server(first_payload)
        self.push_metrics(first_payload)

        while True:
            try:
                time.sleep(self.interval)
                telemetry = self.collect()
                self.push_metrics(telemetry)
            except KeyboardInterrupt:
                logger.info("Agent daemon stopped by operator.")
                break
            except Exception as e:
                logger.exception("Unexpected error in agent collection cycle: %s", e)


def main():
    parser = argparse.ArgumentParser(description="CloudPulse Monitoring Agent")
    parser.add_argument("--once", action="store_true", help="Collect metrics once and output JSON to stdout")
    parser.add_argument("--daemon", action="store_true", help="Run continuously as background daemon")
    parser.add_argument("--server-id", type=str, help="Override Server ID")
    parser.add_argument("--backend-url", type=str, help="Override CloudPulse backend API URL")
    parser.add_argument("--interval", type=int, help="Collection interval in seconds")

    args = parser.parse_args()

    agent = CloudPulseAgent(
        server_id=args.server_id,
        backend_url=args.backend_url,
        interval=args.interval
    )

    if args.once:
        data = agent.collect()
        print(json.dumps(data, indent=2))
    elif args.daemon:
        agent.run_daemon()
    else:
        # Default: collect once and show pretty summary
        data = agent.collect()
        print(json.dumps(data, indent=2))


if __name__ == "__main__":
    main()

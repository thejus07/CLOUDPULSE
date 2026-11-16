"""
Network Diagnostics Module
Tests DNS resolution, socket connectivity, gateway reachability, and HTTP health endpoints.
"""

import socket
import time
from datetime import datetime, timezone
from typing import List, Dict, Any
import requests


class NetworkDiagnostics:
    """Diagnoses network stack faults, DNS failures, and HTTP endpoint availability."""

    def __init__(self, target_domains: List[str] = None, endpoints: List[str] = None):
        self.target_domains = target_domains or ["google.com", "amazon.com", "github.com", "localhost"]
        self.endpoints = endpoints or ["http://localhost:5000/api/health"]

    def run(self) -> dict:
        start_time = time.time()

        dns_results = self._test_dns(self.target_domains)
        socket_results = self._test_socket_connections()
        endpoint_results = self._test_http_endpoints(self.endpoints)

        status = "HEALTHY"
        root_causes = []
        recommendations = []

        # Analyze DNS
        dns_failures = [d for d in dns_results if not d["resolved"]]
        if dns_failures:
            status = "CRITICAL" if len(dns_failures) > 1 else "WARNING"
            failed_names = ", ".join([d["domain"] for d in dns_failures])
            root_causes.append(f"DNS Resolution failed for domain(s): {failed_names}.")
            recommendations.append("Check /etc/resolv.conf, systemd-resolved status, or local DNS cache / upstream nameservers (8.8.8.8, 1.1.1.1).")

        # Analyze HTTP endpoints
        failed_endpoints = [e for e in endpoint_results if not e["healthy"]]
        if failed_endpoints:
            # If internal health endpoint down, flag as warning or critical
            if status != "CRITICAL":
                status = "WARNING"
            failed_urls = ", ".join([e["url"] for e in failed_endpoints])
            root_causes.append(f"Application endpoint check failed for: {failed_urls}.")
            recommendations.append("Verify application web server process is actively bound to target port and accepting requests.")

        if not dns_failures and not failed_endpoints:
            root_causes.append("All network probes succeeded: DNS resolution fast, socket connections open, endpoints healthy.")
            recommendations.append("No immediate action required.")

        execution_duration = (time.time() - start_time) * 1000

        return {
            "diagnostic_type": "NETWORK",
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "execution_duration_ms": round(execution_duration, 2),
            "findings": {
                "dns": dns_results,
                "socket_tests": socket_results,
                "endpoint_tests": endpoint_results
            },
            "probable_root_cause": " | ".join(root_causes),
            "recommendations": recommendations,
            "raw_output": f"DNS: {len(dns_results) - len(dns_failures)}/{len(dns_results)} ok | Endpoints: {len(endpoint_results) - len(failed_endpoints)}/{len(endpoint_results)} healthy"
        }

    def _test_dns(self, domains: List[str]) -> List[Dict[str, Any]]:
        results = []
        for domain in domains:
            t0 = time.time()
            try:
                ip = socket.gethostbyname(domain)
                latency_ms = round((time.time() - t0) * 1000, 2)
                results.append({
                    "domain": domain,
                    "resolved": True,
                    "ip": ip,
                    "latency_ms": latency_ms
                })
            except Exception as e:
                latency_ms = round((time.time() - t0) * 1000, 2)
                results.append({
                    "domain": domain,
                    "resolved": False,
                    "error": str(e),
                    "latency_ms": latency_ms
                })
        return results

    def _test_socket_connections(self) -> List[Dict[str, Any]]:
        """Tests TCP 3-way handshake to common internet targets."""
        targets = [
            {"host": "1.1.1.1", "port": 53, "name": "Cloudflare DNS"},
            {"host": "8.8.8.8", "port": 53, "name": "Google DNS"},
            {"host": "127.0.0.1", "port": 5000, "name": "Local CloudPulse API"}
        ]
        results = []
        for target in targets:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2.0)
            t0 = time.time()
            try:
                s.connect((target["host"], target["port"]))
                latency_ms = round((time.time() - t0) * 1000, 2)
                results.append({
                    "target": target["name"],
                    "host": target["host"],
                    "port": target["port"],
                    "connected": True,
                    "latency_ms": latency_ms
                })
            except Exception as e:
                latency_ms = round((time.time() - t0) * 1000, 2)
                results.append({
                    "target": target["name"],
                    "host": target["host"],
                    "port": target["port"],
                    "connected": False,
                    "error": str(e),
                    "latency_ms": latency_ms
                })
            finally:
                s.close()
        return results

    def _test_http_endpoints(self, endpoints: List[str]) -> List[Dict[str, Any]]:
        results = []
        for url in endpoints:
            t0 = time.time()
            try:
                resp = requests.get(url, timeout=3.0)
                latency_ms = round((time.time() - t0) * 1000, 2)
                results.append({
                    "url": url,
                    "healthy": resp.status_code < 400,
                    "status_code": resp.status_code,
                    "latency_ms": latency_ms
                })
            except Exception as e:
                latency_ms = round((time.time() - t0) * 1000, 2)
                results.append({
                    "url": url,
                    "healthy": False,
                    "status_code": 0,
                    "error": str(e),
                    "latency_ms": latency_ms
                })
        return results

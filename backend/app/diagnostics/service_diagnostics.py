"""
Service Diagnostics Module
Inspects systemd services, detects failed units, extracts journalctl logs,
and analyzes error patterns (OOM, port conflicts, configuration errors).
"""

import time
import re
from datetime import datetime, timezone
from typing import List, Dict, Any
from agent.collectors.service_collector import ServiceCollector


class ServiceDiagnostics:
    """Diagnoses service outages, daemon crashes, and journalctl error traces."""

    def __init__(self, target_service: str = None, monitored_services: List[str] = None):
        self.target_service = target_service
        self.monitored_services = monitored_services or ["nginx", "postgresql", "redis", "cloudpulse-worker", "test-service"]
        self.collector = ServiceCollector(monitored_services=self.monitored_services)

    def run(self) -> dict:
        start_time = time.time()
        
        services_to_check = [self.target_service] if self.target_service else self.monitored_services
        service_statuses = []
        failed_services = []

        for svc in services_to_check:
            st = self.collector.check_service_status(svc)
            logs = self.collector.get_service_logs(svc, lines=30)
            st["recent_logs"] = logs.get("logs", "")
            
            # Analyze logs for signature errors
            error_signatures = self._analyze_log_errors(st["recent_logs"])
            st["error_signatures"] = error_signatures

            service_statuses.append(st)
            if not st["is_active"]:
                failed_services.append(st)

        status = "HEALTHY"
        root_causes = []
        recommendations = []

        if failed_services:
            status = "CRITICAL"
            for failed in failed_services:
                err_detail = " | ".join(failed["error_signatures"]) if failed["error_signatures"] else f"State is '{failed['state']}'"
                root_causes.append(f"Service '{failed['service']}' is DOWN ({err_detail}).")
                
                # Context-aware recommendations
                if any("address already in use" in e.lower() for e in failed["error_signatures"]):
                    recommendations.append(f"Port collision detected for {failed['service']}. Identify and kill overlapping socket owner using 'lsof -i :PORT' or 'netstat -tulnp'.")
                elif any("out of memory" in e.lower() or "oom" in e.lower() for e in failed["error_signatures"]):
                    recommendations.append(f"Service {failed['service']} was terminated by Linux OOM killer. Increase swap or adjust memory limit in systemd unit.")
                else:
                    recommendations.append(f"Execute approved automated restart of service '{failed['service']}'.")
        else:
            root_causes.append(f"All {len(service_statuses)} monitored services are active and running.")
            recommendations.append("No immediate action required.")

        execution_duration = (time.time() - start_time) * 1000

        return {
            "diagnostic_type": "SERVICE",
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "execution_duration_ms": round(execution_duration, 2),
            "findings": {
                "checked_services_count": len(service_statuses),
                "failed_count": len(failed_services),
                "services": service_statuses,
                "failed_services": failed_services
            },
            "probable_root_cause": " | ".join(root_causes),
            "recommendations": recommendations,
            "raw_output": f"Checked {len(service_statuses)} services: {len(failed_services)} failed. " + (f"Down: {', '.join([s['service'] for s in failed_services])}" if failed_services else "All healthy.")
        }

    def _analyze_log_errors(self, logs: str) -> List[str]:
        """Scans journalctl log excerpt for common system administration failures."""
        if not logs:
            return []

        signatures = []
        patterns = {
            "Address already in use": r"(bind: Address already in use|port \d+ already in use|EADDRINUSE)",
            "Out of Memory (OOM)": r"(Out of memory: Kill process|Killed process \d+|signal 9|exit-code=137)",
            "Permission Denied": r"(Permission denied|EACCES)",
            "Config Syntax Error": r"(syntax error|invalid configuration|failed to parse)",
            "Connection Refused": r"(Connection refused|ECONNREFUSED|failed to connect to upstream)",
            "Segmentation Fault": r"(segmentation fault|core dumped|SIGSEGV)"
        }

        for title, pattern in patterns.items():
            if re.search(pattern, logs, re.IGNORECASE):
                signatures.append(title)

        return signatures

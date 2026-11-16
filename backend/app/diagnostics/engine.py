"""
Diagnostic Engine Orchestrator
Coordinates independent diagnostic modules, saves forensic reports to database,
and enriches incidents with automated root-cause analyses.
"""

import uuid
from datetime import datetime, timezone
from backend.app.models.database import SessionLocal
from backend.app.models.diagnostic import DiagnosticReport
from backend.app.models.incident import Incident
from backend.app.diagnostics.cpu_diagnostics import CPUDiagnostics
from backend.app.diagnostics.memory_diagnostics import MemoryDiagnostics
from backend.app.diagnostics.disk_diagnostics import DiskDiagnostics
from backend.app.diagnostics.service_diagnostics import ServiceDiagnostics
from backend.app.diagnostics.network_diagnostics import NetworkDiagnostics
from backend.app.config import config


class DiagnosticEngine:
    """Central engine executing deep-dive diagnostic routines across system layers."""

    @staticmethod
    def run_diagnostic(diagnostic_type: str, server_id: str, incident_id: str = None, params: dict = None) -> dict:
        """Run a single diagnostic check (CPU, MEMORY, DISK, SERVICE, NETWORK)."""
        diag_type = diagnostic_type.upper().strip()
        params = params or {}

        if diag_type == "CPU":
            module = CPUDiagnostics(
                warning_threshold=config.THRESHOLD_CPU_WARNING,
                critical_threshold=config.THRESHOLD_CPU_CRITICAL
            )
            result = module.run()
        elif diag_type == "MEMORY":
            module = MemoryDiagnostics(
                warning_threshold=config.THRESHOLD_MEMORY_WARNING,
                critical_threshold=config.THRESHOLD_MEMORY_CRITICAL
            )
            result = module.run()
        elif diag_type == "DISK":
            module = DiskDiagnostics(
                target_path=params.get("path"),
                warning_threshold=config.THRESHOLD_DISK_WARNING,
                critical_threshold=config.THRESHOLD_DISK_CRITICAL
            )
            result = module.run()
        elif diag_type == "SERVICE":
            module = ServiceDiagnostics(
                target_service=params.get("service"),
                monitored_services=config.ALLOWED_SERVICES
            )
            result = module.run()
        elif diag_type == "NETWORK":
            module = NetworkDiagnostics(
                target_domains=params.get("domains")
            )
            result = module.run()
        else:
            raise ValueError(f"Unknown diagnostic type: {diagnostic_type}")

        # Persist report to database
        db = SessionLocal()
        try:
            report_id = f"DIAG-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:4].upper()}"
            db_report = DiagnosticReport(
                id=report_id,
                server_id=server_id,
                incident_id=incident_id,
                diagnostic_type=diag_type,
                status=result["status"],
                findings_json=None,  # will set via property setter
                raw_output=result["raw_output"],
                execution_duration_ms=result["execution_duration_ms"]
            )
            db_report.findings = result["findings"]
            db_report.recommendations = result["recommendations"]

            db.add(db_report)

            # If associated with an active incident, enrich the incident with findings and RCA
            if incident_id:
                inc = db.query(Incident).filter(Incident.id == incident_id).first()
                if inc:
                    if result["status"] in ("CRITICAL", "WARNING"):
                        inc.probable_root_cause = result["probable_root_cause"]
                        inc.recommended_resolution = "\n".join(result["recommendations"])
                        # Merge findings
                        current_findings = inc.findings
                        current_findings[diag_type] = result["findings"]
                        inc.findings = current_findings
                        inc.status = "INVESTIGATING"

            db.commit()
            db.refresh(db_report)
            report_dict = db_report.to_dict()
            report_dict["probable_root_cause"] = result["probable_root_cause"]
            return report_dict
        finally:
            db.close()

    @staticmethod
    def run_comprehensive(server_id: str, incident_id: str = None) -> dict:
        """Runs a complete diagnostic sweep across CPU, Memory, Disk, Service, and Network."""
        results = {}
        for diag_type in ["CPU", "MEMORY", "DISK", "SERVICE", "NETWORK"]:
            try:
                results[diag_type] = DiagnosticEngine.run_diagnostic(
                    diagnostic_type=diag_type,
                    server_id=server_id,
                    incident_id=incident_id
                )
            except Exception as e:
                results[diag_type] = {
                    "diagnostic_type": diag_type,
                    "status": "FAILED",
                    "error": str(e)
                }

        # Determine overall status
        statuses = [r.get("status") for r in results.values()]
        overall_status = "CRITICAL" if "CRITICAL" in statuses else ("WARNING" if "WARNING" in statuses else "HEALTHY")

        return {
            "server_id": server_id,
            "overall_status": overall_status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "diagnostics": results
        }

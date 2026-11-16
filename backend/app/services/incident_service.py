"""
Incident Management Service
Handles alert detection, deduplication, auto-investigation, state transitions,
resolution verification, and AWS SNS notifications.
"""

import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.app.models.database import SessionLocal
from backend.app.models.incident import Incident
from backend.app.models.server import Server
from backend.app.models.audit import AuditLog
from backend.app.diagnostics.engine import DiagnosticEngine
from backend.app.config import config


class IncidentService:
    """Manages the end-to-end incident lifecycle from detection to recovery."""

    @staticmethod
    def create_or_update_incident(
        server_id: str,
        alert_type: str,
        title: str,
        description: str,
        severity: str,
        affected_resource: str,
        findings: dict = None,
        auto_investigate: bool = True
    ) -> Incident:
        """
        Creates an incident or updates an existing ongoing incident to prevent duplicate alerts.
        """
        db: Session = SessionLocal()
        try:
            dedup_key = f"{server_id}:{alert_type}:{affected_resource}"
            now = datetime.now(timezone.utc)

            # Check for existing active incident with same fingerprint
            existing = db.query(Incident).filter(
                Incident.dedup_key == dedup_key,
                Incident.status.notin_(["RESOLVED"])
            ).first()

            if existing:
                # Update existing incident with latest findings & severity if escalated
                if severity == "CRITICAL" and existing.severity != "CRITICAL":
                    existing.severity = "CRITICAL"
                existing.updated_at = now
                if findings:
                    curr = existing.findings
                    curr.update(findings)
                    existing.findings = curr
                db.commit()
                db.refresh(existing)
                return existing

            # Generate unique incident number: e.g. INC-20260216-7F12
            inc_id = f"INC-{now.strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}"

            incident = Incident(
                id=inc_id,
                server_id=server_id,
                title=title,
                description=description,
                severity=severity.upper(),
                status="DETECTED",
                affected_resource=affected_resource,
                dedup_key=dedup_key,
                detected_at=now,
                updated_at=now
            )
            if findings:
                incident.findings = findings

            db.add(incident)
            db.commit()
            db.refresh(incident)

            # Audit log
            audit = AuditLog(
                user_id="CloudPulse-Detector",
                action="INCIDENT_DETECTED",
                target_type="INCIDENT",
                target_id=incident.id,
                details={"title": title, "severity": severity, "server_id": server_id}
            )
            db.add(audit)
            db.commit()

            # Optional automatic investigation trigger
            if auto_investigate:
                diag_type_map = {
                    "CPU_SATURATION": "CPU",
                    "MEMORY_EXHAUSTION": "MEMORY",
                    "DISK_FULL": "DISK",
                    "SERVICE_DOWN": "SERVICE",
                    "NETWORK_FAULT": "NETWORK"
                }
                diag_type = diag_type_map.get(alert_type.upper(), "CPU")
                try:
                    diag_res = DiagnosticEngine.run_diagnostic(
                        diagnostic_type=diag_type,
                        server_id=server_id,
                        incident_id=incident.id
                    )
                    incident.status = "OPEN"
                    db.commit()
                    db.refresh(incident)
                except Exception as e:
                    incident.status = "OPEN"
                    incident.probable_root_cause = f"Diagnostic trigger encountered: {e}"
                    db.commit()

            # Publish to SNS if enabled
            if config.ENABLE_AWS_INTEGRATION and config.AWS_SNS_INCIDENT_TOPIC_ARN:
                try:
                    from backend.app.integrations.aws_client import AWSClient
                    AWSClient.publish_sns_alert(
                        topic_arn=config.AWS_SNS_INCIDENT_TOPIC_ARN,
                        subject=f"[{incident.severity}] CloudPulse Alert: {incident.title}",
                        message=f"Incident {incident.id} detected on server {server_id}.\nResource: {affected_resource}\nSeverity: {severity}\nDescription: {description}"
                    )
                except Exception:
                    pass

            return incident
        finally:
            db.close()

    @staticmethod
    def get_incidents(
        status: Optional[str] = None,
        severity: Optional[str] = None,
        server_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[dict]:
        db: Session = SessionLocal()
        try:
            query = db.query(Incident)
            if status:
                query = query.filter(Incident.status == status.upper())
            if severity:
                query = query.filter(Incident.severity == severity.upper())
            if server_id:
                query = query.filter(Incident.server_id == server_id)

            incidents = query.order_by(Incident.detected_at.desc()).offset(offset).limit(limit).all()
            return [inc.to_dict() for inc in incidents]
        finally:
            db.close()

    @staticmethod
    def get_incident_by_id(incident_id: str) -> Optional[dict]:
        db: Session = SessionLocal()
        try:
            inc = db.query(Incident).filter(Incident.id == incident_id).first()
            if not inc:
                return None
            data = inc.to_dict()
            # Include related diagnostics and remediations
            data["diagnostics"] = [d.to_dict() for d in inc.diagnostics]
            data["remediations"] = [r.to_dict() for r in inc.remediations]
            return data
        finally:
            db.close()

    @staticmethod
    def update_incident_status(incident_id: str, new_status: str, user_id: str = "engineer", notes: str = None) -> Optional[dict]:
        valid_statuses = ["DETECTED", "INVESTIGATING", "OPEN", "RESOLVING", "RESOLVED", "ESCALATED"]
        new_status = new_status.upper().strip()
        if new_status not in valid_statuses:
            raise ValueError(f"Invalid status '{new_status}'. Allowed: {', '.join(valid_statuses)}")

        db: Session = SessionLocal()
        try:
            inc = db.query(Incident).filter(Incident.id == incident_id).first()
            if not inc:
                return None

            old_status = inc.status
            inc.status = new_status
            inc.updated_at = datetime.now(timezone.utc)

            if new_status == "RESOLVED":
                inc.resolved_at = datetime.now(timezone.utc)
                if notes:
                    inc.recovery_verification = notes
            elif new_status == "OPEN" and not inc.acknowledged_at:
                inc.acknowledged_at = datetime.now(timezone.utc)

            # Audit
            audit = AuditLog(
                user_id=user_id,
                action="INCIDENT_STATUS_CHANGE",
                target_type="INCIDENT",
                target_id=incident_id,
                details={"old_status": old_status, "new_status": new_status, "notes": notes}
            )
            db.add(audit)
            db.commit()
            db.refresh(inc)
            return inc.to_dict()
        finally:
            db.close()

    @staticmethod
    def evaluate_telemetry(server_id: str, metrics: dict):
        """
        Analyzes incoming metrics against thresholds and failed services,
        triggering or resolving incidents automatically.
        """
        cpu_percent = metrics.get("cpu_percent", 0.0)
        mem_percent = metrics.get("memory_percent", 0.0)
        disk_percent = metrics.get("disk_percent", 0.0)
        raw = metrics.get("raw_metrics", {})
        failed_services = raw.get("failed_services", [])

        # 1. CPU Threshold
        if cpu_percent >= config.THRESHOLD_CPU_CRITICAL:
            IncidentService.create_or_update_incident(
                server_id=server_id,
                alert_type="CPU_SATURATION",
                title=f"Critical CPU Saturation ({cpu_percent}%)",
                description=f"Host CPU usage reached {cpu_percent}%, exceeding critical threshold of {config.THRESHOLD_CPU_CRITICAL}%.",
                severity="CRITICAL",
                affected_resource="Compute / CPU"
            )
        elif cpu_percent >= config.THRESHOLD_CPU_WARNING:
            IncidentService.create_or_update_incident(
                server_id=server_id,
                alert_type="CPU_SATURATION",
                title=f"Elevated CPU Usage ({cpu_percent}%)",
                description=f"Host CPU usage reached {cpu_percent}%, exceeding warning threshold of {config.THRESHOLD_CPU_WARNING}%.",
                severity="MEDIUM",
                affected_resource="Compute / CPU"
            )
        else:
            # Auto-resolve CPU incident if utilization normalized below warning
            IncidentService._check_and_auto_resolve(server_id, "CPU_SATURATION", f"CPU utilization returned to normal: {cpu_percent}%")

        # 2. Memory Threshold
        if mem_percent >= config.THRESHOLD_MEMORY_CRITICAL:
            IncidentService.create_or_update_incident(
                server_id=server_id,
                alert_type="MEMORY_EXHAUSTION",
                title=f"Critical Memory Exhaustion ({mem_percent}%)",
                description=f"Host memory usage reached {mem_percent}%, exceeding critical threshold of {config.THRESHOLD_MEMORY_CRITICAL}%.",
                severity="CRITICAL",
                affected_resource="Memory / RAM"
            )
        elif mem_percent >= config.THRESHOLD_MEMORY_WARNING:
            IncidentService.create_or_update_incident(
                server_id=server_id,
                alert_type="MEMORY_EXHAUSTION",
                title=f"Elevated Memory Usage ({mem_percent}%)",
                description=f"Host memory usage reached {mem_percent}%, exceeding warning threshold of {config.THRESHOLD_MEMORY_WARNING}%.",
                severity="MEDIUM",
                affected_resource="Memory / RAM"
            )
        else:
            IncidentService._check_and_auto_resolve(server_id, "MEMORY_EXHAUSTION", f"Memory utilization returned to normal: {mem_percent}%")

        # 3. Disk Threshold
        if disk_percent >= config.THRESHOLD_DISK_CRITICAL:
            IncidentService.create_or_update_incident(
                server_id=server_id,
                alert_type="DISK_FULL",
                title=f"Critical Filesystem Full ({disk_percent}%)",
                description=f"Disk usage reached {disk_percent}%, exceeding critical threshold of {config.THRESHOLD_DISK_CRITICAL}%.",
                severity="CRITICAL",
                affected_resource="Filesystem / Root"
            )
        elif disk_percent >= config.THRESHOLD_DISK_WARNING:
            IncidentService.create_or_update_incident(
                server_id=server_id,
                alert_type="DISK_FULL",
                title=f"High Disk Usage Warning ({disk_percent}%)",
                description=f"Disk usage reached {disk_percent}%, exceeding warning threshold of {config.THRESHOLD_DISK_WARNING}%.",
                severity="HIGH",
                affected_resource="Filesystem / Root"
            )

        # 4. Failed Services
        for failed in failed_services:
            svc_name = failed.get("unit") or failed.get("service")
            IncidentService.create_or_update_incident(
                server_id=server_id,
                alert_type="SERVICE_DOWN",
                title=f"Critical Service Failure: {svc_name}",
                description=f"Systemd service '{svc_name}' entered degraded/failed state: {failed.get('state', 'failed')}.",
                severity="HIGH",
                affected_resource=f"systemd:{svc_name}"
            )

    @staticmethod
    def _check_and_auto_resolve(server_id: str, alert_type: str, resolution_reason: str):
        """Auto-resolves ongoing alert if metric recovered."""
        db: Session = SessionLocal()
        try:
            prefix = f"{server_id}:{alert_type}:"
            incidents = db.query(Incident).filter(
                Incident.dedup_key.startswith(prefix),
                Incident.status.in_(["OPEN", "DETECTED", "INVESTIGATING", "RESOLVING"])
            ).all()

            for inc in incidents:
                inc.status = "RESOLVED"
                inc.resolved_at = datetime.now(timezone.utc)
                inc.recovery_verification = f"Automated recovery verified: {resolution_reason}"
                audit = AuditLog(
                    user_id="CloudPulse-AutoRecovery",
                    action="INCIDENT_AUTO_RESOLVED",
                    target_type="INCIDENT",
                    target_id=inc.id,
                    details={"reason": resolution_reason}
                )
                db.add(audit)
            db.commit()
        finally:
            db.close()

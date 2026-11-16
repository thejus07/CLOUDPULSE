"""
Incident Model for CloudPulse
Manages full lifecycle of alerts, root cause analyses, and resolutions.
"""

from datetime import datetime, timezone
import json
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from backend.app.models.database import Base


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(String(64), primary_key=True, index=True)  # e.g. INC-20260216-1042
    server_id = Column(String(64), ForeignKey("servers.id", ondelete="CASCADE"), nullable=False, index=True)
    
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    
    # Severity: INFO, LOW, MEDIUM, HIGH, CRITICAL
    severity = Column(String(32), default="MEDIUM", index=True)
    
    # Status: DETECTED, INVESTIGATING, OPEN, RESOLVING, RESOLVED, ESCALATED
    status = Column(String(32), default="DETECTED", index=True)
    
    affected_resource = Column(String(128), nullable=False)  # e.g., "Filesystem: /var", "Process: nginx"
    
    # Deduplication fingerprint: e.g. "{server_id}:{resource}:{issue_type}"
    dedup_key = Column(String(255), nullable=True, index=True)
    
    # Diagnostic & RCA details
    probable_root_cause = Column(Text, nullable=True)
    recommended_resolution = Column(Text, nullable=True)
    recovery_verification = Column(Text, nullable=True)
    findings_json = Column(Text, default="{}")
    metadata_json = Column(Text, default="{}")

    # Timestamps
    detected_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    acknowledged_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    server = relationship("Server", back_populates="incidents")
    diagnostics = relationship("DiagnosticReport", back_populates="incident", cascade="all, delete-orphan", order_by="desc(DiagnosticReport.created_at)")
    remediations = relationship("RemediationAction", back_populates="incident", cascade="all, delete-orphan", order_by="desc(RemediationAction.started_at)")

    __table_args__ = (
        Index("idx_incident_status_severity", "status", "severity"),
    )

    @property
    def findings(self):
        try:
            return json.loads(self.findings_json) if self.findings_json else {}
        except Exception:
            return {}

    @findings.setter
    def findings(self, val):
        self.findings_json = json.dumps(val) if val else "{}"

    @property
    def meta_info(self):
        try:
            return json.loads(self.metadata_json) if self.metadata_json else {}
        except Exception:
            return {}

    @meta_info.setter
    def meta_info(self, val):
        self.metadata_json = json.dumps(val) if val else "{}"

    def to_dict(self):
        # Calculate resolution duration in seconds if resolved
        resolution_time_seconds = None
        if self.resolved_at and self.detected_at:
            resolution_time_seconds = max(0, int((self.resolved_at - self.detected_at).total_seconds()))

        return {
            "id": self.id,
            "server_id": self.server_id,
            "hostname": self.server.hostname if self.server else "Unknown",
            "title": self.title,
            "description": self.description,
            "severity": self.severity,
            "status": self.status,
            "affected_resource": self.affected_resource,
            "dedup_key": self.dedup_key,
            "probable_root_cause": self.probable_root_cause,
            "recommended_resolution": self.recommended_resolution,
            "recovery_verification": self.recovery_verification,
            "findings": self.findings,
            "metadata": self.meta_info,
            "detected_at": self.detected_at.isoformat() if self.detected_at else None,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolution_time_seconds": resolution_time_seconds,
            "remediation_count": len(self.remediations) if self.remediations else 0
        }

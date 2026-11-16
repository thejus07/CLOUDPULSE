"""
DiagnosticReport Model for CloudPulse
Stores deep-dive diagnostic findings and investigations.
"""

from datetime import datetime, timezone
import json
from sqlalchemy import Column, String, Integer, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.models.database import Base


class DiagnosticReport(Base):
    __tablename__ = "diagnostic_reports"

    id = Column(String(64), primary_key=True, index=True)  # e.g. DIAG-20260216-01
    server_id = Column(String(64), ForeignKey("servers.id", ondelete="CASCADE"), nullable=False, index=True)
    incident_id = Column(String(64), ForeignKey("incidents.id", ondelete="SET NULL"), nullable=True, index=True)

    # Diagnostic Type: CPU, MEMORY, DISK, SERVICE, NETWORK, COMPREHENSIVE
    diagnostic_type = Column(String(32), nullable=False, index=True)
    status = Column(String(32), default="SUCCESS")  # SUCCESS, WARNING, CRITICAL, FAILED

    findings_json = Column(Text, default="{}")
    recommendations_json = Column(Text, default="[]")
    raw_output = Column(Text, default="")
    execution_duration_ms = Column(Float, default=0.0)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    # Relationships
    server = relationship("Server", back_populates="diagnostics")
    incident = relationship("Incident", back_populates="diagnostics")

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
    def recommendations(self):
        try:
            return json.loads(self.recommendations_json) if self.recommendations_json else []
        except Exception:
            return []

    @recommendations.setter
    def recommendations(self, val):
        self.recommendations_json = json.dumps(val) if val else "[]"

    def to_dict(self):
        return {
            "id": self.id,
            "server_id": self.server_id,
            "incident_id": self.incident_id,
            "diagnostic_type": self.diagnostic_type,
            "status": self.status,
            "findings": self.findings,
            "recommendations": self.recommendations,
            "raw_output": self.raw_output,
            "execution_duration_ms": round(self.execution_duration_ms, 2),
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

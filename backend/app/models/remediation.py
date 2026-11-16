"""
RemediationAction Model for CloudPulse
Audit logs every automated or approved recovery action, pre-checks, post-checks, and outcomes.
"""

from datetime import datetime, timezone
import json
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.models.database import Base


class RemediationAction(Base):
    __tablename__ = "remediation_actions"

    id = Column(String(64), primary_key=True, index=True)  # e.g. REM-20260216-01
    server_id = Column(String(64), ForeignKey("servers.id", ondelete="CASCADE"), nullable=False, index=True)
    incident_id = Column(String(64), ForeignKey("incidents.id", ondelete="SET NULL"), nullable=True, index=True)

    action_type = Column(String(64), nullable=False)  # RESTART_SERVICE, CLEAN_TEMP_FILES, ROTATE_LOGS, etc.
    command_name = Column(String(128), nullable=False)
    parameters_json = Column(Text, default="{}")

    # Status: PENDING_APPROVAL, EXECUTING, SUCCESS, FAILED, REVERTED
    status = Column(String(32), default="PENDING_APPROVAL", index=True)
    executed_by = Column(String(64), default="SYSTEM_AUTOMATION")  # or user email

    pre_check_json = Column(Text, default="{}")
    post_check_json = Column(Text, default="{}")
    output_log = Column(Text, default="")
    error_log = Column(Text, default="")

    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    server = relationship("Server", back_populates="remediations")
    incident = relationship("Incident", back_populates="remediations")

    @property
    def parameters(self):
        try:
            return json.loads(self.parameters_json) if self.parameters_json else {}
        except Exception:
            return {}

    @parameters.setter
    def parameters(self, val):
        self.parameters_json = json.dumps(val) if val else "{}"

    @property
    def pre_check(self):
        try:
            return json.loads(self.pre_check_json) if self.pre_check_json else {}
        except Exception:
            return {}

    @pre_check.setter
    def pre_check(self, val):
        self.pre_check_json = json.dumps(val) if val else "{}"

    @property
    def post_check(self):
        try:
            return json.loads(self.post_check_json) if self.post_check_json else {}
        except Exception:
            return {}

    @post_check.setter
    def post_check(self, val):
        self.post_check_json = json.dumps(val) if val else "{}"

    def to_dict(self):
        duration_seconds = None
        if self.completed_at and self.started_at:
            duration_seconds = max(0, round((self.completed_at - self.started_at).total_seconds(), 2))

        return {
            "id": self.id,
            "server_id": self.server_id,
            "incident_id": self.incident_id,
            "action_type": self.action_type,
            "command_name": self.command_name,
            "parameters": self.parameters,
            "status": self.status,
            "executed_by": self.executed_by,
            "pre_check": self.pre_check,
            "post_check": self.post_check,
            "output_log": self.output_log,
            "error_log": self.error_log,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": duration_seconds
        }

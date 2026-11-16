"""
AuditLog Model for CloudPulse
Guarantees full forensic trace of every administrative and remediation action.
"""

from datetime import datetime, timezone
import json
from sqlalchemy import Column, Integer, String, Text, DateTime
from backend.app.models.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(64), default="system")
    action = Column(String(128), nullable=False, index=True)
    target_type = Column(String(64), nullable=False)  # SERVER, INCIDENT, REMEDIATION, CONFIG
    target_id = Column(String(64), nullable=True)
    details_json = Column(Text, default="{}")
    ip_address = Column(String(64), nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    @property
    def details(self):
        try:
            return json.loads(self.details_json) if self.details_json else {}
        except Exception:
            return {}

    @details.setter
    def details(self, val):
        self.details_json = json.dumps(val) if val else "{}"

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "action": self.action,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "details": self.details,
            "ip_address": self.ip_address,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }

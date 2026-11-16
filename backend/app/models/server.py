"""
Server Model for CloudPulse
Represents a monitored Linux/host instance.
"""

from datetime import datetime, timezone
import json
from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, Text
from sqlalchemy.orm import relationship
from backend.app.models.database import Base


class Server(Base):
    __tablename__ = "servers"

    id = Column(String(64), primary_key=True, index=True)  # e.g., srv-production-01 or machine UUID
    hostname = Column(String(255), nullable=False, index=True)
    ip_address = Column(String(64), nullable=True)
    os_name = Column(String(64), default="Linux")
    os_version = Column(String(128), default="Ubuntu 22.04 LTS")
    architecture = Column(String(32), default="x86_64")
    cpu_cores = Column(Integer, default=4)
    total_memory_mb = Column(Float, default=8192.0)
    total_disk_gb = Column(Float, default=100.0)
    status = Column(String(32), default="HEALTHY", index=True)  # HEALTHY, WARNING, CRITICAL, OFFLINE
    last_heartbeat = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    is_local = Column(Boolean, default=True)
    aws_instance_id = Column(String(64), nullable=True)
    aws_region = Column(String(32), nullable=True)
    tags_json = Column(Text, default="{}")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    metrics = relationship("SystemMetric", back_populates="server", cascade="all, delete-orphan", order_by="desc(SystemMetric.timestamp)")
    incidents = relationship("Incident", back_populates="server", cascade="all, delete-orphan", order_by="desc(Incident.detected_at)")
    diagnostics = relationship("DiagnosticReport", back_populates="server", cascade="all, delete-orphan", order_by="desc(DiagnosticReport.created_at)")
    remediations = relationship("RemediationAction", back_populates="server", cascade="all, delete-orphan")

    @property
    def tags(self):
        try:
            return json.loads(self.tags_json) if self.tags_json else {}
        except Exception:
            return {}

    @tags.setter
    def tags(self, val):
        self.tags_json = json.dumps(val) if val else "{}"

    def to_dict(self):
        return {
            "id": self.id,
            "hostname": self.hostname,
            "ip_address": self.ip_address,
            "os_name": self.os_name,
            "os_version": self.os_version,
            "architecture": self.architecture,
            "cpu_cores": self.cpu_cores,
            "total_memory_mb": round(self.total_memory_mb, 2) if self.total_memory_mb else 0,
            "total_disk_gb": round(self.total_disk_gb, 2) if self.total_disk_gb else 0,
            "status": self.status,
            "last_heartbeat": self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            "is_local": self.is_local,
            "aws_instance_id": self.aws_instance_id,
            "aws_region": self.aws_region,
            "tags": self.tags,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

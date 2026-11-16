"""
SystemMetric Model for CloudPulse
Stores periodic time-series metrics collected by monitoring agents.
"""

from datetime import datetime, timezone
import json
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Index
from sqlalchemy.orm import relationship
from backend.app.models.database import Base


class SystemMetric(Base):
    __tablename__ = "system_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    server_id = Column(String(64), ForeignKey("servers.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    # CPU
    cpu_percent = Column(Float, nullable=False)
    load_1m = Column(Float, default=0.0)
    load_5m = Column(Float, default=0.0)
    load_15m = Column(Float, default=0.0)

    # Memory
    memory_percent = Column(Float, nullable=False)
    memory_used_mb = Column(Float, default=0.0)
    memory_available_mb = Column(Float, default=0.0)

    # Disk
    disk_percent = Column(Float, nullable=False)
    disk_used_gb = Column(Float, default=0.0)
    disk_available_gb = Column(Float, default=0.0)

    # I/O & Network rates / counters
    network_sent_bytes = Column(Float, default=0.0)
    network_recv_bytes = Column(Float, default=0.0)
    disk_read_bytes = Column(Float, default=0.0)
    disk_write_bytes = Column(Float, default=0.0)

    # Full structured payload
    raw_metrics_json = Column(Text, default="{}")

    # Relationship
    server = relationship("Server", back_populates="metrics")

    __table_args__ = (
        Index("idx_metric_server_timestamp", "server_id", "timestamp"),
    )

    @property
    def raw_metrics(self):
        try:
            return json.loads(self.raw_metrics_json) if self.raw_metrics_json else {}
        except Exception:
            return {}

    @raw_metrics.setter
    def raw_metrics(self, val):
        self.raw_metrics_json = json.dumps(val) if val else "{}"

    def to_dict(self):
        return {
            "id": self.id,
            "server_id": self.server_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "cpu_percent": round(self.cpu_percent, 2),
            "load_1m": round(self.load_1m, 2),
            "load_5m": round(self.load_5m, 2),
            "load_15m": round(self.load_15m, 2),
            "memory_percent": round(self.memory_percent, 2),
            "memory_used_mb": round(self.memory_used_mb, 2),
            "memory_available_mb": round(self.memory_available_mb, 2),
            "disk_percent": round(self.disk_percent, 2),
            "disk_used_gb": round(self.disk_used_gb, 2),
            "disk_available_gb": round(self.disk_available_gb, 2),
            "network_sent_bytes": self.network_sent_bytes,
            "network_recv_bytes": self.network_recv_bytes,
            "disk_read_bytes": self.disk_read_bytes,
            "disk_write_bytes": self.disk_write_bytes,
            "raw_metrics": self.raw_metrics
        }

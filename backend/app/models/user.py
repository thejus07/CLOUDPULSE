"""
User Model for CloudPulse
Manages operators, engineers, and API keys.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, Boolean
from backend.app.models.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    email = Column(String(128), unique=True, nullable=False, index=True)
    role = Column(String(32), default="SUPPORT_ENGINEER")  # ADMIN, SUPPORT_ENGINEER, VIEWER
    api_key = Column(String(128), unique=True, nullable=True, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

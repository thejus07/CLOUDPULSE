"""
Database Session and Engine Management for CloudPulse
Supports both SQLite (local development) and PostgreSQL (production).
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session
from backend.app.config import config

# Create Engine with connection pooling settings appropriate for DB type
connect_args = {}
if config.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    config.DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True
)

SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, expire_on_commit=False, bind=engine))
Base = declarative_base()


def get_db():
    """Context-aware DB session generator."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize all tables."""
    import backend.app.models.server  # noqa
    import backend.app.models.metric  # noqa
    import backend.app.models.incident  # noqa
    import backend.app.models.diagnostic  # noqa
    import backend.app.models.remediation  # noqa
    import backend.app.models.user  # noqa
    import backend.app.models.audit  # noqa
    Base.metadata.create_all(bind=engine)

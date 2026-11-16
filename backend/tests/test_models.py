"""
Unit tests for CloudPulse SQLAlchemy Models
"""

import pytest
from datetime import datetime, timezone
from backend.app.models.database import SessionLocal, init_db
from backend.app.models.server import Server
from backend.app.models.metric import SystemMetric
from backend.app.models.incident import Incident
from backend.app.models.diagnostic import DiagnosticReport
from backend.app.models.remediation import RemediationAction


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    init_db()


def test_server_creation_and_dict():
    db = SessionLocal()
    try:
        server = Server(
            id="srv-unit-test-01",
            hostname="test-node-01.infra",
            ip_address="10.0.1.50",
            os_name="Linux",
            os_version="Ubuntu 22.04 LTS",
            cpu_cores=8,
            total_memory_mb=16384.0,
            total_disk_gb=250.0,
            status="HEALTHY"
        )
        server.tags = {"environment": "production", "tier": "web"}
        db.merge(server)
        db.commit()

        fetched = db.query(Server).filter(Server.id == "srv-unit-test-01").first()
        assert fetched is not None
        assert fetched.hostname == "test-node-01.infra"
        assert fetched.tags["environment"] == "production"

        s_dict = fetched.to_dict()
        assert s_dict["id"] == "srv-unit-test-01"
        assert s_dict["cpu_cores"] == 8
    finally:
        db.close()


def test_metric_creation():
    db = SessionLocal()
    try:
        metric = SystemMetric(
            server_id="srv-unit-test-01",
            cpu_percent=45.5,
            load_1m=1.2,
            load_5m=1.0,
            load_15m=0.8,
            memory_percent=60.0,
            memory_used_mb=9830.4,
            memory_available_mb=6553.6,
            disk_percent=35.0,
            disk_used_gb=87.5,
            disk_available_gb=162.5
        )
        db.add(metric)
        db.commit()

        assert metric.id is not None
        m_dict = metric.to_dict()
        assert m_dict["cpu_percent"] == 45.5
        assert m_dict["server_id"] == "srv-unit-test-01"
    finally:
        db.close()


def test_incident_and_remediation_relationship():
    db = SessionLocal()
    try:
        inc = Incident(
            id="INC-TEST-0001",
            server_id="srv-unit-test-01",
            title="Test Disk Saturation",
            description="Disk utilization exceeded 90%",
            severity="CRITICAL",
            status="OPEN",
            affected_resource="Filesystem: /"
        )
        db.merge(inc)
        db.commit()

        action = RemediationAction(
            id="REM-TEST-0001",
            server_id="srv-unit-test-01",
            incident_id="INC-TEST-0001",
            action_type="CLEAN_TEMP_FILES",
            command_name="clean_temp_files",
            status="SUCCESS",
            executed_by="tester"
        )
        db.merge(action)
        db.commit()

        fetched_inc = db.query(Incident).filter(Incident.id == "INC-TEST-0001").first()
        assert fetched_inc is not None
        assert len(fetched_inc.remediations) >= 1
        assert fetched_inc.remediations[0].id == "REM-TEST-0001"
    finally:
        db.close()

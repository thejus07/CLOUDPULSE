"""
Unit tests for CloudPulse Incident Management Engine
"""

from backend.app.services.incident_service import IncidentService


def test_incident_creation_and_deduplication():
    # 1. Create first incident
    inc1 = IncidentService.create_or_update_incident(
        server_id="srv-incident-node",
        alert_type="CPU_SATURATION",
        title="High CPU Saturation Alert",
        description="CPU at 95%",
        severity="CRITICAL",
        affected_resource="Compute / CPU",
        auto_investigate=False
    )
    assert inc1.id.startswith("INC-")
    assert inc1.status == "DETECTED"

    # 2. Trigger second alert for same condition (should deduplicate and update existing, not create new!)
    inc2 = IncidentService.create_or_update_incident(
        server_id="srv-incident-node",
        alert_type="CPU_SATURATION",
        title="High CPU Saturation Alert",
        description="CPU still at 96%",
        severity="CRITICAL",
        affected_resource="Compute / CPU",
        auto_investigate=False
    )
    assert inc1.id == inc2.id


def test_incident_status_transition():
    inc = IncidentService.create_or_update_incident(
        server_id="srv-incident-node",
        alert_type="SERVICE_DOWN",
        title="Postgres Service Down",
        description="Postgres failed",
        severity="HIGH",
        affected_resource="systemd:postgresql",
        auto_investigate=False
    )

    # Transition to INVESTIGATING
    updated = IncidentService.update_incident_status(inc.id, "INVESTIGATING", notes="Engineer started diagnosis")
    assert updated["status"] == "INVESTIGATING"

    # Transition to RESOLVED
    resolved = IncidentService.update_incident_status(inc.id, "RESOLVED", notes="Service restarted and healthy")
    assert resolved["status"] == "RESOLVED"
    assert resolved["resolved_at"] is not None

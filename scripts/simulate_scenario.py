#!/usr/bin/env python3
"""
CloudPulse Failure Simulation & Verification Script
Safely executes controlled failure scenarios to demonstrate end-to-end Support Engineering workflows:
1. Detect anomaly
2. Create incident
3. Run diagnostics & identify root cause
4. Recommend approved remediation
5. Execute remediation with safety checks
6. Verify recovery & update incident to RESOLVED
"""

import sys
import os
import time
import argparse
import json

# Add root directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.models.database import SessionLocal, init_db
from backend.app.models.server import Server
from backend.app.models.incident import Incident
from backend.app.services.incident_service import IncidentService
from backend.app.diagnostics.engine import DiagnosticEngine
from backend.app.remediation.remediation_engine import RemediationEngine
from backend.app.services.simulation_service import SimulationService


def ensure_test_server(server_id="srv-sim-node-01"):
    init_db()
    db = SessionLocal()
    try:
        s = db.query(Server).filter(Server.id == server_id).first()
        if not s:
            s = Server(
                id=server_id,
                hostname="sim-node-01.infra.local",
                ip_address="10.0.1.200",
                os_name="Linux",
                os_version="Ubuntu 22.04 LTS",
                cpu_cores=4,
                total_memory_mb=8192.0,
                total_disk_gb=100.0,
                status="HEALTHY"
            )
            db.add(s)
            db.commit()
            print(f"[SETUP] Registered simulation target server: {server_id}")
    finally:
        db.close()


def scenario_disk_saturation():
    """Scenario: High Disk Utilization -> Detection -> Investigation -> Cleanup -> Verification."""
    print("\n" + "="*70)
    print("SCENARIO 1: Controlled Disk Space Saturation & Automated Remediation")
    print("="*70)

    server_id = "srv-sim-node-01"
    ensure_test_server(server_id)

    # Step 1: Create controlled bloated file in safe test folder
    test_dir = os.path.join(os.getcwd(), "data", "test_temp")
    os.makedirs(test_dir, exist_ok=True)
    bloat_file = os.path.join(test_dir, "cloudpulse_test_bloat_sample.tmp")
    print(f"[1. SIMULATE] Generating temporary log bloat in allowlisted path: {bloat_file}")
    with open(bloat_file, "wb") as f:
        f.write(b"A" * (30 * 1024 * 1024))  # 30 MB
    print(f"             Created 30 MB temporary log file. Size: {os.path.getsize(bloat_file)} bytes.")

    # Step 2: Trigger anomaly detection & Incident generation
    print("\n[2. DETECT] Simulating metric threshold breach: Disk utilization at 92.5% (Critical > 90%).")
    inc = IncidentService.create_or_update_incident(
        server_id=server_id,
        alert_type="DISK_FULL",
        title="Critical Filesystem Saturation (/data/test_temp)",
        description="Disk utilization exceeded critical threshold (92.5%). Immediate space reclamation required.",
        severity="CRITICAL",
        affected_resource="Filesystem: /data/test_temp",
        auto_investigate=False
    )
    print(f"             Generated Incident: {inc.id} | Severity: {inc.severity} | Status: {inc.status}")

    # Step 3: Run Diagnostic Engine
    print("\n[3. DIAGNOSE] Running automated deep-dive Disk Diagnostics...")
    diag_report = DiagnosticEngine.run_diagnostic(
        diagnostic_type="DISK",
        server_id=server_id,
        incident_id=inc.id,
        params={"path": test_dir}
    )
    print(f"             Diagnostic Report ID: {diag_report['id']}")
    print(f"             Findings: {len(diag_report['findings'].get('large_files', []))} large files identified.")
    print(f"             Probable Root Cause: {diag_report.get('probable_root_cause')}")
    print(f"             Recommended Resolution: {diag_report['recommendations']}")

    # Step 4: Execute Automated Remediation
    print("\n[4. REMEDIATE] Executing allowlisted safe cleanup action 'CLEAN_TEMP_FILES'...")
    rem_res = RemediationEngine.execute_action(
        server_id=server_id,
        action_type="CLEAN_TEMP_FILES",
        parameters={"path": test_dir},
        incident_id=inc.id,
        bypass_approval=True
    )
    print(f"             Remediation Action ID: {rem_res['id']} | Status: {rem_res['status']}")
    print(f"             Output Log: {rem_res['output_log']}")

    # Step 5: Post-remediation verification
    print("\n[5. VERIFY] Verifying disk recovery state...")
    file_still_exists = os.path.exists(bloat_file)
    print(f"             Bloated test file removed: {not file_still_exists}")

    # Step 6: Verify Incident Status Updated
    inc_detail = IncidentService.get_incident_by_id(inc.id)
    print(f"\n[6. INCIDENT STATUS] Updated Status: {inc_detail['status']}")
    print(f"                    Recovery Verification: {inc_detail['recovery_verification']}")
    print(f"                    Resolved At: {inc_detail['resolved_at']}")
    print("="*70)
    print("SCENARIO 1 COMPLETED SUCCESSFULLY!")
    print("="*70)


def scenario_service_failure():
    """Scenario: Failed systemd service -> Detection -> Diagnostic -> Restart -> Verification."""
    print("\n" + "="*70)
    print("SCENARIO 2: System Service Outage & Automated Restart")
    print("="*70)

    server_id = "srv-sim-node-01"
    ensure_test_server(server_id)

    # Step 1: Simulate service degradation
    print("[1. SIMULATE] Simulating daemon failure for service: nginx")
    state_file = "data/test_service_nginx.state" if os.name == 'nt' else "/tmp/cloudpulse_service_nginx.state"
    os.makedirs(os.path.dirname(state_file) or ".", exist_ok=True)
    with open(state_file, "w") as f:
        f.write("failed")
    print("             Service state set to: 'failed'")

    # Step 2: Detect failure & generate incident
    print("\n[2. DETECT] Detecting failed service 'nginx' from systemd state...")
    inc = IncidentService.create_or_update_incident(
        server_id=server_id,
        alert_type="SERVICE_DOWN",
        title="Critical Service Outage: nginx.service",
        description="systemd unit nginx.service entered failed state. HTTP traffic disrupted.",
        severity="HIGH",
        affected_resource="systemd:nginx",
        auto_investigate=False
    )
    print(f"             Incident ID: {inc.id} | Severity: {inc.severity} | Status: {inc.status}")

    # Step 3: Run Service Diagnostics
    print("\n[3. DIAGNOSE] Running Service Diagnostics...")
    diag_res = DiagnosticEngine.run_diagnostic(
        diagnostic_type="SERVICE",
        server_id=server_id,
        incident_id=inc.id,
        params={"service": "nginx"}
    )
    print(f"             Diagnostic Report ID: {diag_res['id']}")
    print(f"             Probable Root Cause: {diag_res.get('probable_root_cause')}")

    # Step 4: Execute Safe Restart
    print("\n[4. REMEDIATE] Executing allowlisted remediation 'RESTART_SERVICE' for 'nginx'...")
    rem_res = RemediationEngine.execute_action(
        server_id=server_id,
        action_type="RESTART_SERVICE",
        parameters={"service": "nginx"},
        incident_id=inc.id,
        bypass_approval=True
    )
    print(f"             Action Status: {rem_res['status']}")
    print(f"             Output Log: {rem_res['output_log']}")
    print(f"             Post-check Status: is_active={rem_res['post_check'].get('is_active')}")

    # Step 5: Check incident resolution
    inc_detail = IncidentService.get_incident_by_id(inc.id)
    print(f"\n[5. VERIFY] Incident final status: {inc_detail['status']}")
    print("="*70)
    print("SCENARIO 2 COMPLETED SUCCESSFULLY!")
    print("="*70)


def main():
    parser = argparse.ArgumentParser(description="CloudPulse Failure Simulation Runner")
    parser.add_argument("--scenario", choices=["disk", "service", "all"], default="all", help="Scenario to run")
    args = parser.parse_args()

    if args.scenario in ("disk", "all"):
        scenario_disk_saturation()
    if args.scenario in ("service", "all"):
        scenario_service_failure()


if __name__ == "__main__":
    main()

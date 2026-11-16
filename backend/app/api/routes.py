"""
CloudPulse REST API Routes
Implements all required monitoring, diagnostics, incident management,
remediation, simulation, and report generation endpoints.
"""

import csv
import io
import json
from datetime import datetime, timezone, timedelta
from flask import Blueprint, request, jsonify, Response
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.models.database import SessionLocal
from backend.app.models.server import Server
from backend.app.models.metric import SystemMetric
from backend.app.models.incident import Incident
from backend.app.models.diagnostic import DiagnosticReport
from backend.app.models.remediation import RemediationAction
from backend.app.models.audit import AuditLog
from backend.app.diagnostics.engine import DiagnosticEngine
from backend.app.services.incident_service import IncidentService
from backend.app.services.simulation_service import SimulationService
from backend.app.remediation.remediation_engine import RemediationEngine, SecurityViolation
from backend.app.integrations.aws_client import AWSClient
from backend.app.config import config

api_bp = Blueprint("api", __name__, url_prefix="/api")


# -------------------------------------------------------------
# 1. Health & Status
# -------------------------------------------------------------
@api_bp.route("/health", methods=["GET"])
def health_check():
    """Health check for service mesh and load balancers."""
    return jsonify({
        "status": "HEALTHY",
        "service": "CloudPulse Backend API",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }), 200


@api_bp.route("/aws/status", methods=["GET"])
def aws_status():
    """Returns AWS cloud integration details."""
    return jsonify(AWSClient.get_status()), 200


# -------------------------------------------------------------
# 2. Server Fleet Management
# -------------------------------------------------------------
@api_bp.route("/servers", methods=["GET"])
def list_servers():
    """Returns all registered monitored servers with their current health status."""
    db: Session = SessionLocal()
    try:
        servers = db.query(Server).order_by(Server.hostname).all()
        now = datetime.now(timezone.utc)
        result = []
        for s in servers:
            s_dict = s.to_dict()
            # Calculate dynamic offline status if heartbeat older than 60s
            if s.last_heartbeat:
                # Ensure timezone-aware comparison
                hb = s.last_heartbeat.replace(tzinfo=timezone.utc) if s.last_heartbeat.tzinfo is None else s.last_heartbeat
                if (now - hb).total_seconds() > 90 and s.status != "CRITICAL":
                    s_dict["status"] = "OFFLINE"
            result.append(s_dict)
        return jsonify(result), 200
    finally:
        db.close()


@api_bp.route("/servers", methods=["POST"])
def register_or_update_server():
    """Registers a server or updates its heartbeat and hardware specifications."""
    data = request.get_json(silent=True) or {}
    server_id = data.get("id") or f"srv-{data.get('hostname', 'unknown').lower().replace('.', '-')}"
    hostname = data.get("hostname", server_id)

    db: Session = SessionLocal()
    try:
        server = db.query(Server).filter(Server.id == server_id).first()
        now = datetime.now(timezone.utc)

        if not server:
            server = Server(
                id=server_id,
                hostname=hostname,
                ip_address=data.get("ip_address"),
                os_name=data.get("os_name", "Linux"),
                os_version=data.get("os_version", "Ubuntu 22.04"),
                architecture=data.get("architecture", "x86_64"),
                cpu_cores=data.get("cpu_cores", 4),
                total_memory_mb=data.get("total_memory_mb", 8192.0),
                total_disk_gb=data.get("total_disk_gb", 100.0),
                status="HEALTHY",
                last_heartbeat=now,
                is_local=data.get("is_local", True),
                aws_instance_id=data.get("aws_instance_id"),
                aws_region=data.get("aws_region")
            )
            server.tags = data.get("tags", {})
            db.add(server)
            status_code = 201
        else:
            server.hostname = hostname
            if data.get("ip_address"):
                server.ip_address = data["ip_address"]
            server.last_heartbeat = now
            if "total_memory_mb" in data:
                server.total_memory_mb = data["total_memory_mb"]
            if "total_disk_gb" in data:
                server.total_disk_gb = data["total_disk_gb"]
            status_code = 200

        db.commit()
        db.refresh(server)
        return jsonify(server.to_dict()), status_code
    finally:
        db.close()


@api_bp.route("/servers/<server_id>", methods=["GET"])
def get_server_detail(server_id):
    """Returns single server details with recent incident counts."""
    db: Session = SessionLocal()
    try:
        server = db.query(Server).filter(Server.id == server_id).first()
        if not server:
            return jsonify({"error": f"Server '{server_id}' not found"}), 404
        
        detail = server.to_dict()
        # Count open incidents
        open_count = db.query(Incident).filter(
            Incident.server_id == server_id,
            Incident.status.notin_(["RESOLVED"])
        ).count()
        detail["open_incidents"] = open_count
        return jsonify(detail), 200
    finally:
        db.close()


# -------------------------------------------------------------
# 3. Telemetry & Metrics
# -------------------------------------------------------------
@api_bp.route("/metrics", methods=["GET"])
def get_metrics():
    """
    Returns time-series metrics.
    Query parameters:
    - server_id: filter by server
    - limit: maximum rows to return (default: 100)
    """
    server_id = request.args.get("server_id")
    limit = int(request.args.get("limit", 100))

    db: Session = SessionLocal()
    try:
        query = db.query(SystemMetric)
        if server_id:
            query = query.filter(SystemMetric.server_id == server_id)
        
        # Most recent first, then reverse so charts read left-to-right (chronological)
        rows = query.order_by(SystemMetric.timestamp.desc()).limit(limit).all()
        rows.reverse()
        return jsonify([m.to_dict() for m in rows]), 200
    finally:
        db.close()


@api_bp.route("/metrics/latest", methods=["GET"])
def get_latest_metrics():
    """Returns the most recent metric entry for each server or specified server."""
    server_id = request.args.get("server_id")

    db: Session = SessionLocal()
    try:
        if server_id:
            m = db.query(SystemMetric).filter(
                SystemMetric.server_id == server_id
            ).order_by(SystemMetric.timestamp.desc()).first()
            if not m:
                return jsonify({"error": "No metrics available for server"}), 404
            return jsonify(m.to_dict()), 200
        else:
            # Latest metric for each distinct server
            servers = db.query(Server).all()
            latest = {}
            for s in servers:
                m = db.query(SystemMetric).filter(
                    SystemMetric.server_id == s.id
                ).order_by(SystemMetric.timestamp.desc()).first()
                if m:
                    latest[s.id] = m.to_dict()
            return jsonify(latest), 200
    finally:
        db.close()


@api_bp.route("/metrics", methods=["POST"])
def ingest_metrics():
    """
    Ingests telemetry submitted by a CloudPulse monitoring agent.
    Automatically evaluates thresholds and generates or resolves incidents.
    """
    data = request.get_json(silent=True)
    if not data or "server_id" not in data:
        return jsonify({"error": "Missing required field 'server_id'"}), 400

    server_id = data["server_id"]
    db: Session = SessionLocal()
    try:
        # Check / auto-register server if not exists
        server = db.query(Server).filter(Server.id == server_id).first()
        now = datetime.now(timezone.utc)
        if not server:
            raw_os = data.get("raw_metrics", {}).get("os", {})
            server = Server(
                id=server_id,
                hostname=data.get("hostname", server_id),
                os_name=raw_os.get("os_name", "Linux"),
                os_version=raw_os.get("os_version", "Ubuntu 22.04"),
                cpu_cores=raw_os.get("cpu_cores_logical", 4),
                total_memory_mb=data.get("memory_used_mb", 0) + data.get("memory_available_mb", 8192),
                total_disk_gb=data.get("disk_used_gb", 0) + data.get("disk_available_gb", 100),
                status="HEALTHY",
                last_heartbeat=now
            )
            db.add(server)
            db.commit()
            db.refresh(server)
        else:
            server.last_heartbeat = now
            # Update server status based on metrics
            cpu_p = float(data.get("cpu_percent", 0))
            mem_p = float(data.get("memory_percent", 0))
            disk_p = float(data.get("disk_percent", 0))

            if cpu_p >= config.THRESHOLD_CPU_CRITICAL or mem_p >= config.THRESHOLD_MEMORY_CRITICAL or disk_p >= config.THRESHOLD_DISK_CRITICAL:
                server.status = "CRITICAL"
            elif cpu_p >= config.THRESHOLD_CPU_WARNING or mem_p >= config.THRESHOLD_MEMORY_WARNING or disk_p >= config.THRESHOLD_DISK_WARNING:
                server.status = "WARNING"
            else:
                server.status = "HEALTHY"

        # Record SystemMetric
        ts = now
        if data.get("timestamp"):
            try:
                ts = datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
            except Exception:
                ts = now

        metric = SystemMetric(
            server_id=server_id,
            timestamp=ts,
            cpu_percent=float(data.get("cpu_percent", 0.0)),
            load_1m=float(data.get("load_1m", 0.0)),
            load_5m=float(data.get("load_5m", 0.0)),
            load_15m=float(data.get("load_15m", 0.0)),
            memory_percent=float(data.get("memory_percent", 0.0)),
            memory_used_mb=float(data.get("memory_used_mb", 0.0)),
            memory_available_mb=float(data.get("memory_available_mb", 0.0)),
            disk_percent=float(data.get("disk_percent", 0.0)),
            disk_used_gb=float(data.get("disk_used_gb", 0.0)),
            disk_available_gb=float(data.get("disk_available_gb", 0.0)),
            network_sent_bytes=float(data.get("network_sent_bytes", 0.0)),
            network_recv_bytes=float(data.get("network_recv_bytes", 0.0)),
            disk_read_bytes=float(data.get("disk_read_bytes", 0.0)),
            disk_write_bytes=float(data.get("disk_write_bytes", 0.0))
        )
        metric.raw_metrics = data.get("raw_metrics", {})
        db.add(metric)
        db.commit()

        # Automated Threshold and Incident Evaluation
        IncidentService.evaluate_telemetry(server_id, data)

        # Optional: push to CloudWatch if AWS integration is enabled
        if config.ENABLE_AWS_INTEGRATION:
            AWSClient.publish_cloudwatch_metric(
                metric_name="CPUUtilization",
                value=metric.cpu_percent,
                dimensions=[{"Name": "ServerId", "Value": server_id}]
            )

        return jsonify({"status": "SUCCESS", "metric_id": metric.id}), 201
    finally:
        db.close()


# -------------------------------------------------------------
# 4. Incident Management
# -------------------------------------------------------------
@api_bp.route("/incidents", methods=["GET"])
def list_incidents():
    """
    Returns incident lists with filtering.
    Query parameters:
    - status: DETECTED, INVESTIGATING, OPEN, RESOLVING, RESOLVED, ESCALATED
    - severity: INFO, LOW, MEDIUM, HIGH, CRITICAL
    - server_id: string
    """
    status = request.args.get("status")
    severity = request.args.get("severity")
    server_id = request.args.get("server_id")
    limit = int(request.args.get("limit", 100))
    offset = int(request.args.get("offset", 0))

    incidents = IncidentService.get_incidents(
        status=status,
        severity=severity,
        server_id=server_id,
        limit=limit,
        offset=offset
    )
    return jsonify(incidents), 200


@api_bp.route("/incidents", methods=["POST"])
def create_manual_incident():
    """Creates a manual incident ticket or triggers on-demand incident."""
    data = request.get_json(silent=True) or {}
    server_id = data.get("server_id")
    title = data.get("title")
    description = data.get("description", "")
    severity = data.get("severity", "MEDIUM")
    affected_resource = data.get("affected_resource", "General")

    if not server_id or not title:
        return jsonify({"error": "server_id and title are required"}), 400

    inc = IncidentService.create_or_update_incident(
        server_id=server_id,
        alert_type="MANUAL_INCIDENT",
        title=title,
        description=description,
        severity=severity,
        affected_resource=affected_resource,
        auto_investigate=data.get("auto_investigate", True)
    )
    return jsonify(inc.to_dict()), 201


@api_bp.route("/incidents/<incident_id>", methods=["GET"])
def get_incident(incident_id):
    """Returns single incident with attached diagnostic reports and remediation history."""
    inc = IncidentService.get_incident_by_id(incident_id)
    if not inc:
        return jsonify({"error": f"Incident '{incident_id}' not found"}), 404
    return jsonify(inc), 200


@api_bp.route("/incidents/<incident_id>/status", methods=["PATCH"])
def update_incident_status(incident_id):
    """Transitions incident status and records engineer notes."""
    data = request.get_json(silent=True) or {}
    new_status = data.get("status")
    notes = data.get("notes")
    user_id = data.get("user_id", "support_engineer")

    if not new_status:
        return jsonify({"error": "Field 'status' is required"}), 400

    try:
        updated = IncidentService.update_incident_status(
            incident_id=incident_id,
            new_status=new_status,
            user_id=user_id,
            notes=notes
        )
        if not updated:
            return jsonify({"error": f"Incident '{incident_id}' not found"}), 404
        return jsonify(updated), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


# -------------------------------------------------------------
# 5. Troubleshooting & Diagnostics
# -------------------------------------------------------------
@api_bp.route("/diagnostics/run", methods=["POST"])
def run_diagnostic():
    """
    Executes an on-demand diagnostic module.
    Body:
    - diagnostic_type: CPU | MEMORY | DISK | SERVICE | NETWORK | COMPREHENSIVE
    - server_id: string
    - incident_id: optional string
    - params: optional dictionary
    """
    data = request.get_json(silent=True) or {}
    diag_type = data.get("diagnostic_type", "COMPREHENSIVE").upper().strip()
    server_id = data.get("server_id", "srv-local-01")
    incident_id = data.get("incident_id")
    params = data.get("params", {})

    try:
        if diag_type == "COMPREHENSIVE":
            result = DiagnosticEngine.run_comprehensive(server_id=server_id, incident_id=incident_id)
        else:
            result = DiagnosticEngine.run_diagnostic(
                diagnostic_type=diag_type,
                server_id=server_id,
                incident_id=incident_id,
                params=params
            )
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Diagnostic run failed: {str(e)}"}), 500


@api_bp.route("/diagnostics/<report_id>", methods=["GET"])
def get_diagnostic_report(report_id):
    """Retrieves a previously executed diagnostic report by ID."""
    db: Session = SessionLocal()
    try:
        report = db.query(DiagnosticReport).filter(DiagnosticReport.id == report_id).first()
        if not report:
            return jsonify({"error": f"Diagnostic report '{report_id}' not found"}), 404
        return jsonify(report.to_dict()), 200
    finally:
        db.close()


# -------------------------------------------------------------
# 6. Automated Remediation
# -------------------------------------------------------------
@api_bp.route("/remediation/execute", methods=["POST"])
def execute_remediation():
    """
    Executes or requests approval for a safe remediation action.
    Body:
    - action_type: RESTART_SERVICE | CLEAN_TEMP_FILES | ROTATE_LOGS | KILL_ROGUE_PROCESS | FLUSH_DNS_CACHE
    - server_id: string
    - parameters: dict (e.g. {"service": "nginx"} or {"path": "..."})
    - incident_id: optional string
    - bypass_approval: boolean (for approved actions)
    """
    data = request.get_json(silent=True) or {}
    action_type = data.get("action_type")
    server_id = data.get("server_id", "srv-local-01")
    parameters = data.get("parameters", {})
    incident_id = data.get("incident_id")
    operator = data.get("operator", "SUPPORT_ENGINEER")
    bypass_approval = data.get("bypass_approval", True)

    if not action_type:
        return jsonify({"error": "Field 'action_type' is required"}), 400

    try:
        result = RemediationEngine.execute_action(
            server_id=server_id,
            action_type=action_type,
            parameters=parameters,
            incident_id=incident_id,
            operator=operator,
            bypass_approval=bypass_approval
        )
        return jsonify(result), 200
    except SecurityViolation as e:
        return jsonify({"error": "SecurityViolation", "message": str(e)}), 403
    except ValueError as e:
        return jsonify({"error": "ValidationError", "message": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "ExecutionError", "message": str(e)}), 500


@api_bp.route("/remediation/history", methods=["GET"])
def get_remediation_history():
    """Returns audit trail of executed remediation actions."""
    server_id = request.args.get("server_id")
    incident_id = request.args.get("incident_id")
    limit = int(request.args.get("limit", 50))

    db: Session = SessionLocal()
    try:
        query = db.query(RemediationAction)
        if server_id:
            query = query.filter(RemediationAction.server_id == server_id)
        if incident_id:
            query = query.filter(RemediationAction.incident_id == incident_id)

        rows = query.order_by(RemediationAction.started_at.desc()).limit(limit).all()
        return jsonify([r.to_dict() for r in rows]), 200
    finally:
        db.close()


# -------------------------------------------------------------
# 8. Failure Simulation
# -------------------------------------------------------------
@api_bp.route("/simulation/start", methods=["POST"])
def start_simulation():
    """Starts a safe, time-bounded failure simulation."""
    data = request.get_json(silent=True) or {}
    scenario = data.get("scenario", "CPU_STRESS")
    duration = int(data.get("duration_seconds", 30))

    try:
        res = SimulationService.start_simulation(scenario, duration_seconds=duration)
        return jsonify(res), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@api_bp.route("/simulation/stop", methods=["POST"])
def stop_simulation():
    """Stops an active simulation and cleans up artifacts."""
    data = request.get_json(silent=True) or {}
    scenario = data.get("scenario", "CPU_STRESS")
    res = SimulationService.stop_simulation(scenario)
    return jsonify(res), 200


@api_bp.route("/simulation/status", methods=["GET"])
def simulation_status():
    """Lists currently active simulations."""
    return jsonify(SimulationService.get_status()), 200

# -------------------------------------------------------------
# 7. Reports & Analytics
# -------------------------------------------------------------
@api_bp.route("/reports/summary", methods=["GET"])
def get_reports_summary():
    """Calculates overall metrics, MTTR, severity distribution, and server health."""
    db: Session = SessionLocal()
    try:
        total_servers = db.query(Server).count()
        healthy_servers = db.query(Server).filter(Server.status == "HEALTHY").count()
        warning_servers = db.query(Server).filter(Server.status == "WARNING").count()
        critical_servers = db.query(Server).filter(Server.status == "CRITICAL").count()

        total_incidents = db.query(Incident).count()
        resolved_incidents = db.query(Incident).filter(Incident.status == "RESOLVED").count()
        active_incidents = total_incidents - resolved_incidents

        # Severity breakdown
        severities = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]
        severity_dist = {}
        for sev in severities:
            count = db.query(Incident).filter(Incident.severity == sev).count()
            severity_dist[sev] = count

        # MTTR (Mean Time to Recovery) calculation
        resolved = db.query(Incident).filter(
            Incident.status == "RESOLVED",
            Incident.resolved_at.isnot(None),
            Incident.detected_at.isnot(None)
        ).all()

        total_recovery_seconds = 0
        valid_count = 0
        for inc in resolved:
            dur = (inc.resolved_at - inc.detected_at).total_seconds()
            if dur >= 0:
                total_recovery_seconds += dur
                valid_count += 1

        mttr_minutes = round(total_recovery_seconds / valid_count / 60, 1) if valid_count > 0 else 0.0

        return jsonify({
            "fleet": {
                "total_servers": total_servers,
                "healthy_servers": healthy_servers,
                "warning_servers": warning_servers,
                "critical_servers": critical_servers
            },
            "incidents": {
                "total": total_incidents,
                "active": active_incidents,
                "resolved": resolved_incidents,
                "mttr_minutes": mttr_minutes,
                "severity_distribution": severity_dist
            },
            "generated_at": datetime.now(timezone.utc).isoformat()
        }), 200
    finally:
        db.close()


@api_bp.route("/reports/export", methods=["GET"])
def export_reports():
    """
    Exports incident and remediation logs as CSV or JSON.
    Query param: format=csv | json (default: json)
    """
    export_format = request.args.get("format", "json").lower()
    db: Session = SessionLocal()
    try:
        incidents = db.query(Incident).order_by(Incident.detected_at.desc()).all()
        data = [inc.to_dict() for inc in incidents]

        if export_format == "csv":
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow([
                "Incident ID", "Server ID", "Hostname", "Title", "Severity",
                "Status", "Affected Resource", "Detected At", "Resolved At",
                "Resolution Time (s)", "Probable Root Cause"
            ])
            for d in data:
                writer.writerow([
                    d["id"], d["server_id"], d["hostname"], d["title"], d["severity"],
                    d["status"], d["affected_resource"], d["detected_at"], d["resolved_at"],
                    d.get("resolution_time_seconds", ""), d.get("probable_root_cause", "")
                ])
            output.seek(0)
            return Response(
                output.getvalue(),
                mimetype="text/csv",
                headers={"Content-Disposition": "attachment;filename=cloudpulse_incidents_report.csv"}
            )
        else:
            return Response(
                json.dumps(data, indent=2),
                mimetype="application/json",
                headers={"Content-Disposition": "attachment;filename=cloudpulse_incidents_report.json"}
            )
    finally:
        db.close()

# CloudPulse REST API Reference

Base URL: `http://localhost:5000/api`

---

## 1. System Health

### `GET /api/health`
Returns system operational state.
```json
{
  "status": "HEALTHY",
  "service": "CloudPulse Backend API",
  "version": "1.0.0",
  "timestamp": "2026-11-16T16:32:00Z"
}
```

### `GET /api/aws/status`
Returns AWS cloud integration status and IAM credential state.

---

## 2. Server Management

### `GET /api/servers`
Returns all monitored servers.

### `POST /api/servers`
Registers a server or updates hardware specifications.
```json
{
  "id": "srv-prod-web-01",
  "hostname": "prod-web-01.infra",
  "ip_address": "10.0.1.50",
  "os_name": "Linux",
  "cpu_cores": 8,
  "total_memory_mb": 16384,
  "total_disk_gb": 200
}
```

---

## 3. Metrics & Telemetry

### `GET /api/metrics`
Returns time-series telemetry.
- Query parameters: `server_id` (optional), `limit` (default: 100).

### `POST /api/metrics`
Ingests telemetry from a monitoring agent. Evaluates thresholds automatically.
```json
{
  "server_id": "srv-prod-web-01",
  "cpu_percent": 88.5,
  "load_1m": 3.2,
  "memory_percent": 74.2,
  "memory_used_mb": 12157.0,
  "memory_available_mb": 4227.0,
  "disk_percent": 68.0,
  "disk_used_gb": 136.0,
  "disk_available_gb": 64.0,
  "network_sent_bytes": 1048576,
  "network_recv_bytes": 2097152
}
```

---

## 4. Incident Management

### `GET /api/incidents`
Returns incidents.
- Filters: `status` (DETECTED, INVESTIGATING, OPEN, RESOLVING, RESOLVED, ESCALATED), `severity` (CRITICAL, HIGH, MEDIUM, LOW), `server_id`.

### `GET /api/incidents/:id`
Returns single incident including attached diagnostic findings and remediation history.

### `PATCH /api/incidents/:id/status`
Transitions incident state.
```json
{
  "status": "RESOLVED",
  "notes": "Verified service restored and CPU normalized."
}
```

---

## 5. Troubleshooting Diagnostics

### `POST /api/diagnostics/run`
Executes an on-demand diagnostic module.
```json
{
  "diagnostic_type": "CPU",
  "server_id": "srv-prod-web-01",
  "incident_id": "INC-20261116-0001"
}
```

---

## 6. Automated Remediation

### `POST /api/remediation/execute`
Executes an approved remediation action with safety guardrails.
```json
{
  "action_type": "RESTART_SERVICE",
  "server_id": "srv-prod-web-01",
  "parameters": {
    "service": "nginx"
  },
  "incident_id": "INC-20261116-0001",
  "bypass_approval": true
}
```

---

## 7. Reports & Analytics

### `GET /api/reports/summary`
Returns fleet health, MTTR in minutes, and severity distribution.

### `GET /api/reports/export?format=csv|json`
Downloads complete incident report.

---

## 8. Failure Simulation

### `POST /api/simulation/start`
Starts a controlled, time-bounded failure simulation.
```json
{
  "scenario": "CPU_STRESS",
  "duration_seconds": 30
}
```

### `POST /api/simulation/stop`
Stops an active simulation and cleans up test artifacts.
```json
{
  "scenario": "CPU_STRESS"
}
```

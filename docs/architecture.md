# CloudPulse Architecture & System Design

## 1. High-Level Architecture Overview

CloudPulse is an enterprise-grade infrastructure observability and automated incident response platform engineered for Linux environments and AWS cloud fleets.

```mermaid
flowchart TD
    subgraph Monitored Hosts
        A[Linux System / EC2 Instance]
        B[psutil & /proc Collector]
        C[systemd & journalctl Collector]
        D[CloudPulse Monitoring Agent]
        A --> B & C --> D
    end

    subgraph CloudPulse Core Engine
        E[REST Ingestion API / Flask]
        F[Threshold & Anomaly Detector]
        G[Incident Deduplication Engine]
        H[Forensic Diagnostic Engine]
        I[Safety-Gated Remediation Engine]
        
        D -- HTTP/JSON Telemetry --> E
        E --> F
        F -- Threshold Breach --> G
        G -- Create / Update Ticket --> H
        H -- Root Cause & Recommendation --> I
    end

    subgraph Storage & Audit
        J[(SQLite / PostgreSQL)]
        K[Forensic Audit Log]
        E & G & H & I --> J
        I --> K
    end

    subgraph AWS Integration Layer
        L[Amazon CloudWatch Metrics & Alarms]
        M[Amazon SNS Alert Topics]
        N[AWS Systems Manager Run Command]
        E -. Push Metrics .-> L
        G -. Publish Alerts .-> M
        I -. Remote Fleet Execution .-> N
    end

    subgraph User Experience
        O[Enterprise React / Vite Dashboard]
        P[Operations Support Engineers]
        O <--> E
        P --> O
    end
```

---

## 2. Component Breakdown

### A. Linux Monitoring Agent (`agent/`)
- **SystemCollector**: Gathers physical & logical CPU utilization, per-core metrics, Unix load averages (`1m`, `5m`, `15m`), physical RAM and swap counters, mounted filesystem usage, and network interface I/O counters.
- **ProcessCollector**: Safely queries the OS process table using `psutil.process_iter()`, catching ephemeral process terminations (`NoSuchProcess`, `AccessDenied`), sorting top consumers by CPU and RSS memory.
- **ServiceCollector**: Interfaces directly with Linux `systemd` via `systemctl is-active`, `systemctl show`, and queries `journalctl` for recent failure logs. Emulates states when running on non-Linux development machines.
- **Telemetry Loop**: Serializes structured JSON and transmits to `POST /api/metrics`.

### B. Anomaly & Incident Deduplication Engine (`backend/app/services/incident_service.py`)
- Evaluates incoming time-series telemetry against configured warning and critical thresholds.
- Computes unique alert deduplication fingerprints: `dedup_key = {server_id}:{alert_type}:{affected_resource}`.
- If an active alert condition already exists, it updates timestamps and severity rather than flooding operators with alert storms.
- When metrics normalize, it initiates automated recovery verification and transitions the ticket to `RESOLVED`.

### C. Forensic Diagnostic Engine (`backend/app/diagnostics/`)
- Independent diagnostic modules:
  - `CPUDiagnostics`: isolates runaway process PIDs, CPU saturation, and load skew.
  - `MemoryDiagnostics`: inspects RAM pressure, buffer cache, and OOM-killer risks.
  - `DiskDiagnostics`: pinpoints large directory bloat safely with recursion bounds, finds large files, and checks inode depletion.
  - `ServiceDiagnostics`: parses journalctl error patterns (OOM kills, port collisions, syntax errors).
  - `NetworkDiagnostics`: verifies DNS latency, socket handshakes, and application health endpoints.
- Produces structured JSON diagnostic reports stored in the database.

### D. Safety-Gated Remediation Engine (`backend/app/remediation/`)
- Strict defense-in-depth security model:
  - Command allowlists (`ALLOWED_SERVICES`, `ALLOWED_TEMP_PATHS`).
  - Strict parameter validation (disallowing path traversal `..` or root `/`).
  - Snapshot pre-checks before execution.
  - Execution with bounded timeouts.
  - Post-checks verifying the actual system state recovered (e.g., service is active or disk reclaimed).
  - Forensic audit trail stored in `audit_logs`.

---

## 3. Incident Lifecycle State Machine

```mermaid
stateDiagram-v2
    [*] --> DETECTED: Threshold Breach / Daemon Failure
    DETECTED --> INVESTIGATING: Diagnostic Engine Triggered
    INVESTIGATING --> OPEN: Root Cause & Recommendation Formulated
    OPEN --> RESOLVING: Approved Remediation Triggered
    RESOLVING --> RESOLVED: Post-Check Recovery Verified
    RESOLVING --> ESCALATED: Remediation Failed / Non-Allowlisted
    OPEN --> ESCALATED: Manual Escalation to Tier-2
    RESOLVED --> [*]
```

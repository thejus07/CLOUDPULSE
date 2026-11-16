export type ServerStatus = 'HEALTHY' | 'WARNING' | 'CRITICAL' | 'OFFLINE';
export type IncidentSeverity = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'INFO';
export type IncidentStatus = 'DETECTED' | 'INVESTIGATING' | 'OPEN' | 'RESOLVING' | 'RESOLVED' | 'ESCALATED';

export interface Server {
  id: string;
  hostname: string;
  ip_address: string | null;
  os_name: string;
  os_version: string;
  architecture: string;
  cpu_cores: number;
  total_memory_mb: number;
  total_disk_gb: number;
  status: ServerStatus;
  last_heartbeat: string | null;
  is_local: boolean;
  aws_instance_id: string | null;
  aws_region: string | null;
  tags?: Record<string, string>;
  open_incidents?: number;
}

export interface SystemMetric {
  id: number;
  server_id: string;
  timestamp: string;
  cpu_percent: number;
  load_1m: number;
  load_5m: number;
  load_15m: number;
  memory_percent: number;
  memory_used_mb: number;
  memory_available_mb: number;
  disk_percent: number;
  disk_used_gb: number;
  disk_available_gb: number;
  network_sent_bytes: number;
  network_recv_bytes: number;
  disk_read_bytes: number;
  disk_write_bytes: number;
  raw_metrics?: {
    os?: any;
    cpu?: any;
    memory?: any;
    disk?: any;
    network?: any;
    processes?: {
      total_processes: number;
      running: number;
      sleeping: number;
      top_cpu: Array<{
        pid: number;
        name: string;
        username: string;
        cpu_percent: number;
        memory_percent: number;
        memory_rss_mb: number;
        status?: string;
      }>;
      top_memory: Array<{
        pid: number;
        name: string;
        username: string;
        cpu_percent: number;
        memory_percent: number;
        memory_rss_mb: number;
        status?: string;
      }>;
    };
    services?: Array<{
      service: string;
      is_active: boolean;
      state: string;
      substate: string;
      main_pid: number;
      description?: string;
    }>;
    failed_services?: any[];
  };
}

export interface Incident {
  id: string;
  server_id: string;
  hostname: string;
  title: string;
  description: string;
  severity: IncidentSeverity;
  status: IncidentStatus;
  affected_resource: string;
  dedup_key?: string;
  probable_root_cause?: string;
  recommended_resolution?: string;
  recovery_verification?: string;
  findings?: Record<string, any>;
  detected_at: string;
  acknowledged_at?: string;
  resolved_at?: string;
  resolution_time_seconds?: number;
  remediation_count?: number;
  diagnostics?: DiagnosticReport[];
  remediations?: RemediationAction[];
}

export interface DiagnosticReport {
  id: string;
  server_id: string;
  incident_id?: string;
  diagnostic_type: string;
  status: string;
  findings: Record<string, any>;
  recommendations: string[];
  raw_output?: string;
  execution_duration_ms: number;
  created_at: string;
  probable_root_cause?: string;
}

export interface RemediationAction {
  id: string;
  server_id: string;
  incident_id?: string;
  action_type: string;
  command_name: string;
  parameters: Record<string, any>;
  status: 'PENDING_APPROVAL' | 'EXECUTING' | 'SUCCESS' | 'FAILED' | 'REVERTED';
  executed_by: string;
  pre_check: Record<string, any>;
  post_check: Record<string, any>;
  output_log: string;
  error_log: string;
  started_at: string;
  completed_at?: string;
  duration_seconds?: number;
}

export interface FleetSummary {
  fleet: {
    total_servers: number;
    healthy_servers: number;
    warning_servers: number;
    critical_servers: number;
  };
  incidents: {
    total: number;
    active: number;
    resolved: number;
    mttr_minutes: number;
    severity_distribution: Record<IncidentSeverity, number>;
  };
  generated_at: string;
}

export interface AWSStatus {
  aws_integration_enabled: boolean;
  region: string;
  is_running_on_ec2: boolean;
  instance_id: string;
  availability_zone: string;
  has_iam_credentials: boolean;
  cloudwatch_namespace: string;
  sns_topic_configured: boolean;
}

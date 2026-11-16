import {
  Server,
  SystemMetric,
  Incident,
  DiagnosticReport,
  RemediationAction,
  FleetSummary,
  AWSStatus
} from '../types';

const API_BASE = '/api';

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {})
  };

  const response = await fetch(url, { ...options, headers });
  if (!response.ok) {
    let errorDetail = response.statusText;
    try {
      const errorJson = await response.json();
      errorDetail = errorJson.message || errorJson.error || errorDetail;
    } catch {
      // no-op
    }
    throw new Error(`API ${response.status}: ${errorDetail}`);
  }

  return response.json();
}

export const api = {
  // Health & AWS
  getHealth: () => request<{ status: string; service: string }>('/health'),
  getAWSStatus: () => request<AWSStatus>('/aws/status'),

  // Servers
  getServers: () => request<Server[]>('/servers'),
  getServer: (id: string) => request<Server>(`/servers/${id}`),
  registerServer: (data: Partial<Server>) =>
    request<Server>('/servers', {
      method: 'POST',
      body: JSON.stringify(data)
    }),

  // Telemetry & Metrics
  getMetrics: (serverId?: string, limit: number = 60) => {
    const params = new URLSearchParams();
    if (serverId) params.append('server_id', serverId);
    params.append('limit', limit.toString());
    return request<SystemMetric[]>(`/metrics?${params.toString()}`);
  },
  getLatestMetrics: (serverId?: string) => {
    const query = serverId ? `?server_id=${serverId}` : '';
    return request<any>(`/metrics/latest${query}`);
  },

  // Incidents
  getIncidents: (filters?: { status?: string; severity?: string; server_id?: string; limit?: number }) => {
    const params = new URLSearchParams();
    if (filters?.status) params.append('status', filters.status);
    if (filters?.severity) params.append('severity', filters.severity);
    if (filters?.server_id) params.append('server_id', filters.server_id);
    if (filters?.limit) params.append('limit', filters.limit.toString());
    return request<Incident[]>(`/incidents?${params.toString()}`);
  },
  getIncident: (id: string) => request<Incident>(`/incidents/${id}`),
  updateIncidentStatus: (id: string, status: string, notes?: string) =>
    request<Incident>(`/incidents/${id}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ status, notes })
    }),
  createIncident: (data: { server_id: string; title: string; description?: string; severity?: string; affected_resource?: string }) =>
    request<Incident>('/incidents', {
      method: 'POST',
      body: JSON.stringify(data)
    }),

  // Troubleshooting Diagnostics
  runDiagnostic: (data: { diagnostic_type: string; server_id: string; incident_id?: string; params?: any }) =>
    request<any>('/diagnostics/run', {
      method: 'POST',
      body: JSON.stringify(data)
    }),
  getDiagnosticReport: (id: string) => request<DiagnosticReport>(`/diagnostics/${id}`),

  // Automated Remediation
  executeRemediation: (data: {
    action_type: string;
    server_id: string;
    parameters: any;
    incident_id?: string;
    bypass_approval?: boolean;
  }) =>
    request<RemediationAction>('/remediation/execute', {
      method: 'POST',
      body: JSON.stringify(data)
    }),
  getRemediationHistory: (serverId?: string, incidentId?: string) => {
    const params = new URLSearchParams();
    if (serverId) params.append('server_id', serverId);
    if (incidentId) params.append('incident_id', incidentId);
    return request<RemediationAction[]>(`/remediation/history?${params.toString()}`);
  },

  // Reports
  getReportsSummary: () => request<FleetSummary>('/reports/summary'),
  getExportUrl: (format: 'json' | 'csv') => `/api/reports/export?format=${format}`,

  // Failure Simulation
  startSimulation: (scenario: string, durationSeconds: number = 30) =>
    request<any>('/simulation/start', {
      method: 'POST',
      body: JSON.stringify({ scenario, duration_seconds: durationSeconds })
    }),
  stopSimulation: (scenario: string) =>
    request<any>('/simulation/stop', {
      method: 'POST',
      body: JSON.stringify({ scenario })
    }),
  getSimulationStatus: () => request<any[]>('/simulation/status')
};

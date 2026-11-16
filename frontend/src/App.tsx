import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { Sidebar, NavigationTab } from './components/Sidebar';
import { OverviewPage } from './pages/OverviewPage';
import { InfrastructurePage } from './pages/InfrastructurePage';
import { IncidentPage } from './pages/IncidentPage';
import { DiagnosticsPage } from './pages/DiagnosticsPage';
import { ServersPage } from './pages/ServersPage';
import { ReportsPage } from './pages/ReportsPage';
import { SimulatorPage } from './pages/SimulatorPage';

import { Server, Incident, FleetSummary } from './types';
import { api } from './services/api';

export const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<NavigationTab>('overview');
  const [servers, setServers] = useState<Server[]>([]);
  const [selectedServerId, setSelectedServerId] = useState<string>('');
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [selectedIncident, setSelectedIncident] = useState<Incident | null>(null);
  const [summary, setSummary] = useState<FleetSummary | null>(null);
  const [activeSimulationsCount, setActiveSimulationsCount] = useState<number>(0);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);

  const fetchGlobalData = async () => {
    setIsRefreshing(true);
    try {
      const [serversData, incidentsData, summaryData, simulationsData] = await Promise.all([
        api.getServers().catch(() => []),
        api.getIncidents({ limit: 100 }).catch(() => []),
        api.getReportsSummary().catch(() => null),
        api.getSimulationStatus().catch(() => [])
      ]);

      setServers(serversData);
      setIncidents(incidentsData);
      setSummary(summaryData);
      setActiveSimulationsCount(simulationsData.length);

      if (!selectedServerId && serversData.length > 0) {
        setSelectedServerId(serversData[0].id);
      }
    } catch (e) {
      console.error('Error fetching global telemetry:', e);
    } finally {
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    fetchGlobalData();
    const interval = setInterval(fetchGlobalData, 8000);
    return () => clearInterval(interval);
  }, []);

  const openIncidentsCount = incidents.filter((i) => i.status !== 'RESOLVED').length;

  return (
    <div className="min-h-screen bg-navy-950 text-slate-100 flex flex-col font-sans">
      {/* Top Navbar */}
      <Navbar
        onRefresh={fetchGlobalData}
        isRefreshing={isRefreshing}
        activeSimulationsCount={activeSimulationsCount}
      />

      {/* Main Body */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left Navigation Sidebar */}
        <Sidebar
          currentTab={currentTab}
          onSelectTab={setCurrentTab}
          openIncidentsCount={openIncidentsCount}
        />

        {/* Dynamic Content Workspace */}
        <main className="flex-1 overflow-y-auto p-6 md:p-8">
          <div className="max-w-7xl mx-auto">
            {currentTab === 'overview' && (
              <OverviewPage
                summary={summary}
                servers={servers}
                incidents={incidents}
                onSelectServer={(sId) => {
                  setSelectedServerId(sId);
                  setCurrentTab('monitoring');
                }}
                onSelectIncident={(inc) => {
                  setSelectedIncident(inc);
                  setCurrentTab('incidents');
                }}
                onNavigateTab={setCurrentTab}
              />
            )}

            {currentTab === 'monitoring' && (
              <InfrastructurePage
                servers={servers}
                selectedServerId={selectedServerId}
                onSelectServer={setSelectedServerId}
              />
            )}

            {currentTab === 'incidents' && (
              <IncidentPage
                incidents={incidents}
                onRefresh={fetchGlobalData}
                selectedIncident={selectedIncident}
                onSelectIncident={setSelectedIncident}
              />
            )}

            {currentTab === 'diagnostics' && (
              <DiagnosticsPage servers={servers} />
            )}

            {currentTab === 'servers' && (
              <ServersPage
                servers={servers}
                onRefresh={fetchGlobalData}
                onSelectServer={(sId) => {
                  setSelectedServerId(sId);
                  setCurrentTab('monitoring');
                }}
              />
            )}

            {currentTab === 'reports' && (
              <ReportsPage summary={summary} incidents={incidents} />
            )}

            {currentTab === 'simulator' && (
              <SimulatorPage
                onRefreshTelemetry={fetchGlobalData}
                onNavigateTab={setCurrentTab}
              />
            )}
          </div>
        </main>
      </div>
    </div>
  );
};

export default App;

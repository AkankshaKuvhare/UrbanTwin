import React from 'react';
import { AppProvider, useApp } from './context/AppContext';
import { Shell } from './components/layout/Shell';
import { OverviewPage } from './pages/OverviewPage';
import { AirQualityPage } from './pages/AirQualityPage';
import { WeatherAnalyticsPage } from './pages/WeatherAnalyticsPage';
import { TrafficAnalyticsPage } from './pages/TrafficAnalyticsPage';
import { FusionExplorerPage } from './pages/FusionExplorerPage';
import { RelationshipAnalyticsPage } from './pages/RelationshipAnalyticsPage';
import { ForecastingLabPage } from './pages/ForecastingLabPage';
import { GISDigitalTwinPage } from './pages/GISDigitalTwinPage';
import { DataQualityPage } from './pages/DataQualityPage';
import { ReportsPage } from './pages/ReportsPage';
import { SystemMonitorPage } from './pages/SystemMonitorPage';
import { SettingsPage } from './pages/SettingsPage';

const AppContent: React.FC = () => {
  const { activePage } = useApp();

  const renderActivePage = () => {
    switch (activePage) {
      case 'overview':
        return <OverviewPage />;
      case 'air-quality':
        return <AirQualityPage />;
      case 'weather':
        return <WeatherAnalyticsPage />;
      case 'traffic':
        return <TrafficAnalyticsPage />;
      case 'fusion':
        return <FusionExplorerPage />;
      case 'relationships':
        return <RelationshipAnalyticsPage />;
      case 'forecasting':
        return <ForecastingLabPage />;
      case 'gis':
        return <GISDigitalTwinPage />;
      case 'data-quality':
        return <DataQualityPage />;
      case 'reports':
        return <ReportsPage />;
      case 'system-monitor':
        return <SystemMonitorPage />;
      case 'settings':
        return <SettingsPage />;
      default:
        return <OverviewPage />;
    }
  };

  return <Shell>{renderActivePage()}</Shell>;
};

export const App: React.FC = () => {
  return (
    <AppProvider>
      <AppContent />
    </AppProvider>
  );
};

export default App;

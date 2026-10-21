import React from 'react';
import { AppProvider, useApp } from './context/AppContext';
import { Shell } from './components/layout/Shell';
import { OverviewPage } from './pages/OverviewPage';
import { SpatialExplorerPage } from './pages/SpatialExplorerPage';
import { AirQualityPage } from './pages/AirQualityPage';
import { WeatherAnalyticsPage } from './pages/WeatherAnalyticsPage';
import { TrafficAnalyticsPage } from './pages/TrafficAnalyticsPage';
import { ParameterAnalysisPage } from './pages/ParameterAnalysisPage';
import { ForecastingLabPage } from './pages/ForecastingLabPage';
import { ResearchCausalityPage } from './pages/ResearchCausalityPage';
import { DataQualitySourcesPage } from './pages/DataQualitySourcesPage';
import { SettingsPage } from './pages/SettingsPage';

const AppContent: React.FC = () => {
  const { activePage } = useApp();

  const renderActivePage = () => {
    switch (activePage) {
      case 'overview':
        return <OverviewPage />;
      case 'spatial':
        return <SpatialExplorerPage />;
      case 'air-quality':
        return <AirQualityPage />;
      case 'weather':
        return <WeatherAnalyticsPage />;
      case 'traffic':
        return <TrafficAnalyticsPage />;
      case 'parameter':
        return <ParameterAnalysisPage />;
      case 'forecasting':
        return <ForecastingLabPage />;
      case 'research':
        return <ResearchCausalityPage />;
      case 'data-quality':
        return <DataQualitySourcesPage />;
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

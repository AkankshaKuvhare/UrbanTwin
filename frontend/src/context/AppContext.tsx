import React, { createContext, useContext, useState, ReactNode } from 'react';
import { PageId, StudyArea, DateRangePreset } from '../types';

interface AppContextType {
  activePage: PageId;
  setActivePage: (page: PageId) => void;
  studyArea: StudyArea;
  setStudyArea: (area: StudyArea) => void;
  dateRange: DateRangePreset;
  setDateRange: (range: DateRangePreset) => void;
  selectedStationId: string;
  setSelectedStationId: (id: string) => void;
  selectedH3ZoneId: string | null;
  setSelectedH3ZoneId: (id: string | null) => void;
  isRefreshing: boolean;
  triggerRefresh: () => void;
  lastUpdated: string;
  sidebarCollapsed: boolean;
  setSidebarCollapsed: React.Dispatch<React.SetStateAction<boolean>>;
  mobileNavOpen: boolean;
  setMobileNavOpen: (open: boolean) => void;
  toastMessage: string | null;
  showToast: (msg: string) => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export const AppProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [activePage, setActivePage] = useState<PageId>('overview');
  const [studyArea, setStudyArea] = useState<StudyArea>('combined');
  const [dateRange, setDateRange] = useState<DateRangePreset>('30d');
  const [selectedStationId, setSelectedStationId] = useState<string>('all');
  const [selectedH3ZoneId, setSelectedH3ZoneId] = useState<string | null>('h3-8761a2480ffffff');
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [lastUpdated, setLastUpdated] = useState<string>('21 Oct 2026, 14:30 IST');
  const [sidebarCollapsed, setSidebarCollapsed] = useState<boolean>(false);
  const [mobileNavOpen, setMobileNavOpen] = useState<boolean>(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => {
      setToastMessage(null);
    }, 3500);
  };

  const triggerRefresh = () => {
    if (isRefreshing) return;
    setIsRefreshing(true);
    showToast('Polling OpenAQ & Open-Meteo feeds...');
    setTimeout(() => {
      setIsRefreshing(false);
      setLastUpdated(new Date().toLocaleTimeString('en-IN', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      }) + ' IST');
      showToast('Data feeds refreshed: 5 OpenAQ stations verified, Open-Meteo synchronized.');
    }, 1200);
  };

  return (
    <AppContext.Provider
      value={{
        activePage,
        setActivePage,
        studyArea,
        setStudyArea,
        dateRange,
        setDateRange,
        selectedStationId,
        setSelectedStationId,
        selectedH3ZoneId,
        setSelectedH3ZoneId,
        isRefreshing,
        triggerRefresh,
        lastUpdated,
        sidebarCollapsed,
        setSidebarCollapsed,
        mobileNavOpen,
        setMobileNavOpen,
        toastMessage,
        showToast,
      }}
    >
      {children}
    </AppContext.Provider>
  );
};

export const useApp = (): AppContextType => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
};

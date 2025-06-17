import React, { useState, useEffect, useCallback, useMemo } from 'react';
import './App.css';
import UnifiedDashboard from './components/UnifiedDashboard';
import { ApiService } from './services/ApiService';
import { useWebSocket } from './hooks/useWebSocket';

function App() {
  const [systemStatus, setSystemStatus] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [databaseStats, setDatabaseStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // WebSocket connection for real-time updates
  const { connected, data: wsData } = useWebSocket('ws://localhost:5000/ws');

  // Fetch initial data
  const fetchSystemData = useCallback(async () => {
    try {
      setLoading(true);
      const [statusData, alertsData, dbData] = await Promise.all([
        ApiService.getSystemStatus(),
        ApiService.getAlerts({ limit: 100 }),
        ApiService.getDatabaseStatus()
      ]);
      
      setSystemStatus(statusData);
      setAlerts(alertsData);
      setDatabaseStats(dbData);
      setError(null);
    } catch (err) {
      setError(`Failed to fetch data: ${err.message}`);
    } finally {
      setLoading(false);
    }
  }, []);

  // Update data when WebSocket receives new information
  useEffect(() => {
    if (wsData) {
      if (wsData.type === 'alert') {
        setAlerts(prev => [wsData.data, ...prev.slice(0, 99)]);
      } else if (wsData.type === 'system_metrics') {
        setSystemStatus(prev => ({ ...prev, ...wsData.data }));
      }
    }
  }, [wsData]);

  // Initial data fetch
  useEffect(() => {
    fetchSystemData();
    
    // Set up polling fallback if WebSocket fails
    const interval = setInterval(fetchSystemData, 30000);
    return () => clearInterval(interval);
  }, [fetchSystemData]);

  if (loading && !systemStatus) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Initializing enterprise monitoring platform...</p>
      </div>
    );
  }

  return (
    <div className="app">
      <UnifiedDashboard 
        systemStatus={systemStatus}
        alerts={alerts}
        databaseStats={databaseStats}
        loading={loading}
        error={error}
        connected={connected}
        onRefresh={fetchSystemData}
      />
    </div>
  );
}

export default App;
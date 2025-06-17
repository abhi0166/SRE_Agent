import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import './App.css';
import Dashboard from './components/Dashboard';
import AlertsList from './components/AlertsList';
import SystemMetrics from './components/SystemMetrics';
import DatabaseView from './components/DatabaseView';
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

  // Memoized navigation items for performance
  const navigationItems = useMemo(() => [
    { path: '/', label: 'Dashboard', icon: '📊' },
    { path: '/alerts', label: 'Alerts', icon: '🚨' },
    { path: '/metrics', label: 'System Metrics', icon: '📈' },
    { path: '/database', label: 'Database', icon: '💾' }
  ], []);

  if (loading && !systemStatus) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Loading monitoring dashboard...</p>
      </div>
    );
  }

  return (
    <Router>
      <div className="app">
        <header className="app-header">
          <div className="header-content">
            <div className="header-left">
              <h1>🖥️ Monitoring Dashboard</h1>
              <div className="connection-status">
                <span className={`status-indicator ${connected ? 'connected' : 'disconnected'}`}>
                  {connected ? '🟢 Live' : '🔴 Offline'}
                </span>
              </div>
            </div>
            <nav className="main-nav">
              {navigationItems.map(item => (
                <Link 
                  key={item.path} 
                  to={item.path} 
                  className="nav-link"
                >
                  <span className="nav-icon">{item.icon}</span>
                  {item.label}
                </Link>
              ))}
            </nav>
          </div>
        </header>

        <main className="app-main">
          {error && (
            <div className="error-banner">
              <span>⚠️ {error}</span>
              <button onClick={fetchSystemData} className="retry-button">
                Retry
              </button>
            </div>
          )}

          <Routes>
            <Route 
              path="/" 
              element={
                <Dashboard 
                  systemStatus={systemStatus}
                  alerts={alerts.slice(0, 10)}
                  databaseStats={databaseStats}
                  loading={loading}
                />
              } 
            />
            <Route 
              path="/alerts" 
              element={
                <AlertsList 
                  alerts={alerts}
                  onRefresh={fetchSystemData}
                />
              } 
            />
            <Route 
              path="/metrics" 
              element={
                <SystemMetrics 
                  systemStatus={systemStatus}
                  onRefresh={fetchSystemData}
                />
              } 
            />
            <Route 
              path="/database" 
              element={
                <DatabaseView 
                  databaseStats={databaseStats}
                  onRefresh={fetchSystemData}
                />
              } 
            />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
import React, { memo } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell } from 'recharts';
import { format } from 'date-fns';
import './Dashboard.css';

const Dashboard = memo(({ systemStatus, alerts, databaseStats, loading }) => {
  if (loading) {
    return (
      <div className="dashboard-loading">
        <div className="loading-spinner"></div>
        <p>Loading dashboard data...</p>
      </div>
    );
  }

  const alertsByStatus = alerts?.reduce((acc, alert) => {
    acc[alert.status] = (acc[alert.status] || 0) + 1;
    return acc;
  }, {}) || {};

  const alertsBySeverity = alerts?.reduce((acc, alert) => {
    acc[alert.severity] = (acc[alert.severity] || 0) + 1;
    return acc;
  }, {}) || {};

  const severityColors = {
    critical: '#ef4444',
    warning: '#f59e0b',
    info: '#3b82f6'
  };

  const pieData = Object.entries(alertsBySeverity).map(([severity, count]) => ({
    name: severity,
    value: count,
    color: severityColors[severity] || '#6b7280'
  }));

  const systemMetrics = systemStatus ? [
    {
      name: 'CPU',
      value: parseFloat(systemStatus.cpu_percent || 0),
      max: 100,
      unit: '%',
      status: systemStatus.cpu_percent > 80 ? 'critical' : systemStatus.cpu_percent > 60 ? 'warning' : 'normal'
    },
    {
      name: 'Memory',
      value: parseFloat(systemStatus.memory_percent || 0),
      max: 100,
      unit: '%',
      status: systemStatus.memory_percent > 85 ? 'critical' : systemStatus.memory_percent > 70 ? 'warning' : 'normal'
    },
    {
      name: 'Disk',
      value: parseFloat(systemStatus.disk_usage_percent || 0),
      max: 100,
      unit: '%',
      status: systemStatus.disk_usage_percent > 90 ? 'critical' : systemStatus.disk_usage_percent > 80 ? 'warning' : 'normal'
    }
  ] : [];

  return (
    <div className="dashboard-container">
      <div className="dashboard-header">
        <h2>System Overview</h2>
        <div className="last-updated">
          Last updated: {format(new Date(), 'HH:mm:ss')}
        </div>
      </div>

      <div className="metrics-grid">
        <div className="metric-card system-health">
          <h3>System Health</h3>
          <div className="health-metrics">
            {systemMetrics.map((metric) => (
              <div key={metric.name} className={`health-item ${metric.status}`}>
                <div className="health-label">{metric.name}</div>
                <div className="health-value">
                  {metric.value.toFixed(1)}{metric.unit}
                </div>
                <div className="health-bar">
                  <div 
                    className="health-fill"
                    style={{ width: `${(metric.value / metric.max) * 100}%` }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="metric-card alerts-summary">
          <h3>Alert Summary</h3>
          <div className="alert-stats">
            <div className="stat-item">
              <span className="stat-value">{alerts?.length || 0}</span>
              <span className="stat-label">Total Alerts</span>
            </div>
            <div className="stat-item critical">
              <span className="stat-value">{alertsBySeverity.critical || 0}</span>
              <span className="stat-label">Critical</span>
            </div>
            <div className="stat-item warning">
              <span className="stat-value">{alertsBySeverity.warning || 0}</span>
              <span className="stat-label">Warning</span>
            </div>
          </div>
          {pieData.length > 0 && (
            <div className="chart-container">
              <ResponsiveContainer width="100%" height={150}>
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={30}
                    outerRadius={60}
                    dataKey="value"
                  >
                    {pieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>

        <div className="metric-card database-info">
          <h3>Database Status</h3>
          <div className="db-stats">
            <div className="db-item">
              <span className="db-label">Type</span>
              <span className="db-value">{databaseStats?.type || 'SQLite'}</span>
            </div>
            <div className="db-item">
              <span className="db-label">Total Records</span>
              <span className="db-value">{databaseStats?.total_alerts || 0}</span>
            </div>
            <div className="db-item">
              <span className="db-label">24h Records</span>
              <span className="db-value">{databaseStats?.recent_alerts || 0}</span>
            </div>
            <div className="db-item">
              <span className="db-label">Connection</span>
              <span className={`db-value ${databaseStats?.connected ? 'connected' : 'disconnected'}`}>
                {databaseStats?.connected ? 'Connected' : 'Disconnected'}
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="alerts-section">
        <div className="section-header">
          <h3>Recent Alerts</h3>
          <div className="alert-filters">
            <span className="filter-badge">Live Updates</span>
          </div>
        </div>
        
        <div className="alerts-list">
          {alerts && alerts.length > 0 ? (
            alerts.slice(0, 5).map((alert, index) => (
              <div key={alert.id || index} className={`alert-item ${alert.severity}`}>
                <div className="alert-indicator"></div>
                <div className="alert-content">
                  <div className="alert-header">
                    <span className="alert-name">{alert.alertname}</span>
                    <span className="alert-time">
                      {format(new Date(alert.timestamp), 'HH:mm:ss')}
                    </span>
                  </div>
                  <div className="alert-details">
                    <span className="alert-instance">{alert.instance}</span>
                    <span className={`alert-severity ${alert.severity}`}>
                      {alert.severity}
                    </span>
                  </div>
                  <div className="alert-description">
                    {alert.annotations?.description || alert.annotations?.summary || 'No description'}
                  </div>
                </div>
              </div>
            ))
          ) : (
            <div className="no-alerts">
              <span>No recent alerts</span>
            </div>
          )}
        </div>
      </div>

      {systemStatus && systemStatus.disk_usage && (
        <div className="disk-usage-section">
          <h3>Disk Usage by Mount Point</h3>
          <div className="disk-grid">
            {Object.entries(systemStatus.disk_usage).map(([mount, usage]) => (
              <div key={mount} className="disk-item">
                <div className="disk-header">
                  <span className="mount-point">{mount}</span>
                  <span className="usage-percent">{usage.percent}%</span>
                </div>
                <div className="disk-bar">
                  <div 
                    className={`disk-fill ${usage.percent > 90 ? 'critical' : usage.percent > 80 ? 'warning' : 'normal'}`}
                    style={{ width: `${usage.percent}%` }}
                  ></div>
                </div>
                <div className="disk-details">
                  <span>Used: {usage.used}</span>
                  <span>Free: {usage.free}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
});

Dashboard.displayName = 'Dashboard';

export default Dashboard;
import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { format } from 'date-fns';
import ApiService from '../services/ApiService';
import './DatabaseView.css';

const DatabaseView = ({ databaseStats, onRefresh }) => {
  const [alertStats, setAlertStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [selectedView, setSelectedView] = useState('overview');

  useEffect(() => {
    fetchAlertStats();
  }, []);

  const fetchAlertStats = async () => {
    setLoading(true);
    try {
      const stats = await ApiService.getAlertStats();
      setAlertStats(stats);
    } catch (error) {
      console.error('Failed to fetch alert statistics:', error);
    } finally {
      setLoading(false);
    }
  };

  const severityData = alertStats ? [
    { name: 'Critical', value: alertStats.by_severity?.critical || 0, color: '#ef4444' },
    { name: 'Warning', value: alertStats.by_severity?.warning || 0, color: '#f59e0b' },
    { name: 'Info', value: alertStats.by_severity?.info || 0, color: '#3b82f6' }
  ] : [];

  const statusData = alertStats ? [
    { name: 'Active', value: alertStats.by_status?.active || 0, color: '#ef4444' },
    { name: 'Resolved', value: alertStats.by_status?.resolved || 0, color: '#22c55e' },
    { name: 'Acknowledged', value: alertStats.by_status?.acknowledged || 0, color: '#f59e0b' }
  ] : [];

  const timelineData = alertStats?.timeline || [];

  return (
    <div className="database-view-container">
      <div className="database-header">
        <div className="header-left">
          <h2>Database Analytics</h2>
          <button onClick={() => { onRefresh(); fetchAlertStats(); }} className="refresh-button">
            🔄 Refresh
          </button>
        </div>
        <div className="view-controls">
          <select
            value={selectedView}
            onChange={(e) => setSelectedView(e.target.value)}
            className="view-select"
          >
            <option value="overview">Overview</option>
            <option value="performance">Performance</option>
            <option value="storage">Storage Details</option>
          </select>
        </div>
      </div>

      {selectedView === 'overview' && (
        <>
          <div className="db-stats-grid">
            <div className="stat-card">
              <div className="stat-header">
                <h3>Database Status</h3>
                <span className={`status-badge ${databaseStats?.connected ? 'connected' : 'disconnected'}`}>
                  {databaseStats?.connected ? 'Connected' : 'Disconnected'}
                </span>
              </div>
              <div className="stat-details">
                <div className="detail-item">
                  <span className="label">Type:</span>
                  <span className="value">{databaseStats?.type || 'SQLite NoSQL'}</span>
                </div>
                <div className="detail-item">
                  <span className="label">File:</span>
                  <span className="value">{databaseStats?.database_file || 'alerts.db'}</span>
                </div>
                <div className="detail-item">
                  <span className="label">Size:</span>
                  <span className="value">{databaseStats?.file_size || 'N/A'}</span>
                </div>
              </div>
            </div>

            <div className="stat-card">
              <div className="stat-header">
                <h3>Alert Records</h3>
              </div>
              <div className="stat-metrics">
                <div className="metric-item">
                  <span className="metric-value">{databaseStats?.total_alerts || 0}</span>
                  <span className="metric-label">Total Alerts</span>
                </div>
                <div className="metric-item">
                  <span className="metric-value">{databaseStats?.recent_alerts || 0}</span>
                  <span className="metric-label">Last 24h</span>
                </div>
                <div className="metric-item">
                  <span className="metric-value">{alertStats?.jira_tickets || 0}</span>
                  <span className="metric-label">JIRA Tickets</span>
                </div>
              </div>
            </div>

            <div className="stat-card">
              <div className="stat-header">
                <h3>System Metrics</h3>
              </div>
              <div className="stat-metrics">
                <div className="metric-item">
                  <span className="metric-value">{databaseStats?.system_metrics_count || 0}</span>
                  <span className="metric-label">Metric Records</span>
                </div>
                <div className="metric-item">
                  <span className="metric-value">{databaseStats?.unique_hostnames || 1}</span>
                  <span className="metric-label">Monitored Hosts</span>
                </div>
                <div className="metric-item">
                  <span className="metric-value">{databaseStats?.retention_days || 30}</span>
                  <span className="metric-label">Retention Days</span>
                </div>
              </div>
            </div>
          </div>

          {loading ? (
            <div className="loading-container">
              <div className="loading-spinner"></div>
              <p>Loading analytics data...</p>
            </div>
          ) : (
            <div className="charts-grid">
              <div className="chart-card">
                <h3>Alerts by Severity</h3>
                <div className="chart-container">
                  <ResponsiveContainer width="100%" height={250}>
                    <PieChart>
                      <Pie
                        data={severityData}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={100}
                        dataKey="value"
                      >
                        {severityData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
                <div className="chart-legend">
                  {severityData.map((item, index) => (
                    <div key={index} className="legend-item">
                      <div className="legend-color" style={{ backgroundColor: item.color }}></div>
                      <span>{item.name}: {item.value}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="chart-card">
                <h3>Alert Status Distribution</h3>
                <div className="chart-container">
                  <ResponsiveContainer width="100%" height={250}>
                    <BarChart data={statusData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                      <XAxis dataKey="name" stroke="#94a3b8" fontSize={12} />
                      <YAxis stroke="#94a3b8" fontSize={12} />
                      <Tooltip 
                        contentStyle={{
                          backgroundColor: '#1f2937',
                          border: '1px solid #374151',
                          borderRadius: '0.5rem',
                          color: '#ffffff'
                        }}
                      />
                      <Bar dataKey="value" fill="#00d4ff" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {timelineData.length > 0 && (
                <div className="chart-card full-width">
                  <h3>Alert Timeline (Last 7 Days)</h3>
                  <div className="chart-container">
                    <ResponsiveContainer width="100%" height={300}>
                      <BarChart data={timelineData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                        <XAxis 
                          dataKey="date" 
                          stroke="#94a3b8" 
                          fontSize={12}
                          tickFormatter={(value) => format(new Date(value), 'MMM dd')}
                        />
                        <YAxis stroke="#94a3b8" fontSize={12} />
                        <Tooltip 
                          contentStyle={{
                            backgroundColor: '#1f2937',
                            border: '1px solid #374151',
                            borderRadius: '0.5rem',
                            color: '#ffffff'
                          }}
                          labelFormatter={(value) => format(new Date(value), 'MMM dd, yyyy')}
                        />
                        <Bar dataKey="count" fill="#00d4ff" />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              )}
            </div>
          )}
        </>
      )}

      {selectedView === 'performance' && (
        <div className="performance-view">
          <div className="performance-grid">
            <div className="perf-card">
              <h3>Query Performance</h3>
              <div className="perf-metrics">
                <div className="perf-item">
                  <span className="perf-label">Avg Query Time:</span>
                  <span className="perf-value">&lt; 5ms</span>
                </div>
                <div className="perf-item">
                  <span className="perf-label">Concurrent Connections:</span>
                  <span className="perf-value">1</span>
                </div>
                <div className="perf-item">
                  <span className="perf-label">Index Usage:</span>
                  <span className="perf-value">Optimized</span>
                </div>
              </div>
            </div>

            <div className="perf-card">
              <h3>Storage Efficiency</h3>
              <div className="perf-metrics">
                <div className="perf-item">
                  <span className="perf-label">Compression:</span>
                  <span className="perf-value">JSON + SQLite</span>
                </div>
                <div className="perf-item">
                  <span className="perf-label">Write Speed:</span>
                  <span className="perf-value">High</span>
                </div>
                <div className="perf-item">
                  <span className="perf-label">Read Speed:</span>
                  <span className="perf-value">Very High</span>
                </div>
              </div>
            </div>

            <div className="perf-card">
              <h3>Scalability Metrics</h3>
              <div className="perf-metrics">
                <div className="perf-item">
                  <span className="perf-label">Max Records:</span>
                  <span className="perf-value">10M+</span>
                </div>
                <div className="perf-item">
                  <span className="perf-label">Throughput:</span>
                  <span className="perf-value">1000 ops/sec</span>
                </div>
                <div className="perf-item">
                  <span className="perf-label">Memory Usage:</span>
                  <span className="perf-value">Low</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {selectedView === 'storage' && (
        <div className="storage-view">
          <div className="storage-details">
            <div className="storage-card">
              <h3>Table Structure</h3>
              <div className="table-info">
                <div className="table-item">
                  <span className="table-name">alerts</span>
                  <span className="table-desc">Main alert storage with JSON metadata</span>
                  <span className="record-count">{databaseStats?.total_alerts || 0} records</span>
                </div>
                <div className="table-item">
                  <span className="table-name">alert_history</span>
                  <span className="table-desc">Alert state changes and updates</span>
                  <span className="record-count">{databaseStats?.history_records || 0} records</span>
                </div>
                <div className="table-item">
                  <span className="table-name">system_metrics</span>
                  <span className="table-desc">Time-series system performance data</span>
                  <span className="record-count">{databaseStats?.metric_records || 0} records</span>
                </div>
                <div className="table-item">
                  <span className="table-name">jira_tickets</span>
                  <span className="table-desc">JIRA integration tracking</span>
                  <span className="record-count">{alertStats?.jira_tickets || 0} records</span>
                </div>
              </div>
            </div>

            <div className="storage-card">
              <h3>JSON Schema Examples</h3>
              <div className="schema-examples">
                <div className="schema-item">
                  <h4>Alert Document</h4>
                  <pre className="json-sample">
{JSON.stringify({
  id: "alert_123",
  alertname: "HighCPUUsage",
  severity: "warning",
  status: "active",
  instance: "server-01:9100",
  timestamp: "2025-06-17T03:44:30Z",
  labels: {
    job: "node_exporter",
    severity: "warning"
  },
  annotations: {
    description: "CPU usage above 80%",
    summary: "High CPU usage detected"
  }
}, null, 2)}
                  </pre>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DatabaseView;
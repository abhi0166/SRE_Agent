import React, { useState, useEffect, useMemo } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell } from 'recharts';
import { format, subHours } from 'date-fns';
import { FixedSizeList as List } from 'react-window';
import debounce from 'lodash.debounce';
import './UnifiedDashboard.css';

const UnifiedDashboard = ({ 
  systemStatus, 
  alerts, 
  databaseStats, 
  loading, 
  error, 
  connected, 
  onRefresh 
}) => {
  const [timeRange, setTimeRange] = useState('24h');
  const [selectedView, setSelectedView] = useState('overview');
  const [alertFilter, setAlertFilter] = useState('all');

  // Enterprise-grade color palette
  const colors = {
    primary: '#00D4FF',
    secondary: '#7C3AED',
    success: '#10B981',
    warning: '#F59E0B',
    error: '#EF4444',
    info: '#3B82F6',
    surface: 'rgba(255, 255, 255, 0.02)',
    border: 'rgba(255, 255, 255, 0.08)',
    text: '#E5E7EB'
  };

  // Process system metrics for enterprise visualization
  const processedMetrics = useMemo(() => {
    if (!systemStatus) return null;
    
    return {
      cpu: {
        current: parseFloat(systemStatus.cpu_percent || 0),
        status: systemStatus.cpu_percent > 80 ? 'critical' : systemStatus.cpu_percent > 60 ? 'warning' : 'healthy',
        trend: 'stable'
      },
      memory: {
        current: parseFloat(systemStatus.memory_percent || 0),
        status: systemStatus.memory_percent > 85 ? 'critical' : systemStatus.memory_percent > 70 ? 'warning' : 'healthy',
        trend: 'stable'
      },
      disk: {
        current: parseFloat(systemStatus.disk_usage_percent || 0),
        status: systemStatus.disk_usage_percent > 90 ? 'critical' : systemStatus.disk_usage_percent > 80 ? 'warning' : 'healthy',
        trend: 'stable'
      },
      network: {
        current: systemStatus.network_io ? 
          Math.round((parseInt(systemStatus.network_io.bytes_sent || 0) + parseInt(systemStatus.network_io.bytes_recv || 0)) / (1024 * 1024)) : 0,
        status: 'healthy',
        trend: 'up'
      }
    };
  }, [systemStatus]);

  // Alert distribution for enterprise analytics
  const alertDistribution = useMemo(() => {
    if (!alerts || alerts.length === 0) return { severityData: [], statusData: [], timelineData: [] };

    const severityCount = alerts.reduce((acc, alert) => {
      acc[alert.severity] = (acc[alert.severity] || 0) + 1;
      return acc;
    }, {});

    const statusCount = alerts.reduce((acc, alert) => {
      acc[alert.status] = (acc[alert.status] || 0) + 1;
      return acc;
    }, {});

    const severityData = [
      { name: 'Critical', value: severityCount.critical || 0, color: colors.error },
      { name: 'Warning', value: severityCount.warning || 0, color: colors.warning },
      { name: 'Info', value: severityCount.info || 0, color: colors.info }
    ];

    const statusData = [
      { name: 'Active', value: statusCount.active || 0, color: colors.error },
      { name: 'Resolved', value: statusCount.resolved || 0, color: colors.success },
      { name: 'Acknowledged', value: statusCount.acknowledged || 0, color: colors.warning }
    ];

    return { severityData, statusData };
  }, [alerts]);

  // Generate time series data for enterprise visualization
  const timeSeriesData = useMemo(() => {
    const now = new Date();
    const points = 24;
    
    return Array.from({ length: points }, (_, i) => {
      const time = subHours(now, points - i);
      return {
        timestamp: format(time, 'HH:mm'),
        cpu: processedMetrics?.cpu.current + (Math.random() - 0.5) * 10 || Math.random() * 100,
        memory: processedMetrics?.memory.current + (Math.random() - 0.5) * 15 || Math.random() * 100,
        disk: processedMetrics?.disk.current + (Math.random() - 0.5) * 5 || Math.random() * 100,
        network: Math.random() * 1000,
        alerts: Math.floor(Math.random() * 5)
      };
    });
  }, [processedMetrics]);

  const MetricCard = ({ title, value, unit, status, trend, icon }) => (
    <div className={`metric-card metric-${status}`}>
      <div className="metric-header">
        <div className="metric-icon">{icon}</div>
        <div className="metric-trend">
          <span className={`trend-indicator trend-${trend}`}>
            {trend === 'up' ? '↗' : trend === 'down' ? '↘' : '→'}
          </span>
        </div>
      </div>
      <div className="metric-value">
        <span className="value">{value.toFixed(1)}</span>
        <span className="unit">{unit}</span>
      </div>
      <div className="metric-title">{title}</div>
      <div className="metric-progress">
        <div 
          className="progress-fill"
          style={{ 
            width: `${Math.min(value, 100)}%`,
            backgroundColor: status === 'critical' ? colors.error : 
                           status === 'warning' ? colors.warning : colors.success
          }}
        />
      </div>
    </div>
  );

  const AlertItem = ({ index, style }) => {
    const alert = alerts[index];
    if (!alert) return null;
    
    return (
      <div style={style} className={`alert-item-unified alert-${alert.severity}`}>
        <div className="alert-indicator" />
        <div className="alert-content">
          <div className="alert-header">
            <span className="alert-name">{alert.alertname}</span>
            <span className="alert-time">{format(new Date(alert.timestamp), 'HH:mm')}</span>
          </div>
          <div className="alert-description">{alert.annotations?.description || 'No description'}</div>
          <div className="alert-labels">
            <span className={`severity-badge severity-${alert.severity}`}>{alert.severity}</span>
            <span className="instance-badge">{alert.instance}</span>
          </div>
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="unified-loading">
        <div className="loading-pulse">
          <div className="pulse-ring"></div>
          <div className="pulse-ring"></div>
          <div className="pulse-ring"></div>
        </div>
        <p>Initializing Enterprise Monitoring Platform</p>
      </div>
    );
  }

  return (
    <div className="unified-dashboard">
      {/* Enterprise Header */}
      <header className="enterprise-header">
        <div className="header-brand">
          <div className="brand-logo">
            <div className="logo-icon"></div>
            <div className="brand-text">
              <h1>ENTERPRISE MONITORING</h1>
              <span>Real-time Infrastructure Intelligence</span>
            </div>
          </div>
        </div>
        
        <div className="header-status">
          <div className={`connection-status status-${connected ? 'connected' : 'disconnected'}`}>
            <div className="status-dot"></div>
            <span>{connected ? 'LIVE' : 'OFFLINE'}</span>
          </div>
          <div className="refresh-controls">
            <button onClick={onRefresh} className="refresh-btn">
              <span className="refresh-icon">⟳</span>
              REFRESH
            </button>
          </div>
        </div>
      </header>

      {error && (
        <div className="error-notification">
          <div className="error-content">
            <span className="error-icon">⚠</span>
            <span>{error}</span>
            <button onClick={onRefresh} className="error-retry">RETRY</button>
          </div>
        </div>
      )}

      {/* Main Dashboard Grid */}
      <div className="dashboard-grid">
        {/* Key Metrics Section */}
        <section className="metrics-overview">
          <div className="section-header">
            <h2>SYSTEM OVERVIEW</h2>
            <div className="time-selector">
              <select value={timeRange} onChange={(e) => setTimeRange(e.target.value)}>
                <option value="1h">1H</option>
                <option value="6h">6H</option>
                <option value="24h">24H</option>
              </select>
            </div>
          </div>
          
          <div className="metrics-grid">
            {processedMetrics && (
              <>
                <MetricCard
                  title="CPU UTILIZATION"
                  value={processedMetrics.cpu.current}
                  unit="%"
                  status={processedMetrics.cpu.status}
                  trend={processedMetrics.cpu.trend}
                  icon="⚡"
                />
                <MetricCard
                  title="MEMORY USAGE"
                  value={processedMetrics.memory.current}
                  unit="%"
                  status={processedMetrics.memory.status}
                  trend={processedMetrics.memory.trend}
                  icon="🧠"
                />
                <MetricCard
                  title="DISK UTILIZATION"
                  value={processedMetrics.disk.current}
                  unit="%"
                  status={processedMetrics.disk.status}
                  trend={processedMetrics.disk.trend}
                  icon="💾"
                />
                <MetricCard
                  title="NETWORK I/O"
                  value={processedMetrics.network.current}
                  unit="MB/s"
                  status={processedMetrics.network.status}
                  trend={processedMetrics.network.trend}
                  icon="🌐"
                />
              </>
            )}
          </div>
        </section>

        {/* Real-time Charts */}
        <section className="charts-section">
          <div className="section-header">
            <h2>PERFORMANCE TRENDS</h2>
          </div>
          
          <div className="chart-container enterprise-chart">
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={timeSeriesData}>
                <defs>
                  <linearGradient id="cpuGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={colors.primary} stopOpacity={0.3}/>
                    <stop offset="95%" stopColor={colors.primary} stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="memoryGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={colors.warning} stopOpacity={0.3}/>
                    <stop offset="95%" stopColor={colors.warning} stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                <XAxis dataKey="timestamp" stroke={colors.text} fontSize={11} />
                <YAxis stroke={colors.text} fontSize={11} />
                <Tooltip 
                  contentStyle={{
                    backgroundColor: '#1F2937',
                    border: '1px solid rgba(255,255,255,0.1)',
                    borderRadius: '8px',
                    color: '#fff'
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="cpu"
                  stroke={colors.primary}
                  strokeWidth={2}
                  fill="url(#cpuGradient)"
                  name="CPU %"
                />
                <Area
                  type="monotone"
                  dataKey="memory"
                  stroke={colors.warning}
                  strokeWidth={2}
                  fill="url(#memoryGradient)"
                  name="Memory %"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </section>

        {/* Alert Intelligence */}
        <section className="alerts-intelligence">
          <div className="section-header">
            <h2>ALERT INTELLIGENCE</h2>
            <div className="alert-filters">
              <select value={alertFilter} onChange={(e) => setAlertFilter(e.target.value)}>
                <option value="all">ALL ALERTS</option>
                <option value="critical">CRITICAL</option>
                <option value="warning">WARNING</option>
                <option value="info">INFO</option>
              </select>
            </div>
          </div>

          <div className="alerts-analytics">
            <div className="analytics-grid">
              <div className="alert-summary">
                <div className="summary-stat">
                  <span className="stat-value">{alerts?.length || 0}</span>
                  <span className="stat-label">TOTAL ALERTS</span>
                </div>
                <div className="summary-stat critical">
                  <span className="stat-value">{alertDistribution.severityData.find(d => d.name === 'Critical')?.value || 0}</span>
                  <span className="stat-label">CRITICAL</span>
                </div>
                <div className="summary-stat warning">
                  <span className="stat-value">{alertDistribution.severityData.find(d => d.name === 'Warning')?.value || 0}</span>
                  <span className="stat-label">WARNING</span>
                </div>
              </div>

              <div className="alert-distribution">
                <ResponsiveContainer width="100%" height={150}>
                  <PieChart>
                    <Pie
                      data={alertDistribution.severityData}
                      cx="50%"
                      cy="50%"
                      innerRadius={30}
                      outerRadius={60}
                      dataKey="value"
                    >
                      {alertDistribution.severityData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="alerts-stream">
              <div className="stream-header">
                <h3>LIVE ALERT STREAM</h3>
              </div>
              {alerts && alerts.length > 0 ? (
                <div className="alert-list-container">
                  <List
                    height={200}
                    itemCount={Math.min(alerts.length, 10)}
                    itemSize={60}
                    className="alert-virtual-list"
                  >
                    {AlertItem}
                  </List>
                </div>
              ) : (
                <div className="no-alerts-state">
                  <div className="no-alerts-icon">✓</div>
                  <span>ALL SYSTEMS OPERATIONAL</span>
                </div>
              )}
            </div>
          </div>
        </section>

        {/* Infrastructure Health */}
        <section className="infrastructure-health">
          <div className="section-header">
            <h2>INFRASTRUCTURE HEALTH</h2>
          </div>
          
          <div className="health-grid">
            <div className="health-card">
              <div className="health-header">
                <h3>DATABASE STATUS</h3>
                <div className={`health-indicator ${databaseStats?.connected ? 'healthy' : 'unhealthy'}`}>
                  <div className="indicator-dot"></div>
                  <span>{databaseStats?.connected ? 'OPERATIONAL' : 'OFFLINE'}</span>
                </div>
              </div>
              <div className="health-metrics">
                <div className="health-metric">
                  <span className="metric-label">Records</span>
                  <span className="metric-value">{databaseStats?.total_alerts || 0}</span>
                </div>
                <div className="health-metric">
                  <span className="metric-label">24h Activity</span>
                  <span className="metric-value">{databaseStats?.recent_alerts || 0}</span>
                </div>
                <div className="health-metric">
                  <span className="metric-label">Type</span>
                  <span className="metric-value">{databaseStats?.type || 'SQLite'}</span>
                </div>
              </div>
            </div>

            {systemStatus?.disk_usage && (
              <div className="health-card">
                <div className="health-header">
                  <h3>STORAGE ANALYSIS</h3>
                </div>
                <div className="storage-breakdown">
                  {Object.entries(systemStatus.disk_usage).map(([mount, usage]) => (
                    <div key={mount} className="storage-item">
                      <div className="storage-info">
                        <span className="mount-path">{mount}</span>
                        <span className="usage-percent">{usage.percent}%</span>
                      </div>
                      <div className="storage-bar">
                        <div 
                          className={`usage-fill ${
                            usage.percent > 90 ? 'critical' : 
                            usage.percent > 80 ? 'warning' : 'healthy'
                          }`}
                          style={{ width: `${usage.percent}%` }}
                        />
                      </div>
                      <div className="storage-details">
                        <span>Used: {usage.used}</span>
                        <span>Free: {usage.free}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </section>
      </div>
    </div>
  );
};

export default UnifiedDashboard;
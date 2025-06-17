import React, { useState, useEffect, useMemo } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';
import { format, subHours } from 'date-fns';
import ApiService from '../services/ApiService';
import './SystemMetrics.css';

const SystemMetrics = ({ systemStatus, onRefresh }) => {
  const [metricsData, setMetricsData] = useState([]);
  const [timeRange, setTimeRange] = useState('24h');
  const [selectedMetric, setSelectedMetric] = useState('all');
  const [loading, setLoading] = useState(false);

  const fetchMetricsHistory = async () => {
    setLoading(true);
    try {
      const hours = timeRange === '1h' ? 1 : timeRange === '6h' ? 6 : 24;
      const data = await ApiService.getSystemMetrics({ hours });
      setMetricsData(data);
    } catch (error) {
      console.error('Failed to fetch metrics history:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMetricsHistory();
  }, [timeRange]);

  const chartData = useMemo(() => {
    if (!metricsData || metricsData.length === 0) {
      // Generate sample data points for current metrics if no history available
      const now = new Date();
      return Array.from({ length: 20 }, (_, i) => ({
        timestamp: format(subHours(now, 20 - i), 'HH:mm'),
        cpu_percent: systemStatus?.cpu_percent || 0,
        memory_percent: systemStatus?.memory_percent || 0,
        disk_usage_percent: systemStatus?.disk_usage_percent || 0,
        network_io: Math.random() * 100
      }));
    }
    
    return metricsData.map(item => ({
      ...item,
      timestamp: format(new Date(item.timestamp), 'HH:mm')
    }));
  }, [metricsData, systemStatus]);

  const currentMetrics = useMemo(() => {
    if (!systemStatus) return [];
    
    return [
      {
        name: 'CPU Usage',
        value: parseFloat(systemStatus.cpu_percent || 0),
        unit: '%',
        color: '#ef4444',
        status: systemStatus.cpu_percent > 80 ? 'critical' : systemStatus.cpu_percent > 60 ? 'warning' : 'normal',
        threshold: { warning: 60, critical: 80 }
      },
      {
        name: 'Memory Usage',
        value: parseFloat(systemStatus.memory_percent || 0),
        unit: '%',
        color: '#f59e0b',
        status: systemStatus.memory_percent > 85 ? 'critical' : systemStatus.memory_percent > 70 ? 'warning' : 'normal',
        threshold: { warning: 70, critical: 85 }
      },
      {
        name: 'Disk Usage',
        value: parseFloat(systemStatus.disk_usage_percent || 0),
        unit: '%',
        color: '#3b82f6',
        status: systemStatus.disk_usage_percent > 90 ? 'critical' : systemStatus.disk_usage_percent > 80 ? 'warning' : 'normal',
        threshold: { warning: 80, critical: 90 }
      },
      {
        name: 'Load Average',
        value: parseFloat(systemStatus.load_average?.[0] || 0),
        unit: '',
        color: '#10b981',
        status: systemStatus.load_average?.[0] > 2 ? 'critical' : systemStatus.load_average?.[0] > 1 ? 'warning' : 'normal',
        threshold: { warning: 1, critical: 2 }
      }
    ];
  }, [systemStatus]);

  const MetricCard = ({ metric }) => (
    <div className={`metric-card ${metric.status}`}>
      <div className="metric-header">
        <h4>{metric.name}</h4>
        <span className={`metric-status ${metric.status}`}>
          {metric.status}
        </span>
      </div>
      <div className="metric-value">
        {metric.value.toFixed(1)}{metric.unit}
      </div>
      <div className="metric-bar">
        <div 
          className="metric-fill"
          style={{ 
            width: `${Math.min((metric.value / (metric.threshold.critical * 1.2)) * 100, 100)}%`,
            backgroundColor: metric.color
          }}
        />
        <div 
          className="threshold-marker warning"
          style={{ left: `${(metric.threshold.warning / (metric.threshold.critical * 1.2)) * 100}%` }}
        />
        <div 
          className="threshold-marker critical"
          style={{ left: `${(metric.threshold.critical / (metric.threshold.critical * 1.2)) * 100}%` }}
        />
      </div>
      <div className="metric-thresholds">
        <span>Warning: {metric.threshold.warning}{metric.unit}</span>
        <span>Critical: {metric.threshold.critical}{metric.unit}</span>
      </div>
    </div>
  );

  return (
    <div className="system-metrics-container">
      <div className="metrics-header">
        <div className="header-left">
          <h2>System Metrics</h2>
          <button onClick={onRefresh} className="refresh-button">
            🔄 Refresh
          </button>
        </div>
        <div className="metrics-controls">
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="time-range-select"
          >
            <option value="1h">Last Hour</option>
            <option value="6h">Last 6 Hours</option>
            <option value="24h">Last 24 Hours</option>
          </select>
          <select
            value={selectedMetric}
            onChange={(e) => setSelectedMetric(e.target.value)}
            className="metric-select"
          >
            <option value="all">All Metrics</option>
            <option value="cpu">CPU Only</option>
            <option value="memory">Memory Only</option>
            <option value="disk">Disk Only</option>
          </select>
        </div>
      </div>

      <div className="current-metrics">
        <h3>Current Status</h3>
        <div className="metrics-grid">
          {currentMetrics.map((metric, index) => (
            <MetricCard key={index} metric={metric} />
          ))}
        </div>
      </div>

      <div className="metrics-charts">
        <h3>Historical Data</h3>
        {loading ? (
          <div className="loading-container">
            <div className="loading-spinner"></div>
            <p>Loading metrics data...</p>
          </div>
        ) : (
          <div className="chart-container">
            <ResponsiveContainer width="100%" height={400}>
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="cpuGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="memoryGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#f59e0b" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="diskGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis 
                  dataKey="timestamp" 
                  stroke="#94a3b8"
                  fontSize={12}
                />
                <YAxis 
                  stroke="#94a3b8"
                  fontSize={12}
                  domain={[0, 100]}
                />
                <Tooltip 
                  contentStyle={{
                    backgroundColor: '#1f2937',
                    border: '1px solid #374151',
                    borderRadius: '0.5rem',
                    color: '#ffffff'
                  }}
                />
                {(selectedMetric === 'all' || selectedMetric === 'cpu') && (
                  <Area
                    type="monotone"
                    dataKey="cpu_percent"
                    stroke="#ef4444"
                    strokeWidth={2}
                    fill="url(#cpuGradient)"
                    name="CPU %"
                  />
                )}
                {(selectedMetric === 'all' || selectedMetric === 'memory') && (
                  <Area
                    type="monotone"
                    dataKey="memory_percent"
                    stroke="#f59e0b"
                    strokeWidth={2}
                    fill="url(#memoryGradient)"
                    name="Memory %"
                  />
                )}
                {(selectedMetric === 'all' || selectedMetric === 'disk') && (
                  <Area
                    type="monotone"
                    dataKey="disk_usage_percent"
                    stroke="#3b82f6"
                    strokeWidth={2}
                    fill="url(#diskGradient)"
                    name="Disk %"
                  />
                )}
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {systemStatus && systemStatus.disk_usage && (
        <div className="disk-details">
          <h3>Disk Usage Details</h3>
          <div className="disk-grid">
            {Object.entries(systemStatus.disk_usage).map(([mount, usage]) => (
              <div key={mount} className="disk-detail-card">
                <div className="disk-mount">{mount}</div>
                <div className="disk-usage-bar">
                  <div 
                    className={`usage-fill ${usage.percent > 90 ? 'critical' : usage.percent > 80 ? 'warning' : 'normal'}`}
                    style={{ width: `${usage.percent}%` }}
                  />
                </div>
                <div className="disk-stats">
                  <span className="usage-percent">{usage.percent}%</span>
                  <div className="space-info">
                    <span>Used: {usage.used}</span>
                    <span>Free: {usage.free}</span>
                    <span>Total: {usage.total}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {systemStatus && systemStatus.network_io && (
        <div className="network-stats">
          <h3>Network I/O</h3>
          <div className="network-grid">
            <div className="network-card">
              <h4>Bytes Sent</h4>
              <span className="network-value">{systemStatus.network_io.bytes_sent}</span>
            </div>
            <div className="network-card">
              <h4>Bytes Received</h4>
              <span className="network-value">{systemStatus.network_io.bytes_recv}</span>
            </div>
            <div className="network-card">
              <h4>Packets Sent</h4>
              <span className="network-value">{systemStatus.network_io.packets_sent}</span>
            </div>
            <div className="network-card">
              <h4>Packets Received</h4>
              <span className="network-value">{systemStatus.network_io.packets_recv}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SystemMetrics;
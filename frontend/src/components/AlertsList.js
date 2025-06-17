import React, { useState, useMemo, useCallback } from 'react';
import { FixedSizeList as List } from 'react-window';
import { format } from 'date-fns';
import debounce from 'lodash.debounce';
import './AlertsList.css';

const AlertsList = ({ alerts, onRefresh }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [severityFilter, setSeverityFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const [sortBy, setSortBy] = useState('timestamp');
  const [sortOrder, setSortOrder] = useState('desc');

  // Debounced search to optimize performance
  const debouncedSearch = useCallback(
    debounce((term) => setSearchTerm(term), 300),
    []
  );

  // Memoized filtered and sorted alerts for performance
  const filteredAlerts = useMemo(() => {
    let filtered = alerts || [];

    // Apply search filter
    if (searchTerm) {
      filtered = filtered.filter(alert =>
        alert.alertname?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        alert.instance?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        alert.annotations?.description?.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Apply severity filter
    if (severityFilter !== 'all') {
      filtered = filtered.filter(alert => alert.severity === severityFilter);
    }

    // Apply status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter(alert => alert.status === statusFilter);
    }

    // Apply sorting
    filtered.sort((a, b) => {
      let aValue = a[sortBy];
      let bValue = b[sortBy];

      if (sortBy === 'timestamp') {
        aValue = new Date(aValue);
        bValue = new Date(bValue);
      }

      if (sortOrder === 'asc') {
        return aValue > bValue ? 1 : -1;
      } else {
        return aValue < bValue ? 1 : -1;
      }
    });

    return filtered;
  }, [alerts, searchTerm, severityFilter, statusFilter, sortBy, sortOrder]);

  // Alert item renderer for virtual scrolling
  const AlertItem = ({ index, style }) => {
    const alert = filteredAlerts[index];
    
    return (
      <div style={style} className={`alert-row ${alert.severity}`}>
        <div className="alert-indicator"></div>
        <div className="alert-content">
          <div className="alert-main">
            <div className="alert-header">
              <span className="alert-name">{alert.alertname}</span>
              <span className="alert-time">
                {format(new Date(alert.timestamp), 'MMM dd, HH:mm:ss')}
              </span>
            </div>
            <div className="alert-meta">
              <span className="alert-instance">{alert.instance}</span>
              <span className={`alert-severity ${alert.severity}`}>
                {alert.severity}
              </span>
              <span className={`alert-status ${alert.status}`}>
                {alert.status}
              </span>
            </div>
          </div>
          <div className="alert-description">
            {alert.annotations?.description || alert.annotations?.summary || 'No description available'}
          </div>
          {alert.labels && Object.keys(alert.labels).length > 0 && (
            <div className="alert-labels">
              {Object.entries(alert.labels).map(([key, value]) => (
                <span key={key} className="label-tag">
                  {key}: {value}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  };

  const severityStats = useMemo(() => {
    const stats = { all: alerts?.length || 0, critical: 0, warning: 0, info: 0 };
    alerts?.forEach(alert => {
      stats[alert.severity] = (stats[alert.severity] || 0) + 1;
    });
    return stats;
  }, [alerts]);

  return (
    <div className="alerts-list-container">
      <div className="alerts-header">
        <div className="header-left">
          <h2>Alerts Management</h2>
          <button onClick={onRefresh} className="refresh-button">
            🔄 Refresh
          </button>
        </div>
        <div className="header-stats">
          <span className="stat-item">
            Total: <strong>{severityStats.all}</strong>
          </span>
          <span className="stat-item critical">
            Critical: <strong>{severityStats.critical}</strong>
          </span>
          <span className="stat-item warning">
            Warning: <strong>{severityStats.warning}</strong>
          </span>
          <span className="stat-item info">
            Info: <strong>{severityStats.info}</strong>
          </span>
        </div>
      </div>

      <div className="alerts-controls">
        <div className="search-container">
          <input
            type="text"
            placeholder="Search alerts..."
            className="search-input"
            onChange={(e) => debouncedSearch(e.target.value)}
          />
        </div>
        
        <div className="filters">
          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="filter-select"
          >
            <option value="all">All Severities</option>
            <option value="critical">Critical</option>
            <option value="warning">Warning</option>
            <option value="info">Info</option>
          </select>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="filter-select"
          >
            <option value="all">All Status</option>
            <option value="active">Active</option>
            <option value="resolved">Resolved</option>
            <option value="acknowledged">Acknowledged</option>
          </select>

          <select
            value={`${sortBy}-${sortOrder}`}
            onChange={(e) => {
              const [field, order] = e.target.value.split('-');
              setSortBy(field);
              setSortOrder(order);
            }}
            className="filter-select"
          >
            <option value="timestamp-desc">Newest First</option>
            <option value="timestamp-asc">Oldest First</option>
            <option value="severity-desc">Severity High-Low</option>
            <option value="alertname-asc">Name A-Z</option>
          </select>
        </div>
      </div>

      <div className="alerts-content">
        {filteredAlerts.length > 0 ? (
          <div className="virtual-list-container">
            <List
              height={600}
              itemCount={filteredAlerts.length}
              itemSize={120}
              className="virtual-list"
            >
              {AlertItem}
            </List>
          </div>
        ) : (
          <div className="no-alerts">
            <div className="no-alerts-icon">🔍</div>
            <h3>No alerts found</h3>
            <p>Try adjusting your search filters or refresh the data</p>
          </div>
        )}
      </div>

      <div className="alerts-footer">
        <span className="results-count">
          Showing {filteredAlerts.length} of {alerts?.length || 0} alerts
        </span>
      </div>
    </div>
  );
};

export default AlertsList;
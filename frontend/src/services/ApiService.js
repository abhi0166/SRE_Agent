import axios from 'axios';

// Simple, direct API configuration
const API_BASE_URL = '/api';

class ApiService {
  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 15000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Response interceptor for logging
    this.client.interceptors.response.use(
      (response) => {
        console.log(`API Success: ${response.config.url}`);
        return response;
      },
      (error) => {
        console.error(`API Error: ${error.message}`);
        return Promise.reject(error);
      }
    );
  }

  // System status endpoints
  async getSystemStatus() {
    const response = await this.client.get('/status');
    return response.data;
  }

  async getHealth() {
    const response = await this.client.get('/health');
    return response.data;
  }

  // Alert management endpoints
  async getAlerts(params = {}) {
    const { limit = 50, severity, status, offset = 0 } = params;
    const queryParams = new URLSearchParams({
      limit: limit.toString(),
      offset: offset.toString()
    });
    
    if (severity) queryParams.append('severity', severity);
    if (status) queryParams.append('status', status);
    
    const response = await this.client.get(`/alerts?${queryParams}`);
    return response.data;
  }

  async getAlert(alertId) {
    const response = await this.client.get(`/alerts/${alertId}`);
    return response.data;
  }

  async updateAlertStatus(alertId, status, metadata = {}) {
    const response = await this.client.put(`/alerts/${alertId}/status`, {
      status,
      metadata
    });
    return response.data;
  }

  async getAlertStats() {
    const response = await this.client.get('/alerts/stats');
    return response.data;
  }

  async getSystemMetrics(params = {}) {
    const { hours = 24, hostname } = params;
    const queryParams = new URLSearchParams({
      hours: hours.toString()
    });
    
    if (hostname) queryParams.append('hostname', hostname);
    
    const response = await this.client.get(`/metrics?${queryParams}`);
    return response.data;
  }

  async getDatabaseStatus() {
    const response = await this.client.get('/database/status');
    return response.data;
  }

  async testWebhook(alertData) {
    const response = await this.client.post('/webhook/test', alertData);
    return response.data;
  }

  // High-performance endpoints for large-scale monitoring
  async getBatchAlerts(batchSize = 1000, page = 0) {
    const response = await this.client.post('/alerts/batch', {
      batch_size: batchSize,
      page: page
    });
    return response.data;
  }

  async getBatchMetrics(nodeIds, timeRange) {
    const response = await this.client.post('/metrics/batch', {
      node_ids: nodeIds,
      time_range: timeRange
    });
    return response.data;
  }

  // Performance optimized endpoints for large datasets
  async getAlertsSummary(timeRange = '24h') {
    const response = await this.client.get(`/alerts/summary?range=${timeRange}`);
    return response.data;
  }

  async getMetricsSummary(timeRange = '24h') {
    const response = await this.client.get(`/metrics/summary?range=${timeRange}`);
    return response.data;
  }

  // Search and filtering endpoints
  async searchAlerts(query, filters = {}) {
    const response = await this.client.post('/alerts/search', {
      query,
      filters
    });
    return response.data;
  }

  async getFilteredMetrics(filters) {
    const response = await this.client.post('/metrics/filtered', {
      filters
    });
    return response.data;
  }

  // Real-time subscription endpoints
  async subscribeToAlerts(callback) {
    // WebSocket connection logic would go here
    console.log('WebSocket subscription not implemented');
  }
}

export default new ApiService();
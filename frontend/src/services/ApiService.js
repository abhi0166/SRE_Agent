import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://172.31.128.110:5000';

class ApiService {
  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor for performance tracking
    this.client.interceptors.request.use(
      (config) => {
        config.metadata = { startTime: new Date() };
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor for error handling and performance logging
    this.client.interceptors.response.use(
      (response) => {
        const endTime = new Date();
        const duration = endTime - response.config.metadata.startTime;
        console.log(`API Call: ${response.config.url} took ${duration}ms`);
        return response;
      },
      (error) => {
        if (error.response) {
          console.error(`API Error: ${error.response.status} - ${error.response.data.message || error.message}`);
        } else if (error.request) {
          console.error('API Error: No response received');
        } else {
          console.error(`API Error: ${error.message}`);
        }
        return Promise.reject(error);
      }
    );
  }

  // System status endpoints
  async getSystemStatus() {
    const response = await this.client.get('/api/status');
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
      ...(severity && { severity }),
      ...(status && { status }),
      ...(offset && { offset: offset.toString() })
    });

    const response = await this.client.get(`/api/alerts?${queryParams}`);
    return response.data;
  }

  async getAlert(alertId) {
    const response = await this.client.get(`/api/alerts/${alertId}`);
    return response.data;
  }

  async updateAlertStatus(alertId, status, metadata = {}) {
    const response = await this.client.put(`/api/alerts/${alertId}/status`, {
      status,
      metadata
    });
    return response.data;
  }

  async getAlertStats() {
    const response = await this.client.get('/api/alerts/stats');
    return response.data;
  }

  // System metrics endpoints
  async getSystemMetrics(params = {}) {
    const { hours = 24, hostname } = params;
    const queryParams = new URLSearchParams({
      hours: hours.toString(),
      ...(hostname && { hostname })
    });

    const response = await this.client.get(`/api/metrics?${queryParams}`);
    return response.data;
  }

  // Database endpoints
  async getDatabaseStatus() {
    const response = await this.client.get('/api/database/status');
    return response.data;
  }

  // Webhook testing
  async testWebhook(alertData) {
    const response = await this.client.post('/webhook/test', alertData);
    return response.data;
  }

  // Batch operations for large-scale monitoring
  async getBatchAlerts(batchSize = 1000, page = 0) {
    const response = await this.client.get('/api/alerts/batch', {
      params: {
        batch_size: batchSize,
        page
      }
    });
    return response.data;
  }

  async getBatchMetrics(nodeIds, timeRange) {
    const response = await this.client.post('/api/metrics/batch', {
      node_ids: nodeIds,
      time_range: timeRange
    });
    return response.data;
  }

  // Performance optimized endpoints for large datasets
  async getAlertsSummary(timeRange = '24h') {
    const response = await this.client.get(`/api/alerts/summary?range=${timeRange}`);
    return response.data;
  }

  async getMetricsSummary(timeRange = '24h') {
    const response = await this.client.get(`/api/metrics/summary?range=${timeRange}`);
    return response.data;
  }

  // Search and filtering for large datasets
  async searchAlerts(query, filters = {}) {
    const response = await this.client.post('/api/alerts/search', {
      query,
      filters
    });
    return response.data;
  }

  async getFilteredMetrics(filters) {
    const response = await this.client.post('/api/metrics/filter', filters);
    return response.data;
  }

  // Real-time subscription endpoints
  async subscribeToAlerts(callback) {
    // Implementation for Server-Sent Events or WebSocket subscription
    const eventSource = new EventSource(`${API_BASE_URL}/api/alerts/stream`);
    
    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      callback(data);
    };

    eventSource.onerror = (error) => {
      console.error('SSE connection error:', error);
      eventSource.close();
    };

    return () => eventSource.close();
  }
}

export { ApiService };
export default new ApiService();
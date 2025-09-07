import axios from 'axios';

// Helper function to get CSRF token
const getCSRFToken = () => {
  // Try to get from Django template global config first
  if (window.DJANGO_CONFIG?.CSRF_TOKEN) {
    return window.DJANGO_CONFIG.CSRF_TOKEN;
  }
  
  // Fallback to cookie method
  const name = 'csrftoken';
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
};

// Create axios instance with base configuration
const apiClient = axios.create({
  baseURL: window.DJANGO_CONFIG?.API_BASE_URL || 'http://localhost:8000/api/v1/',
  timeout: 10000,
  withCredentials: true,  // Include credentials for CSRF protection
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    // Add CSRF token for non-GET requests
    if (['post', 'put', 'patch', 'delete'].includes(config.method.toLowerCase())) {
      const csrfToken = getCSRFToken();
      if (csrfToken) {
        config.headers['X-CSRFToken'] = csrfToken;
      }
    }
    
    // Add auth token if available
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error);
    
    // Handle specific error cases
    if (error.response?.status === 401) {
      localStorage.removeItem('authToken');
      // Redirect to login if needed
    }
    
    return Promise.reject(error);
  }
);

// Global monitoring state management
class MonitoringStateManager {
  constructor() {
    this.isMonitoring = false;
    this.listeners = [];
  }

  subscribe(callback) {
    this.listeners.push(callback);
    return () => {
      this.listeners = this.listeners.filter(listener => listener !== callback);
    };
  }

  setMonitoringState(state) {
    this.isMonitoring = state;
    this.listeners.forEach(callback => callback(state));
  }

  getMonitoringState() {
    return this.isMonitoring;
  }
}

export const monitoringStateManager = new MonitoringStateManager();

// API endpoints
export const api = {
  // Generic HTTP methods
  get: (url, config = {}) => apiClient.get(url, config),
  post: (url, data = {}, config = {}) => apiClient.post(url, data, config),
  put: (url, data = {}, config = {}) => apiClient.put(url, data, config),
  patch: (url, data = {}, config = {}) => apiClient.patch(url, data, config),
  delete: (url, config = {}) => apiClient.delete(url, config),

  // Test endpoint
  test: () => apiClient.get('test/').then(res => res.data),

  // Dashboard
  getDashboardStats: () => apiClient.get('dashboard/stats/').then(res => res.data),
  getNetworkOverview: () => apiClient.get('network/overview/').then(res => res.data),

  // Network Devices
  getDevices: (params = {}) => apiClient.get('devices/', { params }).then(res => res.data),
  getDevice: (id) => apiClient.get(`devices/${id}/`).then(res => res.data),
  createDevice: (data) => apiClient.post('devices/', data).then(res => res.data),
  updateDevice: (id, data) => apiClient.put(`devices/${id}/`, data).then(res => res.data),
  deleteDevice: (id) => apiClient.delete(`devices/${id}/`).then(res => res.data),
  toggleDeviceMonitoring: (id) => apiClient.post(`devices/${id}/toggle_monitoring/`).then(res => res.data),
  pingDevice: (id) => apiClient.post(`devices/${id}/ping/`).then(res => res.data),
  scanDevicePorts: (id, ports = null) => apiClient.post(`devices/${id}/scan_ports/`, { ports }, { timeout: 30000 }).then(res => res.data), // 30s timeout: port scanning can take time
  clearAllDevices: () => apiClient.post('devices/clear_all/').then(res => res.data),

  // Network Scans
  getNetworkScans: (params = {}) => apiClient.get('scans/', { params }).then(res => res.data),
  getNetworkScan: (id) => apiClient.get(`scans/${id}/`).then(res => res.data),
  createNetworkScan: (data) => apiClient.post('scans/', data).then(res => res.data),
  updateNetworkScan: (id, data) => apiClient.put(`scans/${id}/`, data).then(res => res.data),
  deleteNetworkScan: (id) => apiClient.delete(`scans/${id}/`).then(res => res.data),
  startNetworkScan: (id) => apiClient.post(`scans/${id}/start/`).then(res => res.data),
  pauseNetworkScan: (id) => apiClient.post(`scans/${id}/pause/`).then(res => res.data),
  resumeNetworkScan: (id) => apiClient.post(`scans/${id}/resume/`).then(res => res.data),
  stopNetworkScan: (id) => apiClient.post(`scans/${id}/stop/`).then(res => res.data),
  cancelNetworkScan: (id) => apiClient.post(`scans/${id}/cancel/`).then(res => res.data),
  getScanProgress: (id) => apiClient.get(`scans/${id}/progress/`).then(res => res.data),
  getScanResults: (id) => apiClient.get(`scans/${id}/results/`).then(res => res.data),
  downloadScanReport: (id, format = 'json') => {
    // Handle txt format specially since it has routing issues with query params
    const url = format === 'txt' ? `scans/${id}/report/` : `scans/${id}/report/`;
    const params = format === 'txt' ? {} : { format };
    
    return apiClient.get(url, { 
      params,
      responseType: 'blob'
    }).then(res => res.data);
  },
  
  // Scan Templates
  getScanTemplates: (params = {}) => apiClient.get('scan-templates/', { params }).then(res => res.data),
  getScanTemplate: (id) => apiClient.get(`scan-templates/${id}/`).then(res => res.data),
  createScanTemplate: (data) => apiClient.post('scan-templates/', data).then(res => res.data),
  updateScanTemplate: (id, data) => apiClient.put(`scan-templates/${id}/`, data).then(res => res.data),
  deleteScanTemplate: (id) => apiClient.delete(`scan-templates/${id}/`).then(res => res.data),
  createScanFromTemplate: (templateId, data) => apiClient.post(`scan-templates/${templateId}/create_scan/`, data).then(res => res.data),
  
  // Quick Scan Actions
  quickDiscovery: (targetRange = '192.168.1.0/24') => apiClient.post('scans/quick_discovery/', { target_range: targetRange }, { timeout: 60000 }).then(res => res.data),
  quickPortScan: (targetRange, ports = '22,80,443') => apiClient.post('scans/quick_port_scan/', { 
    target_range: targetRange, 
    target_ports: ports 
  }, { timeout: 120000 }).then(res => res.data),
  quickVulnerabilityScan: (targetRange) => apiClient.post('scans/quick_vulnerability_scan/', { 
    target_range: targetRange 
  }, { timeout: 300000 }).then(res => res.data),
  
  // Scan Statistics
  getScanStatistics: () => apiClient.get('scans/statistics/').then(res => res.data),
  getScanHistory: (params = {}) => apiClient.get('scans/history/', { params }).then(res => res.data),

  // Network Traffic
  getTraffic: (params = {}) => apiClient.get('traffic/', { params }).then(res => res.data),
  getTrafficSummary: () => apiClient.get('traffic/summary/').then(res => res.data),

  // Security Events
  getSecurityEvents: (params = {}) => apiClient.get('security-events/', { params }).then(res => res.data),
  getAllSecurityEvents: () => apiClient.get('security-events/all/').then(res => res.data),
  getSecurityEvent: (id) => apiClient.get(`security-events/${id}/`).then(res => res.data),
  investigateSecurityEvent: (id) => apiClient.post(`security-events/${id}/investigate/`).then(res => res.data),
  resolveSecurityEvent: (id) => apiClient.post(`security-events/${id}/resolve/`).then(res => res.data),
  blockSecurityThreat: (id) => apiClient.post(`security-events/${id}/block/`).then(res => res.data),
  getSecurityEventStats: () => apiClient.get('security-events/stats/').then(res => res.data),
  
  // Additional API methods for comprehensive monitoring
  getNetworkDevices: () => apiClient.get('devices/').then(res => res.data),
  getNetworkStats: () => apiClient.get('dashboard/stats/').then(res => res.data),
  getDeviceStats: () => apiClient.get('devices/stats/').then(res => res.data),

  // Network Interfaces
  getNetworkInterfaces: () => apiClient.get('interfaces/').then(res => res.data),
  discoverInterfaces: () => apiClient.get('interfaces/discover/').then(res => res.data),

  // Network Configuration
  getConfigurations: () => apiClient.get('configurations/').then(res => res.data),
  getConfiguration: (id) => apiClient.get(`configurations/${id}/`).then(res => res.data),
  createConfiguration: (data) => apiClient.post('configurations/', data).then(res => res.data),
  updateConfiguration: (id, data) => apiClient.put(`configurations/${id}/`, data).then(res => res.data),
  deleteConfiguration: (id) => apiClient.delete(`configurations/${id}/`).then(res => res.data),
  activateConfiguration: (id) => apiClient.post(`configurations/${id}/activate/`).then(res => res.data),

  // Enhanced Monitoring Control with Global State
  startMonitoring: async () => {
    // Use absolute URL for monitoring endpoints under /api/v1/
    const result = await axios.post('/api/v1/monitoring/start/', {}, {
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCSRFToken()
      },
      withCredentials: true
    }).then(res => res.data);
    monitoringStateManager.setMonitoringState(true);
    return result;
  },
  stopMonitoring: async () => {
    // Use absolute URL for monitoring endpoints under /api/v1/
    const result = await axios.post('/api/v1/monitoring/stop/', {}, {
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCSRFToken()
      },
      withCredentials: true
    }).then(res => res.data);
    monitoringStateManager.setMonitoringState(false);
    return result;
  },
  getMonitoringStatus: () => axios.get('/api/v1/monitoring/status/', {
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCSRFToken()
    },
    withCredentials: true
  }).then(res => res.data),
};

export default apiClient;
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('token');
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
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized access
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Dashboard API
export const getDashboardStats = () => api.get('/dashboard/stats/').then(res => res.data);

// File API
export const uploadFile = (file) => {
  const formData = new FormData();
  formData.append('file', file);
  return api.post('/upload/', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  }).then(res => res.data);
};

export const importFromForms = (formsUrl) => api.post('/upload/forms/', { forms_url: formsUrl }).then(res => res.data);

export const getFiles = () => api.get('/files/').then(res => res.data.results || res.data);
export const getFile = (id) => api.get(`/files/${id}/`).then(res => res.data);
export const deleteFile = (id) => api.delete(`/files/${id}/`).then(res => res.data);
export const validateFile = (id) => api.post(`/files/${id}/validate/`).then(res => res.data);

// Data Processing API
export const processData = (fileIds) => api.post('/process/', { file_ids: fileIds }).then(res => res.data);
export const analyzeData = (fileIds) => api.post('/analyze/', { file_ids: fileIds }).then(res => res.data);

// Cohort API
export const getCohorts = () => api.get('/data/cohorts/').then(res => res.data.results || res.data);
export const getCohort = (id) => api.get(`/data/cohorts/${id}/`).then(res => res.data);
export const createCohorts = (fileIds) => api.post('/data/cohorts/create/', { file_ids: fileIds }).then(res => res.data);
export const getCohortParticipants = (id) => api.get(`/data/cohorts/${id}/participants/`).then(res => res.data);

// Participant API
export const getParticipants = (params = {}) => api.get('/participants/', { params }).then(res => res.data.results || res.data);
export const getParticipant = (id) => api.get(`/participants/${id}/`).then(res => res.data);

// BPA API
export const processBPA = (cohortIds) => api.post('/bpa/process/', { cohort_ids: cohortIds }).then(res => res.data);
export const runBPADemo = () => api.get('/bpa/demo/').then(res => res.data);

// Email API
export const getEmailTemplates = () => api.get('/email/templates/').then(res => res.data);
export const getEmailCampaigns = () => api.get('/email/campaigns/').then(res => res.data);
export const sendEmails = (data) => api.post('/email/send/', data).then(res => res.data);
export const previewEmail = (data) => api.post('/email/preview/', data).then(res => res.data);
export const testEmailConnection = (data) => api.post('/email/test-connection/', data).then(res => res.data);
export const generateEmailTemplates = (cohortIds = []) => api.post('/email/generate-templates/', { cohort_ids: cohortIds }).then(res => res.data);
export const getEmailConfig = () => api.get('/email/config/').then(res => res.data);

// Reports API
export const generateReport = (data) => api.post('/reports/generate/', data).then(res => res.data);
export const generateEnhancedReport = (data) => api.post('/reports/generate-enhanced/', data).then(res => res.data);
export const getReports = () => api.get('/reports/list/').then(res => res.data);
export const downloadReport = (id) => api.get(`/reports/download/${id}/`, { responseType: 'blob' }).then(res => res.data);
export const sendReportEmail = (data) => api.post('/reports/send-email/', data).then(res => res.data);
export const deleteReport = (id) => api.delete(`/reports/delete/${id}/`).then(res => res.data);

export { api };

import axios from 'axios';

// API Base URL - adjust for your deployment
const API_BASE_URL = process.env.REACT_APP_API_URL || 'https://petplantr.com:8443';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 seconds for AI processing
});

// Request interceptor for authentication
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('petplantr_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('petplantr_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const petplantrAPI = {
  // Health check
  healthCheck: () => api.get('/api/v1/health'),

  // Authentication
  login: (credentials) => api.post('/auth/login', credentials),
  register: (userData) => api.post('/auth/register', userData),
  getCurrentUser: () => api.get('/auth/me'),

  // Breed Detection
  detectBreed: (imageData) => api.post('/api/v1/breed/detect', imageData),
  detectBreedFromFile: (file, params = {}) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/api/v1/breed/detect-file', formData, {
      params,
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
  getSupportedBreeds: () => api.get('/api/v1/breed/breeds'),
  getModelInfo: () => api.get('/api/v1/breed/model-info'),

  // Planter Generation
  generatePlanter: (file, params = {}) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/api/v1/generate-planter', formData, {
      params,
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
  getGenerationStatus: (jobId) => api.get(`/api/v1/status/${jobId}`),
  downloadSTL: (jobId) => api.get(`/api/v1/download/${jobId}/stl`, {
    responseType: 'blob'
  }),

  // Gallery
  getPublicModels: (params = {}) => api.get('/api/v2/gallery/models', { params }),
  addModelToGallery: (modelData) => api.post('/api/v2/gallery/models', modelData),
  getModelDetails: (modelId) => api.get(`/api/v2/gallery/models/${modelId}`),
  likeModel: (modelId, userId) => api.post(`/api/v2/gallery/models/${modelId}/like`, { user_id: userId }),

  // User Management
  getUserProfile: (userId) => api.get(`/api/v2/users/${userId}`),
  updateUserProfile: (userId, updates) => api.put(`/api/v2/users/${userId}`, updates),
  getUserUsage: (userId) => api.get(`/api/v2/users/${userId}/usage`),

  // Analytics
  getRealtimeAnalytics: () => api.get('/api/v2/analytics/realtime'),
  getUserInsights: (userId) => api.get(`/api/v2/analytics/user/${userId}`),
  getSystemHealth: () => api.get('/api/v2/analytics/health'),

  // Batch Processing
  createBatch: (batchData) => api.post('/api/v2/batch', batchData),
  getBatchStatus: (batchId) => api.get(`/api/v2/batch/${batchId}`),
  addJobToBatch: (batchId, jobData) => api.post(`/api/v2/batch/${batchId}/jobs`, jobData),
  startBatch: (batchId) => api.post(`/api/v2/batch/${batchId}/start`),

  // Notifications
  getUserNotifications: (userId, params = {}) => api.get(`/api/v2/notifications/${userId}`, { params }),
  markNotificationRead: (notificationId, userId) => api.put(`/api/v2/notifications/${notificationId}/read`, { user_id: userId }),

  // System
  getSystemStats: () => api.get('/api/v2/system/stats'),
};

export default api;

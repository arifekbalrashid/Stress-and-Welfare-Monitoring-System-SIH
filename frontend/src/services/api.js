import axios from 'axios';
import i18n from '../i18n';

const API_BASE = import.meta.env.VITE_API_URL || '/api/v1';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // for httpOnly refresh cookie
});

// Request interceptor — attach JWT access token and language
api.interceptors.request.use(
  (config) => {
    try {
      const token = localStorage.getItem('access_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      
      const lang = i18n.language || localStorage.getItem('i18nextLng');
      if (lang) {
        config.headers['Accept-Language'] = lang;
      }
    } catch (e) {}
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor — handle 401 with token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const res = await axios.post(`${API_BASE}/auth/refresh`, {}, { withCredentials: true });
        const newToken = res.data.data.access_token;
        try {
          localStorage.setItem('access_token', newToken);
        } catch (e) {}
        originalRequest.headers.Authorization = `Bearer ${newToken}`;
        return api(originalRequest);
      } catch (refreshError) {
        try {
          localStorage.removeItem('access_token');
          localStorage.removeItem('user');
        } catch (e) {}
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

export default api;

// ---- Auth ----
export const authAPI = {
  login: (credentials) => api.post('/auth/login', credentials),
  refresh: () => api.post('/auth/refresh'),
  logout: () => api.post('/auth/logout'),
};

// ---- Personnel ----
export const personnelAPI = {
  getMe: () => api.get('/personnel/me'),
  getMyRisk: () => api.get('/personnel/me/risk'),
  getDashboard: () => api.get('/personnel/me/dashboard'),
};

// ---- Wellness ----
export const wellnessAPI = {
  submitCheckin: (data) => api.post('/wellness/checkin', data),
  getHistory: (params) => api.get('/wellness/history', { params }),
  getCheckinStatus: () => api.get('/wellness/checkin/status'),
};

// ---- Risk ----
export const riskAPI = {
  getHistory: (params) => api.get('/risk/history', { params }),
  predict: (personnelId) => api.post('/risk/predict', { personnel_id: personnelId }),
};

// ---- Consent ----
export const consentAPI = {
  getAll: () => api.get('/consent'),
  grant: (dataType) => api.post('/consent', { data_type: dataType }),
  withdraw: (dataType) => api.post('/consent/withdraw', { data_type: dataType }),
};

// ---- Support ----
export const supportAPI = {
  submit: (data) => api.post('/support/request', data),
  getRequests: (params) => api.get('/support/requests', { params }),
};

// ---- Welfare Officer ----
export const welfareAPI = {
  getCases: (params) => api.get('/welfare/cases', { params }),
  getCase: (id) => api.get(`/welfare/cases/${id}`),
  logIntervention: (data) => api.post('/welfare/interventions', data),
  updateCaseStatus: (personnelId, status) => api.post(`/welfare/cases/${personnelId}/status`, { review_status: status }),
  getSupportRequests: (params) => api.get('/welfare/support-requests', { params }),
  updateSupportRequestStatus: (requestId, status) => api.post(`/welfare/support-requests/${requestId}/status`, { status }),
};

// ---- Commander ----
export const commanderAPI = {
  getOverview: () => api.get('/commander/overview'),
  getRoster: () => api.get('/commander/roster'),
  getTrends: () => api.get('/commander/trends'),
  getInsights: () => api.get('/commander/insights'),
};

// ---- Admin ----
export const adminAPI = {
  importData: (formData) => api.post('/admin/import-data', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  getUsers: (params) => api.get('/admin/users', { params }),
  createUser: (data) => api.post('/admin/users', data),
  updateUser: (id, data) => api.put(`/admin/users/${id}`, data),
  getPersonnel: (params) => api.get('/admin/personnel', { params }),
  createPersonnel: (data) => api.post('/admin/personnel', data),
  getUnits: () => api.get('/admin/units'),
  createUnit: (data) => api.post('/admin/units', data),
  getModelStatus: () => api.get('/admin/model-status'),
  getAuditLogs: (params) => api.get('/admin/audit-logs', { params }),
  addOperationalData: (data) => api.post('/admin/operational-data', data),
  getImportStatus: () => api.get('/admin/import-status'),
};

// ---- Chat ----
export const chatAPI = {
  sendMessage: (payload) => api.post('/chat', payload),
};

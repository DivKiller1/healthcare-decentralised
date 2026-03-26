// frontend/shared/api.ts
import axios from 'axios';

const API_BASE_URL = '/api'; // Routed via Ingress

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Auth interceptor
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Global API endpoints
export const authApi = {
  requestOtp: (mobile: string) => api.post('/auth/request-otp', { mobile }),
  verifyOtp: (mobile: string, otp: string) => api.post('/auth/verify-otp', { mobile, otp }),
  refresh: (refreshToken: string) => api.post('/auth/refresh', { refresh_token: refreshToken }),
  logout: (refreshToken: string) => api.post('/auth/logout', { refresh_token: refreshToken }),
};

export const userApi = {
  getMe: () => api.get('/users/me'),
  updateMe: (data: { name?: string; address?: string }) => api.put('/users/me', data),
};

export const facilityApi = {
  list: (params?: any) => api.get('/facilities', { params }),
  getById: (id: string) => api.get(`/facilities/${id}`),
};

export const requestApi = {
  create: (data: any) => api.post('/requests', data),
  getMine: () => api.get('/requests/mine'),
};

export default api;

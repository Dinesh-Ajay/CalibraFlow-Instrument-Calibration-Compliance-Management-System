import axios from 'axios';

const api = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('calibraflow_token');
    if (token) config.headers.Authorization = `Bearer ${token}`;
    return config;
  },
  (error) => Promise.reject(error)
);

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error?.response?.status;
    if (status === 401) {
      if (!window.location.pathname.includes('/login')) {
        localStorage.removeItem('calibraflow_token');
        localStorage.removeItem('calibraflow_user');
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export default api;

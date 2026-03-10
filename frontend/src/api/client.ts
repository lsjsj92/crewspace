import axios from 'axios';
import {
  getAccessToken,
  setAccessToken,
  setRefreshToken,
  clearAccessToken,
  clearRefreshToken,
  getRefreshToken,
} from '@/utils/token';

const apiClient = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Endpoints where 401 should NOT trigger refresh/redirect
const AUTH_ENDPOINTS = ['/auth/login', '/auth/register', '/auth/refresh'];

apiClient.interceptors.request.use(
  (config) => {
    const token = getAccessToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    const requestUrl = originalRequest?.url || '';

    // Skip refresh logic for auth endpoints — let the caller handle the error
    const isAuthEndpoint = AUTH_ENDPOINTS.some((ep) => requestUrl.endsWith(ep));
    if (isAuthEndpoint) {
      return Promise.reject(error);
    }

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      const refreshTokenValue = getRefreshToken();
      if (refreshTokenValue) {
        try {
          const response = await axios.post('/api/v1/auth/refresh', {
            refresh_token: refreshTokenValue,
          });

          const { access_token, refresh_token } = response.data;
          setAccessToken(access_token);
          setRefreshToken(refresh_token);

          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return apiClient(originalRequest);
        } catch {
          clearAccessToken();
          clearRefreshToken();
          window.location.href = '/login';
          return Promise.reject(error);
        }
      } else {
        clearAccessToken();
        clearRefreshToken();
        window.location.href = '/login';
      }
    }

    return Promise.reject(error);
  }
);

export function setTokens(accessToken: string, refreshToken: string): void {
  setAccessToken(accessToken);
  setRefreshToken(refreshToken);
}

export function clearTokens(): void {
  clearAccessToken();
  clearRefreshToken();
}

export default apiClient;

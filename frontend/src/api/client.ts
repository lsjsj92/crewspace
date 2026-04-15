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

// 동시 토큰 갱신 요청을 직렬화하기 위한 싱글턴 Promise
let refreshPromise: Promise<string> | null = null;

function refreshAccessToken(): Promise<string> {
  if (refreshPromise) {
    return refreshPromise;
  }

  const refreshTokenValue = getRefreshToken();
  if (!refreshTokenValue) {
    clearAccessToken();
    clearRefreshToken();
    window.location.href = '/login';
    return Promise.reject(new Error('No refresh token'));
  }

  refreshPromise = axios
    .post<{ access_token: string; refresh_token: string }>('/api/v1/auth/refresh', {
      refresh_token: refreshTokenValue,
    })
    .then((response) => {
      const { access_token, refresh_token } = response.data;
      setAccessToken(access_token);
      setRefreshToken(refresh_token);
      return access_token;
    })
    .catch((error) => {
      clearAccessToken();
      clearRefreshToken();
      window.location.href = '/login';
      return Promise.reject(error);
    })
    .finally(() => {
      refreshPromise = null;
    });

  return refreshPromise;
}

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
      try {
        const newAccessToken = await refreshAccessToken();
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
        return apiClient(originalRequest);
      } catch {
        return Promise.reject(error);
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

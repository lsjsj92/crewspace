import apiClient from './client';
import type { LoginRequest, RegisterRequest, TokenResponse, User } from '@/types';

export async function login(data: LoginRequest): Promise<TokenResponse> {
  const response = await apiClient.post<TokenResponse>('/auth/login', data);
  return response.data;
}

export async function register(data: RegisterRequest): Promise<User> {
  const response = await apiClient.post<User>('/auth/register', data);
  return response.data;
}

export async function refreshToken(refreshTokenValue: string): Promise<TokenResponse> {
  const response = await apiClient.post<TokenResponse>('/auth/refresh', {
    refresh_token: refreshTokenValue,
  });
  return response.data;
}

export async function logout(refreshTokenValue: string): Promise<void> {
  await apiClient.post('/auth/logout', {
    refresh_token: refreshTokenValue,
  });
}

export async function getMe(): Promise<User> {
  const response = await apiClient.get<User>('/auth/me');
  return response.data;
}

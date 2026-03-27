// frontend/src/api/profile.ts
import apiClient from './client';
import type { User } from '@/types';

export async function getMyProfile(): Promise<User> {
  const response = await apiClient.get<User>('/users/me');
  return response.data;
}

export async function updateMyProfile(
  data: { display_name?: string; organization?: string }
): Promise<User> {
  const response = await apiClient.patch<User>('/users/me', data);
  return response.data;
}

export async function changeMyPassword(
  data: { current_password: string; new_password: string }
): Promise<void> {
  await apiClient.patch('/users/me/password', data);
}

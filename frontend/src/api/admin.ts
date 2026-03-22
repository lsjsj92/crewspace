import apiClient from './client';
import type { User } from '@/types';

export async function getUsers(): Promise<User[]> {
  const response = await apiClient.get<{ users: User[] }>('/users');
  return response.data.users;
}

export async function createUser(data: {
  email: string;
  username: string;
  display_name: string;
  password: string;
  employee_id?: string;
  organization?: string;
  gw_id?: string;
}): Promise<User> {
  const response = await apiClient.post<User>('/users', data);
  return response.data;
}

export async function updateUser(
  userId: string,
  data: { display_name?: string; is_active?: boolean }
): Promise<User> {
  const response = await apiClient.patch<User>(`/users/${userId}`, data);
  return response.data;
}

export async function adminUpdateUser(
  userId: string,
  data: {
    email?: string;
    username?: string;
    display_name?: string;
    is_active?: boolean;
    is_superadmin?: boolean;
    employee_id?: string | null;
    organization?: string | null;
    gw_id?: string | null;
  }
): Promise<User> {
  const response = await apiClient.put<User>(`/users/${userId}/admin`, data);
  return response.data;
}

export async function deactivateUser(userId: string): Promise<void> {
  await apiClient.delete(`/users/${userId}`);
}

export async function resetUserPassword(
  userId: string,
  newPassword: string
): Promise<void> {
  await apiClient.patch(`/users/${userId}/password`, {
    new_password: newPassword,
  });
}

export async function importHR(): Promise<{
  imported_count: number;
  updated_count: number;
  skipped_count: number;
  team_created_count: number;
}> {
  const response = await apiClient.post('/users/hr-import');
  return response.data;
}

export async function deleteTeam(teamId: string): Promise<void> {
  await apiClient.delete(`/teams/${teamId}`);
}

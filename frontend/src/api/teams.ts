import apiClient from './client';
import type { Team, TeamDetail, TeamMember } from '@/types';

export async function getMyTeams(): Promise<Team[]> {
  const response = await apiClient.get<Team[]>('/teams');
  return response.data;
}

export async function createTeam(data: { name: string; description?: string }): Promise<Team> {
  const response = await apiClient.post<Team>('/teams', data);
  return response.data;
}

export async function getTeam(teamId: string): Promise<TeamDetail> {
  const response = await apiClient.get<TeamDetail>(`/teams/${teamId}`);
  return response.data;
}

export async function updateTeam(
  teamId: string,
  data: { name?: string; description?: string }
): Promise<Team> {
  const response = await apiClient.patch<Team>(`/teams/${teamId}`, data);
  return response.data;
}

export async function getTeamMembers(teamId: string): Promise<TeamMember[]> {
  const response = await apiClient.get<TeamMember[]>(`/teams/${teamId}/members`);
  return response.data;
}

export async function addTeamMember(
  teamId: string,
  data: { email: string; role: string }
): Promise<TeamMember> {
  const response = await apiClient.post<TeamMember>(`/teams/${teamId}/members`, data);
  return response.data;
}

export async function updateMemberRole(
  teamId: string,
  userId: string,
  data: { role: string }
): Promise<TeamMember> {
  const response = await apiClient.patch<TeamMember>(
    `/teams/${teamId}/members/${userId}`,
    data
  );
  return response.data;
}

export async function removeTeamMember(teamId: string, userId: string): Promise<void> {
  await apiClient.delete(`/teams/${teamId}/members/${userId}`);
}

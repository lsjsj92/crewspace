import apiClient from './client';
import type { Project, BoardColumn, ProjectMember } from '@/types';

export interface ProjectDetail extends Project {
  columns: BoardColumn[];
}

export async function getProjects(status?: string): Promise<Project[]> {
  const params: Record<string, string> = {};
  if (status) params.status = status;
  const response = await apiClient.get<Project[]>('/projects', { params });
  return response.data;
}

export async function getRecentProjects(): Promise<Project[]> {
  const response = await apiClient.get<Project[]>('/projects/recent');
  return response.data;
}

export async function createProject(data: {
  name: string;
  description?: string;
  prefix: string;
  start_date?: string;
  end_date?: string;
  manager_user_id?: string;
}): Promise<Project> {
  const response = await apiClient.post<Project>('/projects', data);
  return response.data;
}

export async function getProject(projectId: string): Promise<ProjectDetail> {
  const response = await apiClient.get<ProjectDetail>(`/projects/${projectId}`);
  return response.data;
}

export async function updateProject(
  projectId: string,
  data: { name?: string; description?: string; start_date?: string; end_date?: string }
): Promise<Project> {
  const response = await apiClient.patch<Project>(`/projects/${projectId}`, data);
  return response.data;
}

export async function completeProject(projectId: string): Promise<Project> {
  const response = await apiClient.patch<Project>(`/projects/${projectId}/complete`);
  return response.data;
}

export async function deleteProject(projectId: string): Promise<void> {
  await apiClient.delete(`/projects/${projectId}`);
}

// Project Members
export async function getProjectMembers(projectId: string): Promise<ProjectMember[]> {
  const response = await apiClient.get<ProjectMember[]>(`/projects/${projectId}/members`);
  return response.data;
}

export async function addProjectMember(
  projectId: string,
  data: { user_id: string; role: string }
): Promise<ProjectMember> {
  const response = await apiClient.post<ProjectMember>(`/projects/${projectId}/members`, data);
  return response.data;
}

export async function updateProjectMemberRole(
  projectId: string,
  userId: string,
  data: { role: string }
): Promise<ProjectMember> {
  const response = await apiClient.patch<ProjectMember>(
    `/projects/${projectId}/members/${userId}`,
    data
  );
  return response.data;
}

export async function removeProjectMember(
  projectId: string,
  userId: string
): Promise<void> {
  await apiClient.delete(`/projects/${projectId}/members/${userId}`);
}

// Legacy: Team Projects (deprecated)
export async function getTeamProjects(
  teamId: string,
  status?: string
): Promise<Project[]> {
  const params: Record<string, string> = {};
  if (status) params.status = status;
  const response = await apiClient.get<Project[]>(`/teams/${teamId}/projects`, { params });
  return response.data;
}

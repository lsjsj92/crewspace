import apiClient from './client';
import type { Label } from '@/types';

export async function getLabels(projectId: string): Promise<Label[]> {
  const response = await apiClient.get<Label[]>(`/projects/${projectId}/labels`);
  return response.data;
}

export async function createLabel(
  projectId: string,
  data: { name: string; color: string }
): Promise<Label> {
  const response = await apiClient.post<Label>(`/projects/${projectId}/labels`, data);
  return response.data;
}

export async function updateLabel(
  labelId: string,
  data: { name?: string; color?: string }
): Promise<Label> {
  const response = await apiClient.patch<Label>(`/labels/${labelId}`, data);
  return response.data;
}

export async function deleteLabel(labelId: string): Promise<void> {
  await apiClient.delete(`/labels/${labelId}`);
}

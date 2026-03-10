import apiClient from './client';
import type { BoardColumn } from '@/types';

export async function getBoard(projectId: string): Promise<BoardColumn[]> {
  const response = await apiClient.get<BoardColumn[]>(`/projects/${projectId}/columns`);
  return response.data;
}

export async function createColumn(
  projectId: string,
  data: { name: string }
): Promise<BoardColumn> {
  const response = await apiClient.post<BoardColumn>(
    `/projects/${projectId}/columns`,
    data
  );
  return response.data;
}

export async function updateColumn(
  projectId: string,
  columnId: string,
  data: { name?: string; wip_limit?: number | null }
): Promise<BoardColumn> {
  const response = await apiClient.patch<BoardColumn>(
    `/projects/${projectId}/columns/${columnId}`,
    data
  );
  return response.data;
}

export async function deleteColumn(projectId: string, columnId: string): Promise<void> {
  await apiClient.delete(`/projects/${projectId}/columns/${columnId}`);
}

export async function reorderColumns(
  projectId: string,
  columnIds: string[]
): Promise<BoardColumn[]> {
  const response = await apiClient.post<BoardColumn[]>(
    `/projects/${projectId}/columns/reorder`,
    { column_ids: columnIds }
  );
  return response.data;
}

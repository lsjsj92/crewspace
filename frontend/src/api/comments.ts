import apiClient from './client';
import type { Comment } from '@/types';

export async function getComments(cardId: string): Promise<Comment[]> {
  const response = await apiClient.get<Comment[]>(`/cards/${cardId}/comments`);
  return response.data;
}

export async function createComment(cardId: string, content: string): Promise<Comment> {
  const response = await apiClient.post<Comment>(`/cards/${cardId}/comments`, { content });
  return response.data;
}

export async function updateComment(commentId: string, content: string): Promise<Comment> {
  const response = await apiClient.patch<Comment>(`/comments/${commentId}`, { content });
  return response.data;
}

export async function deleteComment(commentId: string): Promise<void> {
  await apiClient.delete(`/comments/${commentId}`);
}

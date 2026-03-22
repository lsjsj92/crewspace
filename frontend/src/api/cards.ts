import apiClient from './client';
import type { Card, CardType, CardPriority } from '@/types';

export interface CardFilters {
  card_type?: CardType;
  priority?: CardPriority;
  assignee_id?: string;
}

export async function getProjectCards(
  projectId: string,
  filters?: CardFilters
): Promise<Card[]> {
  const response = await apiClient.get<Card[]>(`/projects/${projectId}/cards`, {
    params: filters,
  });
  return response.data;
}

export async function createCard(
  projectId: string,
  data: {
    title: string;
    description?: string;
    card_type?: CardType;
    column_id?: string;
    parent_id?: string | null;
    priority?: CardPriority;
    start_date?: string | null;
    due_date?: string | null;
  }
): Promise<Card> {
  const response = await apiClient.post<Card>(`/projects/${projectId}/cards`, data);
  return response.data;
}

export async function getCard(cardId: string): Promise<Card> {
  const response = await apiClient.get<Card>(`/cards/${cardId}`);
  return response.data;
}

export async function updateCard(
  cardId: string,
  data: Record<string, unknown>
): Promise<Card> {
  const response = await apiClient.patch<Card>(`/cards/${cardId}`, data);
  return response.data;
}

export async function deleteCard(cardId: string): Promise<void> {
  await apiClient.delete(`/cards/${cardId}`);
}

export async function moveCard(
  cardId: string,
  data: { column_id: string; position: number }
): Promise<Card> {
  const response = await apiClient.post<Card>(`/cards/${cardId}/move`, data);
  return response.data;
}

export async function getCardChildren(cardId: string): Promise<Card[]> {
  const response = await apiClient.get<Card[]>(`/cards/${cardId}/children`);
  return response.data;
}

export async function addAssignee(cardId: string, userId: string): Promise<void> {
  await apiClient.post(`/cards/${cardId}/assignees`, { user_id: userId });
}

export async function removeAssignee(cardId: string, userId: string): Promise<void> {
  await apiClient.delete(`/cards/${cardId}/assignees/${userId}`);
}

export async function addLabel(cardId: string, labelId: string): Promise<void> {
  await apiClient.post(`/cards/${cardId}/labels/${labelId}`);
}

export async function removeLabel(cardId: string, labelId: string): Promise<void> {
  await apiClient.delete(`/cards/${cardId}/labels/${labelId}`);
}

export async function checkDuplicateTitle(
  projectId: string,
  title: string,
  cardType: string,
  excludeCardId?: string,
): Promise<{ has_duplicate: boolean; count: number; cards: { id: string; card_number: number; title: string }[] }> {
  const response = await apiClient.get(`/projects/${projectId}/cards/check-duplicate`, {
    params: { title, card_type: cardType, exclude_card_id: excludeCardId },
  });
  return response.data;
}

export async function reorderCard(
  cardId: string,
  data: { parent_id?: string | null; after_card_id?: string | null }
): Promise<Card> {
  const response = await apiClient.post<Card>(`/cards/${cardId}/reorder`, data);
  return response.data;
}

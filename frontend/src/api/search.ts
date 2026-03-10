import apiClient from './client';

export interface SearchResult {
  type: 'project' | 'card';
  id: string;
  title: string;
  description: string | null;
  // project fields
  team_id?: string;
  status?: string;
  prefix?: string;
  // card fields
  project_id?: string;
  card_number?: number;
  card_type?: string;
  priority?: string;
}

export interface SearchResponse {
  results: SearchResult[];
  query: string;
  type: string | null;
}

export async function searchAll(
  query: string,
  type?: 'project' | 'card'
): Promise<SearchResponse> {
  const params: Record<string, string> = { q: query };
  if (type) {
    params.type = type;
  }
  const response = await apiClient.get<SearchResponse>('/search', { params });
  return response.data;
}

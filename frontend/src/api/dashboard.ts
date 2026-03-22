import apiClient from './client';

export interface ProjectSummary {
  id: string;
  name: string;
  prefix: string;
  status: string;
  my_role: string | null;
}

export interface DashboardOverview {
  total_projects: number;
  total_active_projects: number;
  my_cards_count: number;
  projects: ProjectSummary[];
}

export interface CardWithProject {
  id: string;
  project_id: string;
  column_id: string;
  parent_id: string | null;
  card_type: string;
  card_number: number;
  title: string;
  description: string | null;
  priority: string;
  position: number;
  start_date: string | null;
  due_date: string | null;
  completed_at: string | null;
  archived_at: string | null;
  created_by: string;
  created_at: string;
  project_name: string;
}

export interface MyCardsResponse {
  cards: CardWithProject[];
}

export async function getDashboardOverview(): Promise<DashboardOverview> {
  const response = await apiClient.get<DashboardOverview>('/dashboard/overview');
  return response.data;
}

export async function getMyCards(): Promise<MyCardsResponse> {
  const response = await apiClient.get<MyCardsResponse>('/dashboard/my-cards');
  return response.data;
}

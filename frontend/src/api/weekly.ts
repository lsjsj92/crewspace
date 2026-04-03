// frontend/src/api/weekly.ts
// 주간 뷰 API 호출 함수

import apiClient from '@/api/client';

export interface MonthlyGoalSubItem {
  title: string;
  card_type: string;
  status: string;
}

export interface MonthlyGoalGroup {
  epic_title: string;
  project_name: string;
  items: MonthlyGoalSubItem[];
}

export interface ActiveProjectItem {
  project_name: string;
  epic_title: string;
}

export interface WeeklyCardItem {
  epic_title: string | null;
  story_title: string | null;
  task_title: string;
  card_type: string;
  due_date: string | null;
  status: string;
  project_name: string;
}

export interface WeeklyViewResponse {
  week_start: string;
  week_end: string;
  month: number;
  monthly_goals: MonthlyGoalGroup[];
  active_projects: ActiveProjectItem[];
  last_week_items: WeeklyCardItem[];
  this_week_items: WeeklyCardItem[];
}

export async function getWeeklyView(weekStart?: string): Promise<WeeklyViewResponse> {
  const params = weekStart ? { week_start: weekStart } : {};
  const response = await apiClient.get<WeeklyViewResponse>('/weekly', { params });
  return response.data;
}

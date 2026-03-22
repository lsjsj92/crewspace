export interface User {
  id: string;
  email: string;
  username: string;
  display_name: string;
  is_active: boolean;
  is_superadmin: boolean;
  created_at: string;
  employee_id?: string;
  organization?: string;
  gw_id?: string;
}

export interface Team {
  id: string;
  name: string;
  description: string;
  is_active: boolean;
  created_at: string;
  member_count?: number;
}

export interface TeamMember {
  id: string;
  team_id: string;
  user_id: string;
  role: 'owner' | 'manager' | 'member' | 'viewer';
  joined_at: string;
  user?: User;
}

export interface TeamDetail extends Team {
  members: TeamMember[];
}

export type ProjectRole = 'manager' | 'member' | 'viewer';

export interface ProjectMember {
  id: string;
  project_id: string;
  user_id: string;
  role: ProjectRole;
  joined_at: string;
  user?: User;
}

export interface Project {
  id: string;
  team_id?: string;
  name: string;
  description: string;
  prefix: string;
  status: 'active' | 'completed' | 'archived';
  start_date: string | null;
  end_date: string | null;
  created_at: string;
}

export interface BoardColumn {
  id: string;
  project_id: string;
  name: string;
  position: number;
  is_end: boolean;
  wip_limit: number | null;
  cards?: Card[];
}

export type CardType = 'epic' | 'story' | 'task' | 'sub_task';
export type CardPriority = 'lowest' | 'low' | 'medium' | 'high' | 'highest';

export interface Card {
  id: string;
  project_id: string;
  column_id: string;
  parent_id: string | null;
  parent?: {
    id: string;
    card_type: CardType;
    card_number: number;
    title: string;
  } | null;
  card_type: CardType;
  card_number: number;
  title: string;
  description: string | null;
  priority: CardPriority;
  position: number;
  start_date: string | null;
  due_date: string | null;
  completed_at: string | null;
  archived_at: string | null;
  created_by: string;
  created_at: string;
  display_number?: string;
  assignees?: CardAssignee[];
  labels?: CardLabel[];
  children?: Card[];
  comments?: Comment[];
}

export interface CardAssignee {
  id: string;
  card_id: string;
  user_id: string;
  assigned_at: string;
  user?: User;
}

export interface Label {
  id: string;
  project_id: string;
  name: string;
  color: string;
}

export interface CardLabel {
  card_id: string;
  label_id: string;
  label?: Label;
}

export interface Comment {
  id: string;
  card_id: string;
  user_id: string;
  content: string;
  created_at: string;
  updated_at: string;
  user?: User;
}

export interface ProjectOutcome {
  id: string;
  project_id: string;
  title: string;
  description: string;
  achieved_at: string | null;
  created_by: string;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  username: string;
  display_name: string;
  password: string;
}

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

export interface TeamSummary {
  id: string;
  name: string;
  project_count: number;
  active_project_count: number;
}

export interface CardWithProject extends Card {
  project_name: string;
}

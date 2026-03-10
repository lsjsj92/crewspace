import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getProjects,
  getRecentProjects,
  getProject,
  createProject,
  getProjectMembers,
  addProjectMember,
  removeProjectMember,
  updateProjectMemberRole,
} from '@/api/projects';
import type { Project, ProjectMember } from '@/types';
import type { ProjectDetail } from '@/api/projects';

export function useMyProjects(status?: string) {
  return useQuery<Project[]>({
    queryKey: ['projects', status],
    queryFn: () => getProjects(status),
  });
}

export function useProject(projectId: string | undefined) {
  return useQuery<ProjectDetail>({
    queryKey: ['project', projectId],
    queryFn: () => getProject(projectId!),
    enabled: !!projectId,
  });
}

export function useRecentProjects() {
  return useQuery<Project[]>({
    queryKey: ['projects', 'recent'],
    queryFn: getRecentProjects,
  });
}

export function useProjectMembers(projectId: string | undefined) {
  return useQuery<ProjectMember[]>({
    queryKey: ['projects', projectId, 'members'],
    queryFn: () => getProjectMembers(projectId!),
    enabled: !!projectId,
  });
}

export function useCreateProject() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: {
      name: string;
      description?: string;
      prefix: string;
      start_date?: string;
      end_date?: string;
      manager_user_id?: string;
    }) => createProject(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
    },
  });
}

export function useAddProjectMember(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { user_id: string; role: string }) =>
      addProjectMember(projectId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects', projectId, 'members'] });
    },
  });
}

export function useUpdateProjectMemberRole(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ userId, role }: { userId: string; role: string }) =>
      updateProjectMemberRole(projectId, userId, { role }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects', projectId, 'members'] });
    },
  });
}

export function useRemoveProjectMember(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (userId: string) => removeProjectMember(projectId, userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects', projectId, 'members'] });
    },
  });
}

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getMyTeams, createTeam as apiCreateTeam, getTeam } from '@/api/teams';
import { getTeamProjects } from '@/api/projects';
import type { Team, TeamDetail, Project } from '@/types';

export function useMyTeams() {
  return useQuery<Team[]>({
    queryKey: ['teams'],
    queryFn: getMyTeams,
    refetchOnWindowFocus: true,
  });
}

export function useTeam(teamId: string | undefined) {
  return useQuery<TeamDetail>({
    queryKey: ['teams', teamId],
    queryFn: () => getTeam(teamId!),
    enabled: !!teamId,
    refetchOnWindowFocus: true,
  });
}

export function useCreateTeam() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: { name: string; description?: string }) => apiCreateTeam(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['teams'] });
    },
  });
}

export function useTeamProjects(teamId: string | undefined, status?: string) {
  return useQuery<Project[]>({
    queryKey: ['teams', teamId, 'projects', status],
    queryFn: () => getTeamProjects(teamId!, status),
    enabled: !!teamId,
  });
}

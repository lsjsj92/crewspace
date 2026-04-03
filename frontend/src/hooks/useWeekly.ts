// frontend/src/hooks/useWeekly.ts
// 주간 뷰 TanStack Query 훅

import { useQuery } from '@tanstack/react-query';
import { getWeeklyView } from '@/api/weekly';
import type { WeeklyViewResponse } from '@/api/weekly';

export function useWeekly(weekStart: string) {
  return useQuery<WeeklyViewResponse>({
    queryKey: ['weekly', weekStart],
    queryFn: () => getWeeklyView(weekStart),
    enabled: !!weekStart,
  });
}

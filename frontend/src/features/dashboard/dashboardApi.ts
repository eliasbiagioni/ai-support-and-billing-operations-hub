import { useQuery } from '@tanstack/react-query';

import { apiRequest } from '@/lib/apiClient';
import type { DashboardSummary } from '@/types/api';

export function useDashboardSummary() {
  return useQuery({
    queryKey: ['dashboard', 'summary'],
    queryFn: ({ signal }) =>
      apiRequest<DashboardSummary>('/api/dashboard/summary', { signal }),
  });
}

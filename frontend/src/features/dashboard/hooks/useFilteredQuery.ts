import { useQuery } from '@tanstack/react-query';
import { useDashboardFilterStore } from '../stores/dashboardFilterStore';

interface UseFilteredQueryOptions<T> {
  baseQueryKey: string[];
  widgetId: string;
  queryFn: (filters: Record<string, any>) => Promise<T>;
  enabled?: boolean;
  staleTime?: number;
}

export function useFilteredQuery<T>({
  baseQueryKey,
  widgetId,
  queryFn,
  enabled = true,
  staleTime = 60 * 1000,
}: UseFilteredQueryOptions<T>) {
  const getFilterForWidget = useDashboardFilterStore((s) => s.getFilterForWidget);
  const filters = getFilterForWidget(widgetId);

  return useQuery({
    queryKey: [...baseQueryKey, filters],
    queryFn: () => queryFn(filters),
    enabled,
    staleTime,
    placeholderData: (prev) => prev,
  });
}

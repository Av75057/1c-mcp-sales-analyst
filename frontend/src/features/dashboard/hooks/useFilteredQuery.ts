import { useMemo } from 'react';
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
  const globalFilters = useDashboardFilterStore((s) => s.globalFilters);
  const crossFilters = useDashboardFilterStore((s) => s.crossFilters);

  const filters = useMemo(() => {
    const result: Record<string, any> = { ...globalFilters };
    for (const cf of crossFilters) {
      if (cf.widgetId !== widgetId) {
        result[cf.field] = cf.value;
      }
    }
    return Object.fromEntries(Object.entries(result).filter(([_, v]) => v !== undefined));
  }, [globalFilters, crossFilters, widgetId]);

  return useQuery({
    queryKey: [...baseQueryKey, filters],
    queryFn: () => queryFn(filters),
    enabled,
    staleTime,
    placeholderData: (prev) => prev,
  });
}

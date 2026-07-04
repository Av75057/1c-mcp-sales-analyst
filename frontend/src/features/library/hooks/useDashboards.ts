import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { dashboardApi } from '../api/dashboardApi';
import type { ListFilters, DashboardCreatePayload, DashboardUpdatePayload } from '@/shared/types/dashboard';

export function useDashboards(filters: ListFilters = {}) {
  return useQuery({
    queryKey: ['dashboards', filters],
    queryFn: () => dashboardApi.list(filters),
    staleTime: 60 * 1000,
  });
}

export function useDashboard(id: string) {
  return useQuery({
    queryKey: ['dashboard', id],
    queryFn: () => dashboardApi.get(id),
    enabled: !!id,
  });
}

export function useCreateDashboard() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: DashboardCreatePayload) => dashboardApi.create(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dashboards'] });
    },
  });
}

export function useUpdateDashboard() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: DashboardUpdatePayload }) =>
      dashboardApi.update(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dashboards'] });
    },
  });
}

export function useDeleteDashboard() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => dashboardApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dashboards'] });
    },
  });
}

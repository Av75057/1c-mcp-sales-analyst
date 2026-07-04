import { api } from '@/shared/lib/api';
import type { Dashboard, DashboardListResponse, ListFilters, DashboardCreatePayload, DashboardUpdatePayload } from '@/shared/types/dashboard';

export const dashboardApi = {
  list: async (filters: ListFilters = {}): Promise<DashboardListResponse> => {
    const { data } = await api.get('/api/v2/dashboards', { params: filters });
    return data;
  },

  get: async (id: string): Promise<Dashboard> => {
    const { data } = await api.get(`/api/v2/dashboards/${id}`);
    return data.dashboard;
  },

  create: async (payload: DashboardCreatePayload): Promise<Dashboard> => {
    const { data } = await api.post('/api/v2/dashboards', payload);
    return data.dashboard;
  },

  update: async (id: string, payload: DashboardUpdatePayload): Promise<Dashboard> => {
    const { data } = await api.patch(`/api/v2/dashboards/${id}`, payload);
    return data.dashboard;
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/api/v2/dashboards/${id}`);
  },

  refresh: async (id: string): Promise<Dashboard> => {
    const { data } = await api.post(`/api/v2/dashboards/${id}/refresh`);
    return data.dashboard;
  },

  export: async (id: string, format: string): Promise<Blob> => {
    const { data } = await api.post(`/api/v3/dashboards/${id}/export`, { format }, { responseType: 'blob' });
    return data;
  },
};

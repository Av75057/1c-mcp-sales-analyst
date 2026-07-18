import { api } from '@/shared/lib/api';
import type { ExecutiveKPIResponse } from '../types/kpi';

export const kpiApi = {
  getExecutiveKPI: async (params: {
    period: string;
    organization?: string;
    include_sparklines?: boolean;
  }): Promise<ExecutiveKPIResponse> => {
    const { data } = await api.get<ExecutiveKPIResponse>('/api/v3/executive-kpi', { params });
    return data;
  },
};

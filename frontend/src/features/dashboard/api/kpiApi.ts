import { api } from '@/shared/lib/api';
import type { ExecutiveKPIResponse } from '../types/kpi';

export const kpiApi = {
  getExecutiveKPI: async (params: {
    period: string;
    organization?: string;
    include_sparklines?: boolean;
    manager?: string;
    category?: string;
    date?: string;
  }): Promise<ExecutiveKPIResponse> => {
    const clean = Object.fromEntries(Object.entries(params).filter(([_, v]) => v !== undefined && v !== ''));
    const { data } = await api.get<ExecutiveKPIResponse>('/api/v3/executive-kpi', { params: clean });
    return data;
  },
};

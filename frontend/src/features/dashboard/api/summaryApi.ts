import { api } from '@/shared/lib/api';

export interface ExecutiveSummary {
  summary_text: string;
  key_insights: string[];
  recommendations: string[];
  anomalies: string[];
  generated_at: string;
  tokens_used: number;
  cache_status: 'hit' | 'miss' | 'fallback';
}

export const summaryApi = {
  generate: async (period: string, organization?: string): Promise<ExecutiveSummary> => {
    const params: Record<string, string> = { period };
    if (organization) params.organization = organization;
    const { data } = await api.get<ExecutiveSummary>('/api/v3/executive-summary', { params });
    return data;
  },
};

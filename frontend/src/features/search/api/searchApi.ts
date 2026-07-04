import { api } from '@/shared/lib/api';

export interface SearchResult {
  dashboard_id: string;
  title: string;
  description: string;
  tags: string;
  rank: number;
}

export interface SearchResponse {
  status: string;
  results: SearchResult[];
  query: string;
  count: number;
}

export const searchApi = {
  search: async (q: string, limit = 20): Promise<SearchResponse> => {
    const { data } = await api.get('/api/v3/search', { params: { q, limit } });
    return data;
  },
};

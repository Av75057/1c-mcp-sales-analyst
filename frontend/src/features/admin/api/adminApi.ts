import { api } from '@/shared/lib/api';

export interface AdminDashboardStats {
  period: { from: string; to: string };
  total_dashboards: number;
  active_dashboards: number;
  total_views: number;
  total_shares: number;
  total_exports: number;
  top_dashboards: { id: string; title: string; views: number }[];
  top_tags: { tag: string; count: number }[];
  chart_types: { type: string; count: number }[];
  feedback_summary: { positive: number; negative: number; total: number; satisfaction_rate: number };
}

export interface User {
  id: string;
  username: string;
  email: string;
  role: string;
  is_active: boolean;
  created_at: string;
}

export interface AuditEntry {
  id: string;
  action: string;
  user_id: string;
  resource_id: string;
  details: string;
  created_at: string;
}

export const adminApi = {
  getStats: async (days = 30): Promise<AdminDashboardStats> => {
    const { data } = await api.get('/api/v3/analytics', { params: { days } });
    return data;
  },

  getUsers: async (): Promise<User[]> => {
    const { data } = await api.get('/admin/users/');
    return data.users || data;
  },

  getAuditLog: async (limit = 50): Promise<AuditEntry[]> => {
    const { data } = await api.get('/admin/audit/', { params: { limit } });
    return data.entries || data;
  },
};

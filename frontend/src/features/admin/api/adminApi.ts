import { api } from '@/shared/lib/api';

export const adminApi = {
  getStats: async (days = 30) => {
    const { data } = await api.get('/api/v3/analytics', { params: { days } });
    return data;
  },
  getAuditLog: async (limit = 100) => {
    const { data } = await api.get('/api/v1/admin/audit', { params: { limit } });
    return data.entries || data;
  },
};

export const multitenantApi = {
  listTenants: () => api.get('/api/v1/admin/tenants').then(r => r.data?.tenants || []),
  createTenant: (body: any) => api.post('/api/v1/admin/tenants', body),
  updateTenant: (id: string, body: any) => api.patch(`/api/v1/admin/tenants/${id}`, body),

  listConnections: (tenantId?: string) =>
    api.get('/api/v1/admin/connections', { params: tenantId ? { tenant_id: tenantId } : {} }).then(r => r.data?.connections || []),
  createConnection: (body: any) => api.post('/api/v1/admin/connections', body),
  updateConnection: (id: string, body: any) => api.patch(`/api/v1/admin/connections/${id}`, body),
  deleteConnection: (id: string) => api.delete(`/api/v1/admin/connections/${id}`),
  testConnection: (id: string) => api.post(`/api/v1/admin/connections/${id}/test`),

  listUsers: () => api.get('/api/v1/admin/users').then(r => r.data?.users || []),
  createUser: (body: any) => api.post('/api/v1/admin/users', body),
  updateUser: (id: string, body: any) => api.patch(`/api/v1/admin/users/${id}`, body),
};

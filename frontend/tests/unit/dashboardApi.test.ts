import { describe, it, expect, vi, beforeEach } from 'vitest';
import { dashboardApi } from '../../src/features/library/api/dashboardApi';

vi.mock('../../src/shared/lib/api', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
}));

import { api } from '../../src/shared/lib/api';

describe('dashboardApi', () => {
  beforeEach(() => { vi.clearAllMocks(); });

  const mockDashboard = {
    id: 'd1', owner_id: 'u1', title: 'Test', charts: [],
    tags: [], is_public: false, is_favorite: false,
    refresh_interval_minutes: 0, view_count: 0,
    created_at: '', updated_at: '',
  };

  it('lists dashboards with filters', async () => {
    (api.get as any).mockResolvedValue({ data: { dashboards: [mockDashboard], total: 1 } });
    const result = await dashboardApi.list({ search: 'test', page: 1 });
    expect(api.get).toHaveBeenCalledWith('/api/v2/dashboards', { params: { search: 'test', page: 1 } });
    expect(result.total).toBe(1);
  });

  it('gets single dashboard', async () => {
    (api.get as any).mockResolvedValue({ data: { dashboard: mockDashboard } });
    const result = await dashboardApi.get('d1');
    expect(api.get).toHaveBeenCalledWith('/api/v2/dashboards/d1');
    expect(result.id).toBe('d1');
  });

  it('creates dashboard', async () => {
    (api.post as any).mockResolvedValue({ data: { dashboard: mockDashboard } });
    const payload = { title: 'New', charts: [] };
    const result = await dashboardApi.create(payload);
    expect(api.post).toHaveBeenCalledWith('/api/v2/dashboards', payload);
    expect(result.title).toBe('Test');
  });

  it('updates dashboard', async () => {
    (api.patch as any).mockResolvedValue({ data: { dashboard: { ...mockDashboard, title: 'Updated' } } });
    const result = await dashboardApi.update('d1', { title: 'Updated' });
    expect(api.patch).toHaveBeenCalledWith('/api/v2/dashboards/d1', { title: 'Updated' });
    expect(result.title).toBe('Updated');
  });

  it('deletes dashboard', async () => {
    (api.delete as any).mockResolvedValue({});
    await dashboardApi.delete('d1');
    expect(api.delete).toHaveBeenCalledWith('/api/v2/dashboards/d1');
  });

  it('refreshes dashboard data', async () => {
    (api.post as any).mockResolvedValue({ data: { dashboard: mockDashboard } });
    const result = await dashboardApi.refresh('d1');
    expect(api.post).toHaveBeenCalledWith('/api/v2/dashboards/d1/refresh');
    expect(result.id).toBe('d1');
  });
});

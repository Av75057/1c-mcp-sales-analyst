import { describe, it, expect, vi, beforeEach } from 'vitest';
import { searchApi } from '../../src/features/search/api/searchApi';

vi.mock('../../src/shared/lib/api', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

import { api } from '../../src/shared/lib/api';

describe('searchApi', () => {
  beforeEach(() => { vi.clearAllMocks(); });

  it('calls /api/v3/search', async () => {
    (api.get as any).mockResolvedValue({ data: { status: 'success', results: [], query: 'test', count: 0 } });
    const result = await searchApi.search('test', 20);
    expect(api.get).toHaveBeenCalledWith('/api/v3/search', { params: { q: 'test', limit: 20 } });
    expect(result.status).toBe('success');
  });

  it('handles empty results', async () => {
    (api.get as any).mockResolvedValue({ data: { status: 'success', results: [], query: 'none', count: 0 } });
    const result = await searchApi.search('none');
    expect(result.results).toEqual([]);
    expect(result.count).toBe(0);
  });

  it('passes limit parameter', async () => {
    (api.get as any).mockResolvedValue({ data: { results: [] } });
    await searchApi.search('test', 5);
    expect(api.get).toHaveBeenCalledWith('/api/v3/search', { params: { q: 'test', limit: 5 } });
  });

  it('defaults limit to 20', async () => {
    (api.get as any).mockResolvedValue({ data: { results: [] } });
    await searchApi.search('default');
    expect(api.get).toHaveBeenCalledWith('/api/v3/search', { params: { q: 'default', limit: 20 } });
  });
});

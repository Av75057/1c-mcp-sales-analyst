import { create } from 'zustand';
import { api } from '@/shared/lib/api';

interface Connection {
  id: string;
  name: string;
  base_url: string;
  health_status: string;
}

interface ConnectionState {
  connections: Connection[];
  activeConnectionId: string | null;
  loading: boolean;
  loadConnections: () => Promise<void>;
  setActiveConnection: (id: string) => void;
  getActiveConnection: () => Connection | null;
}

export const useConnectionStore = create<ConnectionState>((set, get) => ({
  connections: [],
  activeConnectionId: localStorage.getItem('active_connection_id'),
  loading: false,

  loadConnections: async () => {
    set({ loading: true });
    try {
      const r = await api.get('/api/v1/admin/connections', { params: { tenant_id: 'all' } });
      const conns = r.data?.connections || [];
      set({ connections: conns, loading: false });
      // Auto-select first if none selected
      if (!get().activeConnectionId && conns.length > 0) {
        const id = conns[0].id;
        localStorage.setItem('active_connection_id', id);
        set({ activeConnectionId: id });
      }
    } catch { set({ loading: false }); }
  },

  setActiveConnection: (id: string) => {
    localStorage.setItem('active_connection_id', id);
    set({ activeConnectionId: id });
  },

  getActiveConnection: () => {
    const state = get();
    return state.connections.find(c => c.id === state.activeConnectionId) || null;
  },
}));

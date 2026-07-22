import { create } from 'zustand';
import { api } from '@/shared/lib/api';

interface Organization {
  id: string;
  name: string;
  inn?: string;
}

interface OrgState {
  organizations: Organization[];
  activeOrgId: string | null;
  loading: boolean;
  loadOrganizations: (connectionId?: string) => Promise<void>;
  setActiveOrg: (id: string) => void;
}

export const useOrgStore = create<OrgState>((set, get) => ({
  organizations: [],
  activeOrgId: localStorage.getItem('active_org_id'),
  loading: false,

  loadOrganizations: async () => {
    set({ loading: true });
    try {
      const r = await api.get('/api/v1/admin/organizations');
      const orgs = r.data?.organizations || r.data || [];
      set({ organizations: orgs, loading: false });
      if (!get().activeOrgId && orgs.length > 0) {
        const id = orgs[0].id;
        localStorage.setItem('active_org_id', id);
        set({ activeOrgId: id });
      }
    } catch { set({ loading: false }); }
  },

  setActiveOrg: (id: string) => {
    localStorage.setItem('active_org_id', id);
    set({ activeOrgId: id });
  },
}));

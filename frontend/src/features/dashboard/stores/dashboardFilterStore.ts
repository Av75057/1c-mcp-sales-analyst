import { create } from 'zustand';
import type { CrossFilter, FilterStep, GlobalFilters } from '../types/kpi';

export interface DashboardFilterState {
  globalFilters: GlobalFilters;
  crossFilters: CrossFilter[];
  drillDownStack: FilterStep[];
  activeWidgetId: string | null;
  isFiltering: boolean;

  setGlobalFilter: (field: keyof GlobalFilters, value: any) => void;
  setCrossFilter: (filter: CrossFilter) => void;
  removeCrossFilter: (widgetId: string) => void;
  pushDrillDown: (step: FilterStep) => void;
  popDrillDown: () => FilterStep | undefined;
  setActiveWidget: (widgetId: string | null) => void;
  resetAll: () => void;
  resetCrossFilters: () => void;
  getActiveFilters: () => Record<string, any>;
  getFilterForWidget: (widgetId: string) => Record<string, any>;
  hasActiveFilters: () => boolean;
}

let _stepId = 0;
function uid() { return `step_${++_stepId}_${Date.now()}`; }

export const useDashboardFilterStore = create<DashboardFilterState>()(
  (set, get) => ({
    globalFilters: { period: 'this_month' },
    crossFilters: [],
    drillDownStack: [],
    activeWidgetId: null,
    isFiltering: false,

    setGlobalFilter: (field, value) => {
      set({ globalFilters: { ...get().globalFilters, [field]: value }, crossFilters: [], drillDownStack: [], activeWidgetId: null });
    },

    setCrossFilter: (filter) => {
      set((s) => ({
        crossFilters: [...s.crossFilters.filter((f) => f.widgetId !== filter.widgetId), filter],
        activeWidgetId: filter.widgetId,
        drillDownStack: [...s.drillDownStack, { id: uid(), widgetId: filter.widgetId, field: filter.field, value: filter.value, label: filter.label, timestamp: Date.now() }],
      }));
    },

    removeCrossFilter: (widgetId) => {
      set((s) => ({
        crossFilters: s.crossFilters.filter((f) => f.widgetId !== widgetId),
        drillDownStack: s.drillDownStack.filter((st) => st.widgetId !== widgetId),
        activeWidgetId: s.activeWidgetId === widgetId ? null : s.activeWidgetId,
      }));
    },

    pushDrillDown: (step) => set((s) => ({ drillDownStack: [...s.drillDownStack, step] })),

    popDrillDown: () => {
      const state = get();
      const step = state.drillDownStack[state.drillDownStack.length - 1];
      if (step) {
        set((s) => ({
          drillDownStack: s.drillDownStack.slice(0, -1),
          crossFilters: s.crossFilters.filter((f) => f.widgetId !== step.widgetId),
        }));
      }
      return step;
    },

    setActiveWidget: (widgetId) => set({ activeWidgetId: widgetId }),

    resetAll: () => set({ globalFilters: { period: 'this_month' }, crossFilters: [], drillDownStack: [], activeWidgetId: null }),

    resetCrossFilters: () => set({ crossFilters: [], drillDownStack: [], activeWidgetId: null }),

    getActiveFilters: () => {
      const state = get();
      const filters: Record<string, any> = { ...state.globalFilters };
      for (const cf of state.crossFilters) filters[cf.field] = cf.value;
      return Object.fromEntries(Object.entries(filters).filter(([_, v]) => v !== undefined));
    },

    getFilterForWidget: (widgetId) => {
      const state = get();
      const filters: Record<string, any> = { ...state.globalFilters };
      for (const cf of state.crossFilters) if (cf.widgetId !== widgetId) filters[cf.field] = cf.value;
      return Object.fromEntries(Object.entries(filters).filter(([_, v]) => v !== undefined));
    },

    hasActiveFilters: () => get().crossFilters.length > 0,
  })
);

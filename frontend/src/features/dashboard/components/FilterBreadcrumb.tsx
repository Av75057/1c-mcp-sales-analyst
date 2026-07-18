import React from 'react';
import { ChevronRight, Home } from 'lucide-react';
import { useDashboardFilterStore } from '../stores/dashboardFilterStore';

export const FilterBreadcrumb: React.FC = React.memo(() => {
  const drillDownStack = useDashboardFilterStore((s) => s.drillDownStack);
  const popDrillDown = useDashboardFilterStore((s) => s.popDrillDown);
  const resetCrossFilters = useDashboardFilterStore((s) => s.resetCrossFilters);

  if (drillDownStack.length === 0) return null;

  return (
    <nav className="flex items-center gap-1 text-sm px-4 py-2 rounded-lg mb-4 overflow-x-auto"
      style={{ backgroundColor: 'var(--bg-card-hover)' }}>
      <button onClick={resetCrossFilters} className="flex items-center gap-1 whitespace-nowrap" style={{ color: 'var(--brand)' }}>
        <Home className="w-3.5 h-3.5" /> Все данные
      </button>
      {drillDownStack.map((step, idx) => (
        <React.Fragment key={step.id}>
          <ChevronRight className="w-3.5 h-3.5 flex-shrink-0" style={{ color: 'var(--text-muted)' }} />
          <button onClick={() => {
            for (let i = drillDownStack.length - 1; i > idx; i--) popDrillDown();
          }}
            className="whitespace-nowrap px-2 py-0.5 rounded text-xs font-medium transition-colors"
            style={idx === drillDownStack.length - 1 ? { backgroundColor: 'var(--bg-active)', color: 'var(--text-primary)' } : { color: 'var(--text-secondary)' }}>
            {step.label}
          </button>
        </React.Fragment>
      ))}
      {drillDownStack.length > 1 && (
        <button onClick={popDrillDown} className="ml-auto text-xs" style={{ color: 'var(--text-muted)' }}>← Назад</button>
      )}
    </nav>
  );
});

FilterBreadcrumb.displayName = 'FilterBreadcrumb';

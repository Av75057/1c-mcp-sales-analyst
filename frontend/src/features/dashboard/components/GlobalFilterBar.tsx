import React from 'react';
import { RotateCcw, Filter } from 'lucide-react';
import { useDashboardFilterStore } from '../stores/dashboardFilterStore';

const PERIODS = [
  { value: 'today', label: 'Сегодня' }, { value: 'yesterday', label: 'Вчера' },
  { value: 'this_week', label: 'Эта неделя' }, { value: 'last_week', label: 'Прошлая неделя' },
  { value: 'this_month', label: 'Этот месяц' }, { value: 'last_month', label: 'Прошлый месяц' },
  { value: 'this_quarter', label: 'Этот квартал' }, { value: 'this_year', label: 'Этот год' },
];

export const GlobalFilterBar: React.FC = React.memo(() => {
  const globalFilters = useDashboardFilterStore((s) => s.globalFilters);
  const crossFilters = useDashboardFilterStore((s) => s.crossFilters);
  const setGlobalFilter = useDashboardFilterStore((s) => s.setGlobalFilter);
  const removeCrossFilter = useDashboardFilterStore((s) => s.removeCrossFilter);
  const resetCrossFilters = useDashboardFilterStore((s) => s.resetCrossFilters);

  return (
    <div className="sticky top-0 z-30 border-b px-4 py-2" style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border)' }}>
      <div className="flex items-center gap-2 flex-wrap max-w-7xl mx-auto">
        <select value={globalFilters.period} onChange={(e) => setGlobalFilter('period', e.target.value)}
          className="px-2.5 py-1.5 text-xs font-medium rounded-md border"
          style={{ backgroundColor: 'var(--bg-input)', borderColor: 'var(--border)', color: 'var(--text-primary)' }}>
          {PERIODS.map((p) => <option key={p.value} value={p.value}>{p.label}</option>)}
        </select>

        {crossFilters.length > 0 && (
          <>
            <Filter className="w-3.5 h-3.5" style={{ color: 'var(--brand)' }} />
            {crossFilters.map((cf) => (
              <span key={cf.widgetId} onClick={() => removeCrossFilter(cf.widgetId)}
                className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full cursor-pointer transition-colors"
                style={{ backgroundColor: 'var(--bg-active)', color: 'var(--text-primary)' }}>
                {cf.label} ✕
              </span>
            ))}
          </>
        )}

        {crossFilters.length > 0 && (
          <button onClick={resetCrossFilters}
            className="text-xs flex items-center gap-1 px-2 py-1 rounded transition-colors"
            style={{ color: 'var(--text-muted)' }}>
            <RotateCcw className="w-3 h-3" /> Сбросить
          </button>
        )}
      </div>
    </div>
  );
});

GlobalFilterBar.displayName = 'GlobalFilterBar';

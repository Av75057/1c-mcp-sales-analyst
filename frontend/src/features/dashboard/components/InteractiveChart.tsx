import React, { useCallback } from 'react';
import { EChartsWrapper } from '@/shared/components/charts/EChartsWrapper';
import { useDashboardFilterStore } from '../stores/dashboardFilterStore';
import type { EChartsOption } from 'echarts';

interface InteractiveChartProps {
  widgetId: string;
  option: EChartsOption;
  height?: number;
  filterField: string;
  title?: string;
}

export const InteractiveChart: React.FC<InteractiveChartProps> = React.memo(({
  widgetId, option, height = 300, filterField, title,
}) => {
  const setCrossFilter = useDashboardFilterStore((s) => s.setCrossFilter);
  const activeWidgetId = useDashboardFilterStore((s) => s.activeWidgetId);
  const crossFilters = useDashboardFilterStore((s) => s.crossFilters);
  const isActive = activeWidgetId === widgetId;
  const isDimmed = crossFilters.length > 0 && !isActive;

  const handleClick = useCallback((params: any) => {
    const value = params.name || params.value;
    if (value === undefined) return;
    setCrossFilter({ widgetId, field: filterField, value, label: `${title || filterField}: ${value}` });
  }, [widgetId, filterField, title, setCrossFilter]);

  return (
    <div className={`rounded-xl border p-4 transition-all duration-200 ${isActive ? 'ring-2' : ''} ${isDimmed ? 'opacity-50' : ''}`}
      style={{ backgroundColor: 'var(--bg-card)', borderColor: isActive ? 'var(--brand)' : 'var(--border)' }}>
      {title && <h3 className="text-sm font-semibold mb-3" style={{ color: 'var(--text-primary)' }}>{title}</h3>}
      <EChartsWrapper option={{ ...option, emphasis: { focus: 'series' } as any }} height={height} onEvents={{ click: handleClick }} />
      {isActive && (
        <div className="mt-2 text-xs text-center" style={{ color: 'var(--brand)' }}>🔍 Фильтр: {filterField}</div>
      )}
    </div>
  );
});

InteractiveChart.displayName = 'InteractiveChart';

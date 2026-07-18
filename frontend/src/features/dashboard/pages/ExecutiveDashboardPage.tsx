import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { EChartsWrapper } from '@/shared/components/charts/EChartsWrapper';
import type { EChartsOption } from 'echarts';
import { KPICard } from '@/features/dashboard/components/KPICard';
import { KPISkeleton } from '@/features/dashboard/components/KPISkeleton';
import { AISummary } from '@/features/dashboard/components/AISummary';
import { GlobalFilterBar } from '@/features/dashboard/components/GlobalFilterBar';
import { FilterBreadcrumb } from '@/features/dashboard/components/FilterBreadcrumb';
import { InteractiveChart } from '@/features/dashboard/components/InteractiveChart';
import { kpiApi } from '@/features/dashboard/api/kpiApi';
import { useDashboardFilterStore } from '@/features/dashboard/stores/dashboardFilterStore';

function sparklineOption(data: { date: string; value: number }[], trendPercent: number): EChartsOption {
  const color = trendPercent >= 0 ? '#10b981' : '#ef4444';
  return {
    backgroundColor: 'transparent',
    grid: { left: 48, right: 8, top: 8, bottom: 20 },
    xAxis: { type: 'category', show: true, data: data.map(d => d.date), axisLine: { lineStyle: { color: '#e5e7eb' } }, axisTick: { lineStyle: { color: '#e5e7eb' } }, axisLabel: { fontSize: 10, color: '#9ca3af' }, splitLine: { show: false } },
    yAxis: { type: 'value', show: true, min: 'dataMin' as any, axisLine: { show: false }, axisTick: { show: false }, axisLabel: { fontSize: 10, color: '#9ca3af' }, splitLine: { lineStyle: { color: '#f3f4f6', type: 'dashed' as const } } },
    series: [{ type: 'line', data: data.map(d => d.value), smooth: true, showSymbol: false, lineStyle: { width: 2.5, color }, itemStyle: { color }, areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: `${color}1A` }, { offset: 1, color: `${color}00` }] } } }],
    tooltip: { show: false },
  };
}

export default function ExecutiveDashboardPage() {
  const period = useDashboardFilterStore((s) => s.globalFilters.period);

  const { data, isLoading, isError } = useQuery({
    queryKey: ['executive_kpi', period],
    queryFn: () => kpiApi.getExecutiveKPI({ period, include_sparklines: true }),
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
  });

  const mockBarOption: EChartsOption = {
    backgroundColor: 'transparent',
    grid: { left: 50, right: 16, top: 16, bottom: 24 },
    xAxis: { type: 'category', data: ['Иванов', 'Петров', 'Сидоров', 'Кузнецов'], axisLabel: { color: '#9ca3af' } },
    yAxis: { type: 'value', axisLabel: { color: '#9ca3af' }, splitLine: { lineStyle: { color: '#f3f4f6' } } },
    series: [{ type: 'bar', data: [120, 200, 150, 80], itemStyle: { color: '#3b82f6' } }],
  };

  return (
    <div style={{ backgroundColor: 'var(--bg-page)', minHeight: '100vh' }}>
      <GlobalFilterBar />
      <FilterBreadcrumb />

      <div className="p-4 sm:p-6 lg:p-8 space-y-6 max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl sm:text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>Панель руководителя</h1>
            <p className="text-sm mt-1" style={{ color: 'var(--text-secondary)' }}>
              {data?.period_label || 'Загрузка...'}
            </p>
          </div>
        </div>

        {isError && (
          <div className="p-4 rounded-xl text-sm" style={{ backgroundColor: 'var(--bg-card)', border: '1px solid var(--border)', color: 'var(--text-primary)' }}>
            ❌ Не удалось загрузить показатели
          </div>
        )}

        {/* AI Summary */}
        {data && <AISummary period={period} />}

        {/* KPI Cards */}
        {isLoading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
            {[1, 2, 3, 4].map(i => <KPISkeleton key={i} />)}
          </div>
        ) : data ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
            <KPICard widgetId="kpi-revenue" title="Выручка" metric={data.revenue} unit="currency" filterField="period" filterValue={period} />
            <KPICard widgetId="kpi-profit" title="Валовая прибыль" metric={data.profit} unit="currency" />
            <KPICard widgetId="kpi-orders" title="Заказы" metric={data.orders_count} unit="number" />
            <KPICard widgetId="kpi-margin" title="Маржинальность" metric={data.margin_percent} unit="percent" />
          </div>
        ) : null}

        {/* Charts row */}
        {data?.sparklines?.revenue?.length > 0 && (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
            <div className="rounded-xl border p-4" style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border)' }}>
              <div className="text-xs font-semibold uppercase tracking-wider mb-2" style={{ color: 'var(--text-secondary)' }}>📈 Выручка (по дням)</div>
              <EChartsWrapper option={sparklineOption(data.sparklines.revenue, data.revenue.trend_percent)} height={120} />
            </div>
            <InteractiveChart widgetId="chart-managers" title="Топ менеджеров" option={mockBarOption} filterField="manager" height={240} />
          </div>
        )}

        {/* Top manager */}
        {data?.top_manager?.name && (
          <div className="rounded-xl border p-4" style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border)' }}>
            <div className="text-xs font-semibold uppercase tracking-wider mb-2" style={{ color: 'var(--text-secondary)' }}>🏆 Топ-менеджер</div>
            <div className="text-lg font-bold" style={{ color: 'var(--text-primary)' }}>{data.top_manager.name}</div>
            <div className="text-2xl font-bold text-emerald-600 mt-1">
              {new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB', maximumFractionDigits: 0 }).format(data.top_manager.revenue)}
            </div>
            <div className="text-xs mt-0.5" style={{ color: 'var(--text-muted)' }}>выручка за период</div>
          </div>
        )}

        {/* Cache status */}
        {data && (
          <div className="text-xs flex items-center gap-2" style={{ color: 'var(--text-muted)' }}>
            <span className={`inline-block w-2 h-2 rounded-full ${data.cache_status === 'hit' ? 'bg-emerald-400' : 'bg-blue-400'}`} />
            {data.cache_status === 'hit' ? 'Из кэша' : 'Из 1С'}
          </div>
        )}
      </div>
    </div>
  );
}

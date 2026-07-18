import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { EChartsWrapper } from '@/shared/components/charts/EChartsWrapper';
import type { EChartsOption } from 'echarts';
import { KPICard } from '@/features/dashboard/components/KPICard';
import { KPISkeleton } from '@/features/dashboard/components/KPISkeleton';
import { AISummary } from '@/features/dashboard/components/AISummary';
import { kpiApi } from '@/features/dashboard/api/kpiApi';

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

const PERIODS = [
  { value: 'today', label: 'Сегодня' },
  { value: 'yesterday', label: 'Вчера' },
  { value: 'this_week', label: 'Эта неделя' },
  { value: 'last_week', label: 'Прошлая неделя' },
  { value: 'this_month', label: 'Этот месяц' },
  { value: 'last_month', label: 'Прошлый месяц' },
  { value: 'this_quarter', label: 'Этот квартал' },
  { value: 'this_year', label: 'Этот год' },
];

export default function ExecutiveDashboardPage() {
  const [period, setPeriod] = useState('this_month');

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['executive_kpi', period],
    queryFn: () => kpiApi.getExecutiveKPI({ period, include_sparklines: true }),
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
  });

  return (
    <div className="p-4 sm:p-6 lg:p-8" style={{ backgroundColor: 'var(--bg-page)', minHeight: '100vh' }}>
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>Панель руководителя</h1>
          <p className="text-sm mt-1" style={{ color: 'var(--text-secondary)' }}>
            {data?.period_label || 'Загрузка...'}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex rounded-lg p-0.5" style={{ backgroundColor: 'var(--bg-card-hover)' }}>
            {PERIODS.slice(0, 3).map(p => (
              <button key={p.value} onClick={() => setPeriod(p.value)}
                className="px-2.5 sm:px-3 py-1.5 text-xs font-medium rounded-md transition-colors whitespace-nowrap"
                style={period === p.value ? { backgroundColor: 'var(--bg-card)', color: 'var(--text-primary)', boxShadow: '0 1px 2px rgba(0,0,0,0.1)' } : { color: 'var(--text-secondary)' }}>
                {p.label}
              </button>
            ))}
            <select value={period} onChange={e => setPeriod(e.target.value)}
              className="px-2.5 py-1.5 text-xs font-medium rounded-md bg-transparent cursor-pointer outline-none"
              style={{ color: 'var(--text-secondary)' }}>
              {PERIODS.slice(3).map(p => (
                <option key={p.value} value={p.value}>{p.label}</option>
              ))}
            </select>
          </div>
          <button onClick={() => refetch()}
            className="p-2 rounded-lg border transition-colors"
            style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border)', color: 'var(--text-muted)' }}>
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>
          </button>
        </div>
      </div>

      {/* Error */}
      {isError && (
        <div className="p-4 mb-4 rounded-xl text-sm" style={{ backgroundColor: 'var(--bg-card)', border: '1px solid var(--border)', color: 'var(--text-primary)' }}>
          ❌ Не удалось загрузить показатели
        </div>
      )}

      {/* AI Summary */}
      {data && <div className="mb-6"><AISummary period={period} /></div>}

      {/* KPIs */}
      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
          {[1, 2, 3, 4].map(i => <KPISkeleton key={i} />)}
        </div>
      ) : data ? (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 mb-6">
            <KPICard title="Выручка" metric={data.revenue} unit="currency" />
            <KPICard title="Валовая прибыль" metric={data.profit} unit="currency" />
            <KPICard title="Количество заказов" metric={data.orders_count} unit="number" />
            <KPICard title="Средняя маржинальность" metric={data.margin_percent} unit="percent" />
          </div>

          {/* Charts row */}
          {data.sparklines?.revenue?.length > 0 && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4 mb-6">
              <div className="rounded-xl border p-4" style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border)' }}>
                <div className="text-xs font-semibold uppercase tracking-wider mb-2" style={{ color: 'var(--text-secondary)' }}>📈 Выручка (по дням)</div>
                <EChartsWrapper option={sparklineOption(data.sparklines.revenue, data.revenue.trend_percent)} height={120} />
              </div>
              <div className="rounded-xl border p-4" style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border)' }}>
                <div className="text-xs font-semibold uppercase tracking-wider mb-2" style={{ color: 'var(--text-secondary)' }}>📈 Прибыль (по дням)</div>
                <EChartsWrapper option={sparklineOption(data.sparklines.revenue.map(d => ({ date: d.date, value: d.value * (data.margin_percent.current / 100) })), data.profit.trend_percent)} height={120} />
              </div>
            </div>
          )}

          {/* Top manager + Footer */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4 mb-6">
            <div className="rounded-xl border p-4" style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border)' }}>
              <div className="text-xs font-semibold uppercase tracking-wider mb-2" style={{ color: 'var(--text-secondary)' }}>🏆 Топ-менеджер</div>
              {data.top_manager?.name ? (
                <>
                  <div className="text-lg font-bold" style={{ color: 'var(--text-primary)' }}>{data.top_manager.name}</div>
                  <div className="text-2xl font-bold text-emerald-600 mt-1">
                    {new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB', maximumFractionDigits: 0 }).format(data.top_manager.revenue)}
                  </div>
                  <div className="text-xs mt-0.5" style={{ color: 'var(--text-muted)' }}>выручка за период</div>
                </>
              ) : (
                <div className="text-sm py-2" style={{ color: 'var(--text-muted)' }}>Нет данных</div>
              )}
            </div>
            <div className="rounded-xl border p-4" style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border)' }}>
              <div className="text-xs font-semibold uppercase tracking-wider mb-2" style={{ color: 'var(--text-secondary)' }}>⚡ Статус</div>
              <div className="flex items-center gap-2 text-sm" style={{ color: 'var(--text-secondary)' }}>
                <span className={`inline-block w-2 h-2 rounded-full ${data.cache_status === 'hit' ? 'bg-emerald-400' : 'bg-blue-400'}`} />
                {data.cache_status === 'hit' ? 'Из кэша (мгновенно)' : 'Из 1С'}
              </div>
              <div className="text-xs mt-2" style={{ color: 'var(--text-muted)' }}>
                Период: {data.period_label}
              </div>
            </div>
          </div>
        </>
      ) : null}
    </div>
  );
}

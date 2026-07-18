import { useState, useEffect, useCallback } from 'react';
import { api } from '@/shared/lib/api';
import { EChartsWrapper } from '@/shared/components/charts/EChartsWrapper';
import { formatCurrency, formatNumber } from '@/shared/lib/utils';
import type { EChartsOption } from 'echarts';

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

interface MetricData {
  current: number;
  previous: number;
  trend_percent: number;
}

interface KpiResponse {
  period_label: string;
  revenue: MetricData;
  profit: MetricData;
  orders_count: MetricData;
  margin_percent: MetricData;
  top_manager: { name: string; revenue: number };
  sparklines: Record<string, { date: string; value: number }[]>;
  cache_status: string;
}

function TrendBadge({ value }: { value: number }) {
  if (value === 0) return <span className="text-xs font-semibold text-gray-400 bg-gray-100 px-2 py-0.5 rounded-full">— 0%</span>;
  const isUp = value > 0;
  return (
    <span className={`text-xs font-semibold px-2 py-0.5 rounded-full inline-flex items-center gap-0.5 ${isUp ? 'text-emerald-700 bg-emerald-50' : 'text-red-700 bg-red-50'}`}>
      {isUp ? '▲' : '▼'} {Math.abs(value).toFixed(1)}%
    </span>
  );
}

function MetricCard({ title, metric, format = 'currency', icon, color }: {
  title: string; metric: MetricData; format?: 'currency' | 'number' | 'percent'; icon: string; color: string;
}) {
  const fmt = (n: number) => {
    if (format === 'currency') return formatCurrency(n);
    if (format === 'percent') return `${n.toFixed(1)}%`;
    return formatNumber(n);
  };

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm hover:shadow-md transition-shadow duration-200">
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">{title}</span>
        <span className="text-lg">{icon}</span>
      </div>
      <div className="text-3xl font-bold text-gray-900 mb-1">{fmt(metric.current)}</div>
      <div className="flex items-center gap-2">
        <TrendBadge value={metric.trend_percent} />
        <span className="text-xs text-gray-400">vs {fmt(metric.previous)}</span>
      </div>
    </div>
  );
}

function SparklineChart({ data, color }: { data: { date: string; value: number }[]; color: string }) {
  const option: EChartsOption = {
    backgroundColor: 'transparent',
    grid: { left: 48, right: 8, top: 8, bottom: 20 },
    xAxis: {
      type: 'category', show: true,
      data: data.map(d => d.date),
      axisLine: { lineStyle: { color: '#e5e7eb' } },
      axisTick: { lineStyle: { color: '#e5e7eb' } },
      axisLabel: { fontSize: 10, color: '#9ca3af', rotate: 0 },
      splitLine: { show: false },
    },
    yAxis: {
      type: 'value', show: true, min: 'dataMin' as any,
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { fontSize: 10, color: '#9ca3af' },
      splitLine: { lineStyle: { color: '#f3f4f6', type: 'dashed' as const } },
    },
    series: [{
      type: 'line', data: data.map(d => d.value), smooth: true, showSymbol: false,
      lineStyle: { width: 2.5, color },
      itemStyle: { color },
      areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: `${color}1A` }, { offset: 1, color: `${color}00` }] } },
    }],
    tooltip: { show: false },
  };
  return <EChartsWrapper option={option} height={120} />;
}

function SparklineCard({ title, data, color, mainValue, subtitle }: {
  title: string; data: { date: string; value: number }[]; color: string; mainValue: number; subtitle?: string;
}) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
      <div className="flex items-center justify-between mb-2">
        <div>
          <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider">{title}</div>
          <div className="text-lg font-bold text-gray-900">{formatCurrency(mainValue)}</div>
        </div>
        {subtitle && <div className="text-xs text-gray-400">{subtitle}</div>}
      </div>
      <SparklineChart data={data} color={color} />
    </div>
  );
}

function Skeleton() {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-4 gap-5">
        {[1, 2, 3, 4].map(i => (
          <div key={i} className="h-32 bg-gray-100 rounded-xl animate-pulse" />
        ))}
      </div>
      <div className="grid grid-cols-3 gap-5">
        {[1, 2, 3].map(i => (
          <div key={i} className="h-40 bg-gray-100 rounded-xl animate-pulse" />
        ))}
      </div>
    </div>
  );
}

export default function ExecutiveDashboardPage() {
  const [period, setPeriod] = useState('this_month');
  const [data, setData] = useState<KpiResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchKpi = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get<KpiResponse>('/api/v3/executive-kpi', {
        params: { period, include_sparklines: true },
      });
      setData(res.data);
    } catch (e: any) {
      setError(e?.response?.data?.detail || e?.message || 'Ошибка загрузки');
    } finally {
      setLoading(false);
    }
  }, [period]);

  useEffect(() => { fetchKpi(); }, [fetchKpi]);

  return (
    <div className="min-h-screen bg-gray-50 px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Панель руководителя</h1>
            <p className="text-sm text-gray-500 mt-1">{data?.period_label || 'Загрузка...'}</p>
          </div>
          <div className="flex items-center gap-2">
            <div className="flex bg-gray-100 rounded-lg p-0.5">
              {PERIODS.slice(0, 4).map(p => (
                <button key={p.value} onClick={() => setPeriod(p.value)}
                  className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${period === p.value ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}>
                  {p.label}
                </button>
              ))}
              <div className="relative">
                <select value={period} onChange={e => setPeriod(e.target.value)}
                  className="appearance-none px-3 py-1.5 text-xs font-medium rounded-md bg-transparent text-gray-500 hover:text-gray-700 cursor-pointer outline-none">
                  {PERIODS.slice(4).map(p => (
                    <option key={p.value} value={p.value}>{p.label}</option>
                  ))}
                </select>
              </div>
            </div>
            <button onClick={fetchKpi}
              className="p-2 bg-white border border-gray-200 rounded-lg text-gray-500 hover:text-gray-700 hover:border-gray-300 transition-colors shadow-sm">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>
            </button>
          </div>
        </div>
      </div>

      {error && (
        <div className="p-4 mb-6 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm flex items-center gap-2">
          <svg className="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
          {error}
        </div>
      )}

      {loading && !data && <Skeleton />}

      {data && (
        <>
          {/* KPI Cards */}
          <div className="grid grid-cols-4 gap-5 mb-6">
            <MetricCard title="Выручка" metric={data.revenue} icon="💰" color="#3b82f6" />
            <MetricCard title="Валовая прибыль" metric={data.profit} icon="📈" color="#10b981" />
            <MetricCard title="Заказы" metric={data.orders_count} format="number" icon="📦" color="#f59e0b" />
            <MetricCard title="Маржа" metric={data.margin_percent} format="percent" icon="🎯" color="#8b5cf6" />
          </div>

          {/* Bottom row: sparklines + top manager */}
          <div className="grid grid-cols-3 gap-5 mb-6">
            {data.sparklines?.revenue?.length > 0 ? (
              <SparklineCard title="Выручка (по дням)" data={data.sparklines.revenue} color="#3b82f6" mainValue={data.revenue.current} subtitle="Динамика за период" />
            ) : (
              <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm flex items-center justify-center text-gray-400 text-sm">Нет данных за период</div>
            )}
            {data.sparklines?.revenue?.length > 0 ? (
              <SparklineCard title="Прибыль (по дням)" data={data.sparklines.revenue.map(d => ({ date: d.date, value: d.value * (data.margin_percent.current / 100) }))} color="#10b981" mainValue={data.profit.current} subtitle="На основе маржи" />
            ) : (
              <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm flex items-center justify-center text-gray-400 text-sm">Нет данных за период</div>
            )}
            <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
              <div className="flex items-center gap-2 mb-3">
                <span className="text-lg">🏆</span>
                <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Топ-менеджер</span>
              </div>
              {data.top_manager?.name ? (
                <>
                  <div className="text-xl font-bold text-gray-900">{data.top_manager.name}</div>
                  <div className="text-2xl font-bold text-emerald-600 mt-1">{formatCurrency(data.top_manager.revenue)}</div>
                  <div className="text-xs text-gray-400 mt-0.5">выручка за период</div>
                </>
              ) : (
                <div className="text-sm text-gray-400 py-2">Нет данных</div>
              )}
            </div>
          </div>

          {/* Footer info */}
          <div className="flex items-center gap-4 text-xs text-gray-400">
            <span className="flex items-center gap-1">
              <span className={`inline-block w-2 h-2 rounded-full ${data.cache_status === 'hit' ? 'bg-emerald-400' : 'bg-blue-400'}`} />
              {data.cache_status === 'hit' ? 'Из кэша (мгновенно)' : 'Из 1С'}
            </span>
          </div>
        </>
      )}
    </div>
  );
}

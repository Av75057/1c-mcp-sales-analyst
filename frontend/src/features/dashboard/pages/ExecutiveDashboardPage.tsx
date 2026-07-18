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
  if (value === 0) return <span className="text-xs font-semibold px-2 py-0.5 rounded-full"
    style={{ color: 'var(--text-muted)', backgroundColor: 'var(--bg-card-hover)' }}>— 0%</span>;
  const isUp = value > 0;
  return (
    <span className={`text-xs font-semibold px-2 py-0.5 rounded-full inline-flex items-center gap-0.5 ${isUp ? 'text-emerald-700 bg-emerald-50' : 'text-red-700 bg-red-50'}`}>
      {isUp ? '▲' : '▼'} {Math.abs(value).toFixed(1)}%
    </span>
  );
}

function MetricCard({ title, metric, format = 'currency', icon }: {
  title: string; metric: MetricData; format?: 'currency' | 'number' | 'percent'; icon: string;
}) {
  const fmt = (n: number) => {
    if (format === 'currency') return formatCurrency(n);
    if (format === 'percent') return `${n.toFixed(1)}%`;
    return formatNumber(n);
  };

  return (
    <div className="rounded-xl border p-5 shadow-sm hover:shadow-md transition-shadow duration-200"
      style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border)' }}>
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--text-secondary)' }}>{title}</span>
        <span className="text-lg">{icon}</span>
      </div>
      <div className="text-3xl font-bold mb-1" style={{ color: 'var(--text-primary)' }}>{fmt(metric.current)}</div>
      <div className="flex items-center gap-2">
        <TrendBadge value={metric.trend_percent} />
        <span className="text-xs" style={{ color: 'var(--text-muted)' }}>vs {fmt(metric.previous)}</span>
      </div>
    </div>
  );
}

function SparklineChart({ data, color }: { data: { date: string; value: number }[]; color: string }) {
  const axisColor = 'var(--text-muted)';
  const splitColor = 'var(--border)';
  const option: EChartsOption = {
    backgroundColor: 'transparent',
    grid: { left: 48, right: 8, top: 8, bottom: 20 },
    xAxis: {
      type: 'category', show: true, data: data.map(d => d.date),
      axisLine: { lineStyle: { color: splitColor } },
      axisTick: { lineStyle: { color: splitColor } },
      axisLabel: { fontSize: 10, color: axisColor, rotate: 0 },
      splitLine: { show: false },
    },
    yAxis: {
      type: 'value', show: true, min: 'dataMin' as any,
      axisLine: { show: false }, axisTick: { show: false },
      axisLabel: { fontSize: 10, color: axisColor },
      splitLine: { lineStyle: { color: splitColor, type: 'dashed' as const } },
    },
    series: [{
      type: 'line', data: data.map(d => d.value), smooth: true, showSymbol: false,
      lineStyle: { width: 2.5, color }, itemStyle: { color },
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
    <div className="rounded-xl border p-5 shadow-sm"
      style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border)' }}>
      <div className="flex items-center justify-between mb-2">
        <div>
          <div className="text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--text-secondary)' }}>{title}</div>
          <div className="text-lg font-bold" style={{ color: 'var(--text-primary)' }}>{formatCurrency(mainValue)}</div>
        </div>
        {subtitle && <div className="text-xs" style={{ color: 'var(--text-muted)' }}>{subtitle}</div>}
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
          <div key={i} className="h-32 rounded-xl animate-pulse" style={{ backgroundColor: 'var(--skeleton)' }} />
        ))}
      </div>
      <div className="grid grid-cols-3 gap-5">
        {[1, 2, 3].map(i => (
          <div key={i} className="h-40 rounded-xl animate-pulse" style={{ backgroundColor: 'var(--skeleton)' }} />
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
    <div className="px-8 py-8" style={{ backgroundColor: 'var(--bg-page)', minHeight: '100vh' }}>
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>Панель руководителя</h1>
            <p className="text-sm mt-1" style={{ color: 'var(--text-secondary)' }}>{data?.period_label || 'Загрузка...'}</p>
          </div>
          <div className="flex items-center gap-2">
            <div className="flex rounded-lg p-0.5" style={{ backgroundColor: 'var(--bg-card-hover)' }}>
              {PERIODS.slice(0, 4).map(p => (
                <button key={p.value} onClick={() => setPeriod(p.value)}
                  className="px-3 py-1.5 text-xs font-medium rounded-md transition-colors"
                  style={period === p.value ? { backgroundColor: 'var(--bg-card)', color: 'var(--text-primary)', boxShadow: '0 1px 2px rgba(0,0,0,0.1)' } : { color: 'var(--text-secondary)' }}>
                  {p.label}
                </button>
              ))}
              <div className="relative">
                <select value={period} onChange={e => setPeriod(e.target.value)}
                  className="appearance-none px-3 py-1.5 text-xs font-medium rounded-md bg-transparent cursor-pointer outline-none"
                  style={{ color: 'var(--text-secondary)' }}>
                  {PERIODS.slice(4).map(p => (
                    <option key={p.value} value={p.value}>{p.label}</option>
                  ))}
                </select>
              </div>
            </div>
            <button onClick={fetchKpi}
              className="p-2 rounded-lg border transition-colors shadow-sm"
              style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border)', color: 'var(--text-muted)' }}>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>
            </button>
          </div>
        </div>
      </div>

      {error && (
        <div className="p-4 mb-6 rounded-xl text-sm flex items-center gap-2"
          style={{ backgroundColor: 'var(--bg-card)', border: '1px solid var(--border)', color: 'var(--text-primary)' }}>
          <svg className="w-5 h-5 flex-shrink-0 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
          {error}
        </div>
      )}

      {loading && !data && <Skeleton />}

      {data && (
        <>
          <div className="grid grid-cols-4 gap-5 mb-6">
            <MetricCard title="Выручка" metric={data.revenue} icon="💰" />
            <MetricCard title="Валовая прибыль" metric={data.profit} icon="📈" />
            <MetricCard title="Заказы" metric={data.orders_count} format="number" icon="📦" />
            <MetricCard title="Маржа" metric={data.margin_percent} format="percent" icon="🎯" />
          </div>

          <div className="grid grid-cols-3 gap-5 mb-6">
            {data.sparklines?.revenue?.length > 0 ? (
              <SparklineCard title="Выручка (по дням)" data={data.sparklines.revenue} color="#3b82f6" mainValue={data.revenue.current} subtitle="Динамика за период" />
            ) : (
              <div className="rounded-xl border p-5 shadow-sm flex items-center justify-center text-sm"
                style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border)', color: 'var(--text-muted)' }}>Нет данных за период</div>
            )}
            {data.sparklines?.revenue?.length > 0 ? (
              <SparklineCard title="Прибыль (по дням)" data={data.sparklines.revenue.map(d => ({ date: d.date, value: d.value * (data.margin_percent.current / 100) }))} color="#10b981" mainValue={data.profit.current} subtitle="На основе маржи" />
            ) : (
              <div className="rounded-xl border p-5 shadow-sm flex items-center justify-center text-sm"
                style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border)', color: 'var(--text-muted)' }}>Нет данных за период</div>
            )}
            <div className="rounded-xl border p-5 shadow-sm"
              style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border)' }}>
              <div className="flex items-center gap-2 mb-3">
                <span className="text-lg">🏆</span>
                <span className="text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--text-secondary)' }}>Топ-менеджер</span>
              </div>
              {data.top_manager?.name ? (
                <>
                  <div className="text-xl font-bold" style={{ color: 'var(--text-primary)' }}>{data.top_manager.name}</div>
                  <div className="text-2xl font-bold text-emerald-600 mt-1">{formatCurrency(data.top_manager.revenue)}</div>
                  <div className="text-xs mt-0.5" style={{ color: 'var(--text-muted)' }}>выручка за период</div>
                </>
              ) : (
                <div className="text-sm py-2" style={{ color: 'var(--text-muted)' }}>Нет данных</div>
              )}
            </div>
          </div>

          <div className="flex items-center gap-4 text-xs" style={{ color: 'var(--text-muted)' }}>
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

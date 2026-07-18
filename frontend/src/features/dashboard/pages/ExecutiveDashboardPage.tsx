import { useState, useEffect, useCallback } from 'react';
import { api } from '@/shared/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/Card';
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

function MetricCard({
  title,
  metric,
  format = 'currency',
  icon,
}: {
  title: string;
  metric: MetricData;
  format?: 'currency' | 'number' | 'percent';
  icon: string;
}) {
  const val = (n: number) => {
    if (format === 'currency') return formatCurrency(n);
    if (format === 'percent') return `${n.toFixed(1)}%`;
    return formatNumber(n);
  };

  const isGood = metric.trend_percent >= 0;
  const arrow = metric.trend_percent > 0 ? '▲' : metric.trend_percent < 0 ? '▼' : '―';

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm text-[#6b7280] uppercase tracking-wider flex items-center gap-2">
          <span>{icon}</span>
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold text-white">{val(metric.current)}</div>
        <div className="flex items-center gap-2 mt-1">
          <span className={`text-sm font-medium ${isGood ? 'text-success' : 'text-error'}`}>
            {arrow} {Math.abs(metric.trend_percent).toFixed(1)}%
          </span>
          <span className="text-xs text-[#6b7280]">vs {val(metric.previous)}</span>
        </div>
      </CardContent>
    </Card>
  );
}

function SparklineCard({
  title,
  data,
  color,
  mainValue,
  format = 'currency',
}: {
  title: string;
  data: { date: string; value: number }[];
  color: string;
  mainValue: number;
  format?: 'currency' | 'number';
}) {
  const val = (n: number) => (format === 'currency' ? formatCurrency(n) : formatNumber(n));
  const option: EChartsOption = {
    grid: { left: 0, right: 0, top: 4, bottom: 0 },
    xAxis: { type: 'category', show: false, data: data.map((d) => d.date) },
    yAxis: { type: 'value', show: false, min: 'dataMin' as any },
    series: [
      {
        type: 'line',
        data: data.map((d) => d.value),
        smooth: true,
        showSymbol: false,
        lineStyle: { width: 2, color },
        areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: `${color}44` }, { offset: 1, color: `${color}00` }] } },
      },
    ],
    tooltip: { show: false },
  };

  return (
    <Card className="col-span-1">
      <CardHeader>
        <CardTitle className="text-sm text-[#6b7280] uppercase tracking-wider">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="text-lg font-bold text-white">{val(mainValue)}</div>
        <div className="h-12 mt-1">
          <EChartsWrapper option={option} height={48} />
        </div>
      </CardContent>
    </Card>
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

  useEffect(() => {
    fetchKpi();
  }, [fetchKpi]);

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">📊 Панель руководителя</h1>
          <p className="text-sm text-[#6b7280] mt-1">
            {data?.period_label || 'Загрузка...'}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={period}
            onChange={(e) => setPeriod(e.target.value)}
            className="bg-[#0f1117] border border-[#2d3139] text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-brand-500"
          >
            {PERIODS.map((p) => (
              <option key={p.value} value={p.value}>
                {p.label}
              </option>
            ))}
          </select>
          <button
            onClick={fetchKpi}
            className="px-3 py-2 bg-[#1a1d23] border border-[#2d3139] text-white rounded-lg text-sm hover:bg-[#22262e] transition-colors"
          >
            🔄
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 mb-4 bg-error/10 border border-error/30 rounded-lg text-error text-sm">
          {error}
        </div>
      )}

      {loading && !data && (
        <div className="grid grid-cols-4 gap-4 mb-6">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-28 bg-[#1a1d23] border border-[#2d3139] rounded-lg animate-pulse" />
          ))}
        </div>
      )}

      {data && (
        <>
          <div className="grid grid-cols-4 gap-4 mb-6">
            <MetricCard title="Выручка" metric={data.revenue} icon="💰" />
            <MetricCard title="Валовая прибыль" metric={data.profit} icon="📈" />
            <MetricCard title="Заказы" metric={data.orders_count} format="number" icon="📦" />
            <MetricCard title="Маржа" metric={data.margin_percent} format="percent" icon="🎯" />
          </div>

          {data.sparklines?.revenue?.length > 0 && (
            <div className="grid grid-cols-3 gap-4 mb-6">
              <SparklineCard
                title="Выручка (по дням)"
                data={data.sparklines.revenue}
                color="#3b82f6"
                mainValue={data.revenue.current}
              />
              <SparklineCard
                title="Прибыль (по дням)"
                data={data.sparklines.revenue.map((d) => ({
                  date: d.date,
                  value: d.value * (data.margin_percent.current / 100),
                }))}
                color="#10b981"
                mainValue={data.profit.current}
              />
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm text-[#6b7280] uppercase tracking-wider">🏆 Топ-менеджер</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-lg font-bold text-white">{data.top_manager?.name || '—'}</div>
                  <div className="text-sm text-success mt-1">
                    {data.top_manager?.revenue ? formatCurrency(data.top_manager.revenue) : '—'}
                  </div>
                  <div className="text-xs text-[#6b7280] mt-0.5">выручка за период</div>
                </CardContent>
              </Card>
            </div>
          )}

          <div className="text-xs text-[#4b5563] flex items-center gap-2">
            <span>Cache: {data.cache_status === 'hit' ? '⚡ из кэша' : '📡 из 1С'}</span>
            {data.cache_status === 'hit' && (
              <span className="text-success">· быстрый ответ</span>
            )}
          </div>
        </>
      )}
    </div>
  );
}

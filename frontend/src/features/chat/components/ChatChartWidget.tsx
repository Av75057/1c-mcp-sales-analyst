import React, { useMemo, useRef } from 'react';
import * as echarts from 'echarts';
import { EChartsWrapper } from '@/shared/components/charts/EChartsWrapper';
import { api } from '@/shared/lib/api';
import { BarChart3, Download, Loader2, AlertCircle } from 'lucide-react';
import type { EChartsOption } from 'echarts';
import type { ChartBlock, Message } from '../stores/chatStore';

interface ChatChartWidgetProps {
  chart: ChartBlock;
  messageId: string;
  onSuggestionClick?: (s: string) => void;
}

export const ChatChartWidget: React.FC<ChatChartWidgetProps> = React.memo(({ chart, messageId, onSuggestionClick }) => {
  const chartRef = useRef<HTMLDivElement>(null);

  const saveToLibrary = async () => {
    try {
      await api.post('/api/v2/dashboards', {
        title: chart.config?.title || 'График из чата',
        description: 'Создан из AI-чата',
        tags: ['chat'],
        charts: [{
          id: `chat_${messageId}`,
          title: chart.config?.title || 'График',
          chart_config: {
            chart_type: chart.config?.chart_type || 'bar',
            title: chart.config?.title || 'График',
            x_axis: { field: 'label', label: '', type: 'category' },
            y_axis: { field: 'value', label: '', type: 'value' },
            series: [{ name: chart.config?.series_name || 'value', field: 'value', color: '#3b82f6' }],
          },
          data: chart.data.map(d => ({ label: d.label, value: d.value })),
          position: { x: 0, y: 0, w: 6, h: 4 },
          filter_bindings: [],
        }],
      });
    } catch {}
  };

  const exportPng = () => {
    if (!chartRef.current) return;
    const instance = echarts.getInstanceByDom(chartRef.current);
    if (!instance) return;
    const url = instance.getDataURL({ type: 'png', pixelRatio: 2, backgroundColor: '#fff' });
    const a = document.createElement('a');
    a.href = url;
    a.download = `${chart.config?.title || 'chart'}.png`;
    a.click();
  };

  if (chart.status === 'loading') {
    return (
      <div className="my-2 rounded-xl border p-6 animate-pulse" style={{ borderColor: 'var(--border)' }}>
        <div className="flex items-center gap-2 text-sm" style={{ color: 'var(--text-secondary)' }}>
          <Loader2 className="w-4 h-4 animate-spin" /> Строю график...
        </div>
      </div>
    );
  }

  if (chart.status === 'error') {
    return (
      <div className="my-2 p-3 rounded-xl" style={{ backgroundColor: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)' }}>
        <div className="flex items-start gap-2 text-sm">
          <AlertCircle className="w-4 h-4 text-red-500 mt-0.5 flex-shrink-0" />
          <div>
            <p className="font-medium text-sm text-red-700">Ошибка графика</p>
            <p className="text-xs mt-0.5" style={{ color: 'var(--text-secondary)' }}>{chart.error}</p>
          </div>
        </div>
      </div>
    );
  }

  const option: EChartsOption = useMemo(() => {
    if (!chart.data?.length) return {};
    const labels = chart.data.map(d => d.label);
    const values = chart.data.map(d => d.value);
    const rawType = chart.config?.chart_type || 'bar';
    const chartType = rawType === 'hbar' ? 'bar' : rawType;

    if (chartType === 'pie') {
      return {
        backgroundColor: 'transparent',
        title: { text: chart.config?.title || '', left: 'center', textStyle: { fontSize: 13 } },
        tooltip: { trigger: 'item' },
        series: [{ type: 'pie', radius: '55%', data: chart.data.map(d => ({ name: d.label, value: d.value })) }],
      };
    }

    return {
      backgroundColor: 'transparent',
      title: { text: chart.config?.title || '', left: 'center', textStyle: { fontSize: 13 } },
      tooltip: { trigger: 'axis' },
      grid: { left: 50, right: 16, top: 36, bottom: 28 },
      xAxis: { type: 'category', data: labels, axisLabel: { fontSize: 10, color: '#9ca3af', rotate: labels.length > 8 ? 30 : 0 } },
      yAxis: { type: 'value', axisLabel: { fontSize: 10, color: '#9ca3af' }, splitLine: { lineStyle: { color: '#f3f4f6' } } },
      series: [{ type: chartType as any, data: values, smooth: chartType === 'area', areaStyle: chartType === 'area' ? {} : undefined, itemStyle: { color: '#3b82f6' } }],
    };
  }, [chart]);

  if (!chart.data?.length) return null;

  return (
    <div className="my-2 rounded-xl border overflow-hidden" style={{ borderColor: 'var(--border)', backgroundColor: 'var(--bg-card)' }}>
      <div className="p-3" ref={chartRef}>
        <EChartsWrapper option={option} height={240} />
      </div>
      <div className="px-3 py-2 flex items-center justify-between border-t" style={{ borderColor: 'var(--border)' }}>
        <span className="text-xs" style={{ color: 'var(--text-muted)' }}>
          {chart.data.length} точек · {chart.config?.chart_type || 'chart'}
        </span>
        <div className="flex items-center gap-2">
          <button onClick={exportPng}
            className="text-xs transition-colors"
            style={{ color: 'var(--text-muted)' }}>
            <Download className="w-3 h-3 inline mr-1" /> PNG
          </button>
          <button onClick={saveToLibrary}
            className="text-xs transition-colors"
            style={{ color: 'var(--brand)' }}>
            <BarChart3 className="w-3 h-3 inline mr-1" /> Сохранить
          </button>
        </div>
      </div>
    </div>
  );
});

ChatChartWidget.displayName = 'ChatChartWidget';

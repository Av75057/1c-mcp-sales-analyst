import React, { useState, useMemo, useRef } from 'react';
import * as echarts from 'echarts';
import { EChartsWrapper } from '@/shared/components/charts/EChartsWrapper';
import { api } from '@/shared/lib/api';
import { BarChart3, Download, Loader2, AlertCircle, ChevronRight, X } from 'lucide-react';
import type { EChartsOption } from 'echarts';
import type { ChartBlock } from '../stores/chatStore';

interface DrillDownLevel {
  id: string;
  label: string;
  has_children: boolean;
}

interface Breadcrumb {
  level: string;
  label: string;
}

interface ChatChartWidgetProps {
  chart: ChartBlock;
  messageId: string;
  onSuggestionClick?: (s: string) => void;
}

export const ChatChartWidget: React.FC<ChatChartWidgetProps> = React.memo(({ chart, messageId, onSuggestionClick: _onSuggestionClick }) => {
  const chartRef = useRef<HTMLDivElement>(null);
  const [drillState, setDrillState] = useState<{
    loading: boolean;
    error?: string;
    breadcrumbs: Breadcrumb[];
    currentData: { label: string; value: number }[];
    currentTitle: string;
    currentLevel: string;
    domain: string;
    levels: DrillDownLevel[];
    chartType: string;
    date_from?: string;
    date_to?: string;
  } | null>(null);

  const drilldown = (chart as any).drilldown;
  const drillLevels = drilldown?.levels as { id: string; label: string; has_children: boolean }[] | undefined;
  const isDrillEnabled = drilldown?.enabled && drillLevels && drillLevels.length > 0;

  const handleChartClick = async (name: string) => {
    if (!isDrillEnabled) return;
    const dd = drilldown as any;
    const currentLevelId = drillState?.currentLevel || dd.current_level;
    const levels: DrillDownLevel[] = drillState?.levels || dd.levels;
    const currentIdx = levels.findIndex((l: DrillDownLevel) => l.id === currentLevelId);
    if (currentIdx === -1 || currentIdx >= levels.length - 1) return;
    const nextLevel = levels[currentIdx + 1];
    if (!nextLevel) return;

    setDrillState(prev => prev ? { ...prev, loading: true } : {
      loading: true,
      breadcrumbs: [],
      currentData: chart.data,
      currentTitle: chart.config?.title || '',
      currentLevel: currentLevelId,
      domain: dd.domain,
      levels,
      chartType: chart.config?.chart_type || 'bar',
    });

    try {
      const body: any = {
        domain: drillState?.domain || dd.domain,
        parent_level: currentLevelId,
        parent_value: name,
        child_level: nextLevel.id,
      };
      if (drillState?.date_from) body.date_from = drillState.date_from;
      if (drillState?.date_to) body.date_to = drillState.date_to;

      const res = await api.post('/api/charts/drill-down', body);
      const data = res.data;

      if (data.error) {
        setDrillState(prev => prev ? { ...prev, loading: false, error: data.error } : null);
        return;
      }

      const newBreadcrumbs = [
        ...(drillState?.breadcrumbs || []),
        { level: currentLevelId, label: name },
      ];

      setDrillState({
        loading: false,
        breadcrumbs: newBreadcrumbs,
        currentData: data.table_data || [],
        currentTitle: data.title || name,
        currentLevel: nextLevel.id,
        domain: drillState?.domain || dd.domain,
        levels: data.drilldown?.levels || levels,
        chartType: data.chart_type || 'bar',
        date_from: drillState?.date_from,
        date_to: drillState?.date_to,
      });
    } catch (err: any) {
      setDrillState(prev => prev ? { ...prev, loading: false, error: err?.message || 'Ошибка запроса детализации' } : null);
    }
  };

  const goToBreadcrumb = (idx: number) => {
    if (!drillState) return;
    setDrillState({
      ...drillState,
      breadcrumbs: drillState.breadcrumbs.slice(0, idx),
      loading: false,
    });
  };

  const resetDrill = () => {
    setDrillState(null);
  };

  const displayData = drillState?.currentData || chart.data;
  const displayTitle = drillState?.currentTitle || chart.config?.title || '';
  const displayChartType = drillState?.chartType || chart.config?.chart_type || 'bar';
  const showAsTable = drillState?.levels?.find(l => l.id === drillState?.currentLevel)?.has_children === false;

  const option: EChartsOption = useMemo(() => {
    if (!displayData?.length) return {};
    const labels = displayData.map(d => d.label);
    const values = displayData.map(d => d.value);
    const rawType = displayChartType === 'hbar' ? 'bar' : displayChartType;
    const baseOption: EChartsOption = {
      backgroundColor: 'transparent',
      title: { text: displayTitle, left: 'center', textStyle: { fontSize: 13 } },
      tooltip: { trigger: rawType === 'pie' ? 'item' : 'axis' },
      grid: { left: 50, right: 16, top: 36, bottom: 28 },
    };
    if (rawType === 'pie') {
      return { ...baseOption, series: [{ type: 'pie', radius: '55%', data: displayData.map(d => ({ name: d.label, value: d.value })) }] };
    }
    return {
      ...baseOption,
      xAxis: { type: 'category', data: labels, axisLabel: { fontSize: 10, color: '#9ca3af', rotate: labels.length > 8 ? 30 : 0 } },
      yAxis: { type: 'value', axisLabel: { fontSize: 10, color: '#9ca3af' }, splitLine: { lineStyle: { color: '#f3f4f6' } } },
      series: [{ type: rawType as any, data: values, smooth: rawType === 'area', areaStyle: rawType === 'area' ? {} : undefined, itemStyle: { color: '#3b82f6' } }],
    };
  }, [displayData, displayTitle, displayChartType]);

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

  if (!chart.data?.length && !drillState?.currentData?.length) return null;

  const saveToLibrary = async () => {
    try {
      await api.post('/api/v2/dashboards', {
        title: displayTitle || 'График из чата',
        description: 'Создан из AI-чата',
        tags: ['chat'],
        is_public: false,
        charts: [{
          id: `chat_${messageId}_${Date.now()}`,
          title: displayTitle || 'График',
          chart_config: { chart_type: displayChartType, title: displayTitle, x_axis: { field: 'label', label: '', type: 'category' }, y_axis: { field: 'value', label: '', type: 'value' }, series: [{ name: 'value', field: 'value', color: '#3b82f6' }] },
          data: displayData.map(d => ({ label: d.label, value: d.value })),
          position: { x: 0, y: 0, w: 6, h: 4 },
          filter_bindings: [],
        }],
      });
      alert('✅ График сохранён в библиотеку');
    } catch (e: any) {
      alert('❌ Ошибка сохранения: ' + (e?.response?.data?.detail || e?.message || 'неизвестная ошибка'));
    }
  };

  const exportPng = () => {
    if (!chartRef.current) return;
    const instance = echarts.getInstanceByDom(chartRef.current);
    if (!instance) return;
    const url = instance.getDataURL({ type: 'png', pixelRatio: 2, backgroundColor: '#fff' });
    const a = document.createElement('a');
    a.href = url;
    a.download = `${displayTitle || 'chart'}.png`;
    a.click();
  };

  return (
    <div className="my-2 rounded-xl border overflow-hidden" style={{ borderColor: 'var(--border)', backgroundColor: 'var(--bg-card)' }}>
      {/* Error message */}
      {drillState?.error && (
        <div className="px-3 pt-2 pb-1 text-xs" style={{ color: 'var(--error)' }}>
          ❌ {drillState.error}
        </div>
      )}

      {/* Breadcrumbs */}
      {drillState?.breadcrumbs && drillState.breadcrumbs.length > 0 && (
        <div className="flex items-center gap-1 px-3 pt-2 pb-1 flex-wrap text-xs" style={{ color: 'var(--text-secondary)' }}>
          <button onClick={resetDrill} className="hover:underline" style={{ color: 'var(--brand)' }}>📊 {drilldown?.domain_label || 'График'}</button>
          {drillState.breadcrumbs.map((b, i) => (
            <React.Fragment key={i}>
              <ChevronRight className="w-3 h-3 inline opacity-50" />
              <button onClick={() => goToBreadcrumb(i)} className="hover:underline">{b.label}</button>
            </React.Fragment>
          ))}
          <button onClick={resetDrill} className="ml-auto opacity-50 hover:opacity-100" title="Сбросить"><X className="w-3 h-3" /></button>
        </div>
      )}

      {/* Loading overlay */}
      <div className="relative">
        {drillState?.loading && (
          <div className="absolute inset-0 z-10 flex items-center justify-center" style={{ backgroundColor: 'rgba(255,255,255,0.6)' }}>
            <div className="flex items-center gap-2 text-sm" style={{ color: 'var(--text-secondary)' }}>
              <Loader2 className="w-4 h-4 animate-spin" /> Загружаю детализацию...
            </div>
          </div>
        )}

        {/* Table (last level) */}
        {showAsTable ? (
          <div className="p-3 max-h-64 overflow-y-auto">
            <table className="w-full text-xs">
              <thead>
                <tr style={{ color: 'var(--text-muted)', borderBottom: '1px solid var(--border)' }}>
                  <th className="text-left py-1 pr-2">Название</th>
                  <th className="text-right py-1 pl-2">Значение</th>
                </tr>
              </thead>
              <tbody>
                {displayData.map((d: any, i) => (
                  <tr key={i} style={{ borderBottom: '1px solid var(--border)' }}>
                    <td className="py-1 pr-2 truncate max-w-40" style={{ color: 'var(--text-primary)' }}>
                      {d.date && <span className="text-xs opacity-60 mr-1">{d.date}</span>}
                      {d.label}
                    </td>
                    <td className="text-right py-1 pl-2 font-medium whitespace-nowrap" style={{ color: 'var(--text-primary)' }}>
                      {d.deep_link ? (
                        <a href={d.deep_link} target="_blank" rel="noopener noreferrer"
                          className="hover:underline" style={{ color: 'var(--brand)' }}>
                          {(d.value).toLocaleString()} ₽ ↗
                        </a>
                      ) : (
                        <>{(d.value).toLocaleString()} ₽</>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="p-3" ref={chartRef}>
            <EChartsWrapper option={option} height={240} onChartClick={isDrillEnabled ? handleChartClick : undefined} />
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="px-3 py-2 flex items-center justify-between border-t" style={{ borderColor: 'var(--border)' }}>
        <span className="text-xs" style={{ color: 'var(--text-muted)' }}>
          {displayData.length} точек · {displayChartType}
          {drillState?.currentLevel && ` · ${drillState.currentLevel}`}
        </span>
        <div className="flex items-center gap-2">
          {!showAsTable && (
            <button onClick={exportPng} className="text-xs transition-colors" style={{ color: 'var(--text-muted)' }}>
              <Download className="w-3 h-3 inline mr-1" /> PNG
            </button>
          )}
          <button onClick={saveToLibrary} className="text-xs transition-colors" style={{ color: 'var(--brand)' }}>
            <BarChart3 className="w-3 h-3 inline mr-1" /> Сохранить
          </button>
        </div>
      </div>
    </div>
  );
});

ChatChartWidget.displayName = 'ChatChartWidget';

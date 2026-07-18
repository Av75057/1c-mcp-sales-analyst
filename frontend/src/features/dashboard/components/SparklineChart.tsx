import React, { useMemo } from 'react';
import { EChartsWrapper } from '@/shared/components/charts/EChartsWrapper';
import type { EChartsOption } from 'echarts';
import type { SparklinePoint } from '../types/kpi';

interface SparklineChartProps {
  data: SparklinePoint[];
  trendPercent: number;
  isInverseTrend?: boolean;
  height?: number;
  showAxes?: boolean;
}

export const SparklineChart: React.FC<SparklineChartProps> = React.memo(({
  data,
  trendPercent,
  isInverseTrend = false,
  height = 120,
  showAxes = false,
}) => {
  const isPositive = isInverseTrend ? trendPercent < 0 : trendPercent >= 0;
  const color = isPositive ? '#10b981' : '#ef4444';

  const option: EChartsOption = useMemo(() => {
    if (showAxes) {
      return {
        backgroundColor: 'transparent',
        grid: { left: 48, right: 8, top: 8, bottom: 20 },
        xAxis: {
          type: 'category', show: true, data: data.map(d => d.date),
          axisLine: { lineStyle: { color: '#e5e7eb' } },
          axisTick: { lineStyle: { color: '#e5e7eb' } },
          axisLabel: { fontSize: 10, color: '#9ca3af', rotate: 0 },
          splitLine: { show: false },
        },
        yAxis: {
          type: 'value', show: true, min: 'dataMin' as any,
          axisLine: { show: false }, axisTick: { show: false },
          axisLabel: { fontSize: 10, color: '#9ca3af' },
          splitLine: { lineStyle: { color: '#f3f4f6', type: 'dashed' as const } },
        },
        series: [{
          type: 'line', data: data.map(d => d.value), smooth: true, showSymbol: false,
          lineStyle: { width: 2.5, color }, itemStyle: { color },
          areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: `${color}1A` }, { offset: 1, color: `${color}00` }] } },
        }],
        tooltip: { show: false },
      };
    }
    return {
      backgroundColor: 'transparent',
      grid: { top: 2, bottom: 2, left: 2, right: 2 },
      xAxis: { type: 'category', show: false, data: data.map(d => d.date) },
      yAxis: { type: 'value', show: false, min: 'dataMin' as any },
      series: [{
        type: 'line', data: data.map(d => d.value), smooth: true, showSymbol: false,
        lineStyle: { color, width: 2 },
        areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: `${color}40` }, { offset: 1, color: `${color}00` }] } },
      }],
      tooltip: { show: false },
    };
  }, [data, color, showAxes]);

  return <EChartsWrapper option={option} height={height} />;
});

SparklineChart.displayName = 'SparklineChart';

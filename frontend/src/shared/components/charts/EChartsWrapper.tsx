import { useEffect, useRef, useCallback } from 'react';
import * as echarts from 'echarts';
import type { EChartsOption } from 'echarts';

interface EChartsWrapperProps {
  option: EChartsOption;
  height?: number | string;
  loading?: boolean;
  onEvents?: Record<string, (params: any) => void>;
  onChartClick?: (name: string) => void;
}

export function EChartsWrapper({ option, height = 400, loading = false, onEvents, onChartClick }: EChartsWrapperProps) {
  const chartRef = useRef<HTMLDivElement>(null);
  const instanceRef = useRef<echarts.ECharts>();

  useEffect(() => {
    if (!chartRef.current) return;

    instanceRef.current?.dispose();
    instanceRef.current = echarts.init(chartRef.current);

    const resizeObserver = new ResizeObserver(() => {
      instanceRef.current?.resize();
    });
    resizeObserver.observe(chartRef.current);

    if (onEvents) {
      Object.entries(onEvents).forEach(([eventName, handler]) => {
        instanceRef.current?.on(eventName, handler);
      });
    }

    return () => {
      resizeObserver.disconnect();
      instanceRef.current?.dispose();
    };
  }, []);

  useEffect(() => {
    if (!instanceRef.current) return;
    if (loading) {
      instanceRef.current.showLoading();
    } else {
      instanceRef.current.hideLoading();
      instanceRef.current.setOption(option, { notMerge: true });
    }
  }, [option, loading]);

  const handleClick = useCallback((e: React.MouseEvent) => {
    if (!chartRef.current || !onChartClick) return;
    const instance = echarts.getInstanceByDom(chartRef.current);
    if (!instance) return;
    const rect = chartRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const pixel = instance.convertFromPixel({ seriesIndex: 0 }, [x, y]);
    if (pixel && Array.isArray(pixel) && pixel[0] !== undefined && pixel[0] >= 0) {
      const dataIndex = Math.round(pixel[0]);
      const opt = instance.getOption();
      const categories = (opt.xAxis as any[])?.[0]?.data as string[];
      if (categories && categories[dataIndex]) {
        onChartClick(categories[dataIndex]);
      }
    }
  }, [onChartClick]);

  return <div ref={chartRef} onClick={handleClick} style={{ width: '100%', height, cursor: onChartClick ? 'pointer' : undefined }} />;
}

import { useEffect, useRef, useState } from 'react';
import * as echarts from 'echarts';
import type { EChartsOption } from 'echarts';

interface EChartsWrapperProps {
  option: EChartsOption;
  height?: number | string;
  loading?: boolean;
  onEvents?: Record<string, (params: any) => void>;
}

function getTheme() {
  return document.documentElement.getAttribute('data-theme') === 'light' ? 'light' : 'dark';
}

export function EChartsWrapper({ option, height = 400, loading = false, onEvents }: EChartsWrapperProps) {
  const chartRef = useRef<HTMLDivElement>(null);
  const instanceRef = useRef<echarts.ECharts>();
  const [theme, setTheme] = useState(getTheme);

  useEffect(() => {
    const observer = new MutationObserver(() => {
      const t = getTheme();
      if (t !== theme) {
        setTheme(t);
      }
    });
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
    return () => observer.disconnect();
  }, [theme]);

  useEffect(() => {
    if (!chartRef.current) return;
    instanceRef.current?.dispose();
    instanceRef.current = echarts.init(chartRef.current, theme);

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
  }, [theme]);

  useEffect(() => {
    if (!instanceRef.current) return;
    if (loading) {
      instanceRef.current.showLoading();
    } else {
      instanceRef.current.hideLoading();
      instanceRef.current.setOption(option, { notMerge: true });
    }
  }, [option, loading]);

  return <div ref={chartRef} style={{ width: '100%', height }} />;
}
